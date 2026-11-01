"""Two-mode MPC: commit (model-optimal push) or creep (lowest useful force), with
abort-on-wobble inside every push."""
import numpy as np
from common import CANDIDATES, ABORT_DEG, GOAL, TOL
import updater_bayes as ub

EPS_TIP = 0.03

def score_candidates(post, name, remaining, seed=0, n=300):
    s = ub.sample(post, name, n, seed); spec = post["spec"][name]
    rows = []
    for (F, hp) in CANDIDATES:
        d, w = ub.predict(s, spec, (F, hp, ABORT_DEG))
        rows.append(dict(push=(F, hp, ABORT_DEG), mean=float(d.mean()), std=float(d.std()),
                         p_risk=float((w > 20).mean()),
                         rmse=float(np.sqrt(np.mean((remaining - d) ** 2))),
                         q90=float(np.quantile(d, 0.9))))
    return rows

def choose(post, name, remaining, seed=0):
    rows = score_candidates(post, name, remaining, seed)
    safe = [r for r in rows if r["p_risk"] <= EPS_TIP and r["mean"] > 0.004
            and r["q90"] <= remaining]
    if safe:
        best = max(safe, key=lambda r: r["mean"]); mode = "commit"
    else:
        cands = [r for r in rows if r["p_risk"] <= EPS_TIP] or rows
        best = min(cands, key=lambda r: (r["q90"], r["push"][0])); mode = "creep"
    return best["push"], mode, rows
