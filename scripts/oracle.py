"""Feasibility ceiling (evaluator side, uses hidden truth). An ORACLE probe policy that knows the
anomaly: each step it picks the safe push (by the TRUE model) whose noise-free outcome the current
best fixed-class (base) fit explains worst. Detection = menu-BIC picks the true family.
If this cannot reach >=70% detection with 0 tips, the anomalies are not identifiable by safe probes."""
import os, sys
import numpy as np
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ROOT)
import evaluator, model, updater_bayes as ub
from tracker_sam import Tracker
from common import CANDIDATES, ABORT_DEG

SAFE_W = ABORT_DEG - 0.5   # oracle only uses pushes the abort never has to catch

def oracle_run(seed, n_probes=5, group="surprise", n=6000, top=1500):
    env, an, fam = evaluator.new_env(seed, group)
    t = env.truth
    key = evaluator.FAMILY_MAP[an]; spec = ub.MENU[key]; c1 = np.array([t.strength])
    truth_obs = {}
    for (F, hp) in CANDIDATES:
        d1, w1 = model.simulate(np.array([t.mass]), t.friction, t.com_x, F, hp, ABORT_DEG, spec, c1, None, K=60)
        if w1[0] <= SAFE_W: truth_obs[(F, hp)] = (d1[0], w1[0])
    tr = Tracker(seed); post = ub.prior(seed, menu=True, n=n); tipped = False; picks = []
    for _ in range(n_probes):
        p = post["m"]["base"]; idx = np.argsort(p["ll"])[-top:]
        sub = {k: v[idx] for k, v in p.items()}
        best, bs = None, -1e9
        for (F, hp), (d1, w1) in truth_obs.items():
            if (F, hp) in picks: continue
            d, w = ub.predict(sub, post["spec"]["base"], (F, hp, ABORT_DEG))
            chi = ((d1 - d) / ub.sigma_d(d)) ** 2 + ((w1 - w) / ub.SIG_W) ** 2
            j = (-sub["ll"] + 0.5 * chi).min() - (-sub["ll"]).min()
            if j > bs: bs, best = j, (F, hp)
        picks.append(best)
        o = tr.track(env.push(best[0], best[1], ABORT_DEG)); tipped |= o["tipped"]
        post = ub.update(post, (best[0], best[1], ABORT_DEG), o)
        if tipped: break
    nm = ub.best_model(post)[0]
    return dict(seed=seed, an=an, tipped=tipped, detected=(nm == key), picks=picks, best=nm)

if __name__ == "__main__":
    seeds = [int(a) for a in sys.argv[1:]] or list(range(1000, 1020))
    rs = [oracle_run(s) for s in seeds]
    for r in rs: print(r["seed"], r["an"], r["tipped"], r["detected"], r["best"], r["picks"])
    for a in ("sliding_weight", "stick_slip"):
        q = [r for r in rs if r["an"] == a]
        print(a, "detect %d/%d tips %d" % (sum(r["detected"] for r in q), len(q), sum(r["tipped"] for r in q)))
