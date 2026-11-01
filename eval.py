"""Evaluation harness (evaluator side). All results SIMULATED.
usage: python eval.py [--n-closed 20] [--n-surprise 10] [--agents spark,mi_bic,creep,random] [--out out/eval.csv]"""
import argparse, csv, math, time
import numpy as np
import evaluator
from tracker_sam import Tracker
import agent

AGENTS = ["spark", "mi_bic", "creep", "random"]


def wilson(k, n, z=1.96):
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return ((c - h) / d, (c + h) / d)


def run_all(n_closed, n_surprise, agents, out, live=False):
    rows = []
    jobs = [("closed", s) for s in range(n_closed)] + [("surprise", 1000 + s) for s in range(n_surprise)]
    for group, seed in jobs:
        for kind in agents:
            env, an, fam = evaluator.new_env(seed, group)
            amb_true = evaluator.truly_ambiguous(env.truth)
            r = agent.run(kind, env, Tracker(seed), seed, live)
            fam_det = r["detected"]
            rows.append(dict(
                sim_measured="SIMULATED", group=group, seed=seed, agent=kind, planner_mode=r["planner_mode"],
                true_family=fam, anomaly=an or "", tipped=int(r["tipped"]), delivered=int(r["delivered"]),
                steps=r["steps"], probes=r["probes"], err=r["err"], ambiguity_p1=r["ambiguity_p1"],
                truly_ambiguous=int(amb_true), detected=fam_det or "",
                det_correct=int(fam_det == evaluator.FAMILY_MAP[an]) if an else int(fam_det is None),
                det_probes=r["det_probes"], invalid=r["invalid"], modes=r["modes"]))
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    return rows


def summarize(rows):
    out = []
    for group in ("closed", "surprise"):
        for kind in AGENTS:
            rs = [r for r in rows if r["group"] == group and r["agent"] == kind]
            if not rs:
                continue
            n = len(rs)
            tip = sum(r["tipped"] for r in rs)
            ok = [r for r in rs if not r["tipped"] and r["delivered"]]
            lo, hi = wilson(tip, n)
            line = dict(group=group, agent=kind, n=n, tip=tip, tip_rate=tip / n, tip_ci=(round(lo, 3), round(hi, 3)),
                        delivered=sum(r["delivered"] for r in rs),
                        steps_notip=float(np.mean([r["steps"] for r in ok])) if ok else float("nan"))
            if group == "surprise":
                det = sum(1 for r in rs if r["detected"] and r["det_correct"])
                dp = [r["det_probes"] for r in rs if r["det_probes"] and r["det_correct"]]
                line.update(recall=det / n, recall_ci=tuple(round(x, 3) for x in wilson(det, n)),
                            probes_to_det=float(np.mean(dp)) if dp else float("nan"))
            else:
                fp = sum(1 for r in rs if r["detected"])
                line.update(false_pos=fp)
            out.append(line)
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-closed", type=int, default=20)
    ap.add_argument("--n-surprise", type=int, default=10)
    ap.add_argument("--agents", default=",".join(AGENTS))
    ap.add_argument("--out", default="out/eval.csv")
    a = ap.parse_args()
    t = time.time()
    rows = run_all(a.n_closed, a.n_surprise, a.agents.split(","), a.out)
    for l in summarize(rows):
        print(l)
    print("elapsed %.0fs" % (time.time() - t))
