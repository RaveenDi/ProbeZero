"""Agents. All model-based agents share ONE safe-probing protocol (force ladder + abort-on-wobble
+ same force cap) and the same updater / MPC; they differ only in what happens when the
fixed-class model stops fitting:
  fixed : Bayes over (load, grip, lean) + generic residual-misfit alarm; cannot propose mechanisms,
          falls back to creep when the alarm fires.
  menu  : privileged upper bound: MI+BIC over base + the two known anomaly families.
  spark : fixed-class + planner proposes an EXECUTABLE DSL model patch from residual summaries
          (no family menu). MOCK = scripted rule-based stub; LIVE = muse-spark-1.3.
  random: random safe probes, fixed-class + alarm.   creep: cage-creep baseline (no model).
Only sees env.look()/env.push() clips through the tracker. Never imports sim/evaluator."""
import numpy as np
from common import *
import updater_bayes as ub
import mpc
import dsl
import planner_client

MAX_PROBES = 5
MIN_PROBES = 3
PROBE_RISK = 0.10      # P(push reaches the abort level) allowed for probes
ALARM_THR = 1.6        # generic misfit alarm: chi2 per datum of the best base particle
MAX_CALLS = 4          # planner calls per run
LADDER_START = 3.0


def _sample_rows(post, name, seed, n=150):
    s = ub.sample(post, name, n, seed); spec = post["spec"][name]
    rows = []
    for (F, hp) in CANDIDATES:
        d, w = ub.predict(s, spec, (F, hp, ABORT_DEG))
        info = 0.5 * np.log(1 + d.var() / ub.sigma_d(d.mean()) ** 2) + 0.5 * np.log(1 + w.var() / ub.SIG_W ** 2)
        rows.append(dict(push=(F, hp, ABORT_DEG), p_risk=float((w > ABORT_DEG - 1.5).mean()), info=float(info), d=d))
    return s, rows


def _creep(res, env, tracker, goal_x, cx, hp=0.30, steps=40):
    """Cage-creep: lowest-reach pusher, force ladder up one rung whenever nothing moved."""
    fi, last = 0, 0.0
    for _ in range(steps):
        rem = goal_x - cx
        if abs(rem) <= TOL or rem < -TOL:
            break
        if last > 0 and rem < 1.2 * last and fi > 0:
            fi -= 1
        o = tracker.track(env.push(FORCES[fi], hp, ABORT_DEG))
        res["steps"] += 1
        cx = o["cx"]
        if o["tipped"]:
            res["tipped"] = True
            return cx
        if o["disp"] < 0.004:
            fi = min(fi + 1, len(FORCES) - 1)
        else:
            last = o["disp"]
    res["delivered"] = abs(goal_x - cx) <= TOL
    res["err"] = float(goal_x - cx)
    return cx


def run(kind, env, tracker, seed, live=False):
    rng = np.random.default_rng(seed + 31)
    t0 = tracker.track(env.look())["cx"]
    goal_x = t0 + GOAL
    res = dict(steps=0, probes=0, tipped=False, delivered=False, planner_mode=("MOCK" if kind == "spark" else "-"),
               invalid=0, err=None, modes="", alarm=False, alarm_probe=None, patch_spec=None, calls=0, det_probes=None,
               fell_back=False)
    if kind == "creep":
        _creep(res, env, tracker, goal_x, t0)
        return res
    st = dict(post=ub.prior(seed, menu=(kind == "menu")), cx=t0)

    def do(F, hp, ab):
        o = tracker.track(env.push(F, hp, ab))
        res["steps"] += 1
        st["post"] = ub.update(st["post"], (F, hp, ab), o)
        st["cx"] = o["cx"]
        if o["tipped"]:
            res["tipped"] = True
        return o

    def current():
        if kind in ("menu", "spark"):
            return ub.best_model(st["post"])[0]
        return "base"

    def check_alarm():
        post = st["post"]
        if post["n_obs"] < 2:
            return
        if ub.misfit_chi2(post, "base") > ALARM_THR or current() != "base":
            if not res["alarm"]:
                res["alarm"], res["alarm_probe"] = True, res["probes"]
        if kind == "spark" and res["alarm"] and current() == "base" and res["calls"] < MAX_CALLS:
            res["calls"] += 1
            out = planner_client.call(dict(residuals=ub.residuals(post, "base"), n_obs=post["n_obs"]), live)
            spec = dsl.validate(out.get("model_patch")) if out else None
            if out:
                res["planner_mode"] = out.get("mode", res["planner_mode"])
            if spec is None:
                res["invalid"] += 1
            else:
                ub.add_model(post, "patch%d" % res["calls"], spec)

    cap = LADDER_START
    for i in range(MAX_PROBES):
        nm = current()
        s, rows = _sample_rows(st["post"], nm, seed + i)
        ok = [r for r in rows if r["push"][0] <= cap and r["p_risk"] <= PROBE_RISK] or \
             [min(rows, key=lambda r: (r["p_risk"], r["push"][0]))]
        push = ok[rng.integers(len(ok))]["push"] if kind == "random" else max(ok, key=lambda r: r["info"])["push"]
        o = do(*push)
        res["probes"] += 1
        if res["tipped"]:
            return res
        # abort-on-wobble ladder: escalate force only while the box stays calm
        cap = cap if o["wobble"] > 0.7 * ABORT_DEG else max(cap, push[0]) * 2.0
        check_alarm()
        if res["alarm"] and res["det_probes"] is None and current() != "base":
            res["det_probes"] = res["probes"]
        nm = current()
        _, sd, _ = ub.summary(st["post"], nm)
        resolved = (not res["alarm"]) or nm != "base"
        if res["probes"] >= MIN_PROBES and sd < 0.03 and resolved:
            break
    nm = current()
    if nm != "base":
        res["patch_spec"] = st["post"]["spec"][nm]
    # commit phase
    modes = []
    for j in range(14):
        rem = goal_x - st["cx"]
        if abs(rem) <= TOL or rem < -TOL:
            break
        nm = current()
        if nm == "base" and kind != "creep" and (res["alarm"] or ub.misfit_chi2(st["post"]) > ALARM_THR):
            res["alarm"] = True
            res["fell_back"] = True            # model not trusted: conservative creep
            res["modes"] = "".join(modes) + "|creep"
            _creep(res, env, tracker, goal_x, st["cx"])
            return res
        push, mode, _ = mpc.choose(st["post"], nm, rem, seed + 100 + j)
        modes.append(mode[0])
        do(*push)
        if res["tipped"]:
            return res
    rem = goal_x - st["cx"]
    res["modes"] = "".join(modes)
    res["delivered"] = abs(rem) <= TOL and not res["tipped"]
    res["err"] = float(rem)
    return res
