"""Ground-truth world (evaluator side). Hidden: mass, friction, com_x, anomaly.
Independent scalar implementation (finer substeps) of a pushed box in side view:
a rigid box that slides with Coulomb friction and tips when the support point
leaves the base. NOT PyBullet (build tools unavailable; see docs/STATUS.md).
"""
import math
import numpy as np
from common import W, H, G, T, FMAX, TIP_DEG, PX_PER_M, tilt

K = 60
LAT = 6   # hidden abort latency (substeps): the reality gap the agent does not model

class Truth:
    def __init__(self, mass, friction, com_x, anomaly=None, strength=0.0):
        self.mass, self.friction, self.com_x = mass, friction, com_x
        self.anomaly, self.strength = anomaly, strength  # 'sliding_weight' | 'stick_slip' | None

class Env:
    """Pusher + one box. Planner-side code only ever sees push() clips."""
    def __init__(self, truth: Truth, seed=0):
        self.truth = truth
        self.rng = np.random.default_rng(seed)
        self.x = 0.0
        self.tipped = False
        self.log = []   # every frame for replay (evaluator/UI only)

    def look(self):
        return {"cx_px": [self.x * PX_PER_M] * 6, "theta_deg": [0.0] * 6, "px_per_m": PX_PER_M}

    def push(self, F, hp, abort_deg):
        tr = self.truth
        F = min(float(F), FMAX)
        m, mu, c = tr.mass, tr.friction, tr.com_x
        late = tr.strength if tr.anomaly == 'sliding_weight' else 0.0
        mus = mu * (tr.strength if tr.anomaly == 'stick_slip' else 1.0)
        dt = T / K; v = 0.0; moving = False; released = False
        xs = []; ths = []; x0 = self.x; peak = 0.0; wt = m * G
        for k in range(K):
            t = (k + 0.5) * dt
            Fa = 0.0 if released else F * min(1.0, t / (0.4 * T))
            if not moving and Fa > mus * wt: moving = True
            if moving:
                a = (Fa - mu * wt) / m
                vn = max(v + a * dt, 0.0)
                if vn <= 0 and a <= 0: moving = False
                self.x += 0.5 * (v + vn) * dt if moving or v > 0 else 0.0
                v = vn if moving else 0.0
            f = mu * wt if moving else Fa
            ce = c + (late if moving else 0.0)
            xn = (Fa * (hp * H - H / 2) + f * H / 2) / wt
            r = xn / (W / 2 - ce)
            th = float(tilt(r))
            peak = max(peak, th)
            ths.append(th)
            if len(ths) > LAT and max(ths[-LAT - 1:-1] or [0]) > abort_deg: released = True
            ths.pop()
            if th > TIP_DEG: self.tipped = True
            if self.tipped: th = 90.0
            xs.append(self.x); ths.append(th)
        self.x += v * v / (2 * mu * G)
        xs += [self.x] * 6; ths += [ths[-1]] * 6
        self.log.append(dict(F=F, hp=hp, abort=abort_deg, x=xs, th=ths, tipped=self.tipped))
        return {"cx_px": [q * PX_PER_M for q in [x0] + xs],
                "theta_deg": [0.0] + ths, "px_per_m": PX_PER_M}
