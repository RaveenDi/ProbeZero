"""Matplotlib replay of a logged run: side view, tilt gauge, step captions.
Reads the evaluator log only (no live calls). Every frame is watermarked SIMULATED ONLY.
usage: python ui/replay.py [--seed 3] [--group closed] [--agent mi_bic] [--seconds 60] [--out out/replay.gif]"""
import argparse, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, PillowWriter
from matplotlib.patches import Polygon, Rectangle
import evaluator, agent
from tracker_sam import Tracker
from common import W, H, GOAL, TOL, TIP_DEG

def frames_from_log(env):
    out = []
    for i, L in enumerate(env.log):
        n = len(L["x"])
        for k in range(0, n, 3):
            out.append((i, L["x"][k], L["th"][k], L))
        out += [(i, L["x"][-1], L["th"][-1], L)] * 4
    return out

def render(seed=3, group="closed", kind="mi_bic", seconds=60, out="out/replay.gif", fps=8):
    env, an, fam = evaluator.new_env(seed, group)
    res = agent.run(kind, env, Tracker(seed), seed)
    base = frames_from_log(env)
    total = max(len(base), int(seconds * fps))
    rep = max(1, total // len(base))
    frames = [f for f in base for _ in range(rep)]
    fig, (ax, g) = plt.subplots(1, 2, figsize=(8, 3.2), gridspec_kw=dict(width_ratios=[4, 1]))
    nprobe = res["probes"]
    def draw(j):
        i, x, th, L = frames[j]
        ax.clear(); g.clear()
        ax.set_xlim(-0.1, GOAL + 0.3); ax.set_ylim(-0.05, 0.4); ax.set_aspect("equal"); ax.axis("off")
        ax.add_patch(Rectangle((GOAL - TOL, -0.02), 2 * TOL, 0.02, color="tab:green"))
        ax.plot([-0.1, GOAL + 0.3], [0, 0], "k")
        t = np.deg2rad(min(th, 90)); px = x + W  # pivot at front-bottom corner
        c, s = np.cos(-t), np.sin(-t)
        pts = np.array([[0, 0], [W, 0], [W, H], [0, H]]) - [W, 0]
        R = np.array([[c, -s], [s, c]]); pts = pts @ R.T + [x + W, 0]
        ax.add_patch(Polygon(pts, color="tab:red" if th > 12 else "tab:blue", alpha=.8))
        ax.plot([x - 0.06, x], [L["hp"] * H] * 2, "k", lw=4)
        phase = "PLAN/ACT (probe)" if i < nprobe else "ACT/VERIFY (commit)"
        if th > 12: phase = "RECOVER: abort + re-aim"
        ax.set_title(f"push {i + 1}: F={L['F']:.1f}N h={L['hp']:.2f}  {phase}", fontsize=9)
        ax.text(0.5, 0.02, f"SIMULATED ONLY  seed {seed}  agent {kind}  planner stub: {res['planner_mode']}",
                transform=ax.transAxes, ha="center", fontsize=8, color="gray")
        g.bar([0], [min(th, 40)], color="tab:red" if th > 12 else "tab:blue")
        g.axhline(TIP_DEG, color="k", ls="--"); g.set_ylim(0, 40); g.set_title("tilt deg", fontsize=8)
        g.set_xticks([])
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    FuncAnimation(fig, draw, frames=len(frames), interval=1000 / fps).save(out, writer=PillowWriter(fps=fps))
    plt.close(fig)
    return out, len(frames), res

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=3); ap.add_argument("--group", default="closed")
    ap.add_argument("--agent", default="mi_bic"); ap.add_argument("--seconds", type=float, default=60)
    ap.add_argument("--out", default="out/replay.gif")
    a = ap.parse_args()
    print(render(a.seed, a.group, a.agent, a.seconds, a.out))
