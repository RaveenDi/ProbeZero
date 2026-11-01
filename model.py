"""Agent-side forward model (vectorised). Parameters are neutral: load, grip, lean.
A model patch (validated DSL spec, see dsl.py) may override two hooks:
  brk  : threshold force at which motion starts (default grip*load*g)
  lean : effective lean while pushing (default lean)
"""
import numpy as np
from common import W, H, G, T, tilt
import dsl


def simulate(load, grip, lean, F, hp, abort_deg, spec=None, c1=None, c2=None, K=24):
    load = np.asarray(load, float); n = load.shape[0]
    grip = np.broadcast_to(grip, (n,)); lean = np.broadcast_to(lean, (n,))
    env = dict(load=load, grip=grip, lean=lean, g=G,
               c1=np.broadcast_to(1.0 if c1 is None else c1, (n,)), c2=np.broadcast_to(1.0 if c2 is None else c2, (n,)))
    wt = load * G
    thr = grip * wt
    lean_fn = None
    if spec is not None:
        if spec.get("brk"): thr = np.maximum(np.asarray(dsl.compile_expr(spec["brk"], dsl.STATIC)(env), float), 0.1) * np.ones(n)
        if spec.get("lean"): lean_fn = dsl.compile_expr(spec["lean"], dsl.DYNAMIC)
    x = np.zeros(n); v = np.zeros(n); moving = np.zeros(n, bool)
    released = np.zeros(n, bool); peak = np.zeros(n); dt = T / K
    for k in range(K):
        t = (k + 0.5) * dt
        Fa = np.where(released, 0.0, F * min(1.0, t / (0.4 * T)))
        moving = moving | (Fa > thr)
        a = np.where(moving, (Fa - grip * wt) / load, 0.0)
        vn = np.maximum(v + a * dt, 0.0)
        stopped = moving & (vn <= 0) & (a <= 0)
        x = x + 0.5 * (v + vn) * dt * moving
        v = np.where(moving, vn, 0.0)
        moving = moving & ~stopped
        f = np.where(moving, grip * wt, Fa)
        xn = (Fa * (hp * H - H / 2) + f * H / 2) / wt
        ce = lean if lean_fn is None else np.clip(np.asarray(lean_fn(dict(env, moving=moving.astype(float), Fa=Fa, v=v)), float), -0.05, W / 2 - 0.03)
        r = xn / (W / 2 - ce)
        th = tilt(r)
        peak = np.maximum(peak, th)
        released = released | (th > abort_deg)
    x = x + v ** 2 / (2 * grip * G)
    return x, peak
