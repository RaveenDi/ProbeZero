"""Perception adapter. MOCK mode: turns the simulator clip into noisy pixel tracks
(stand-in for SAM 3.1 mask centroid + tilt). Never a model result.
LIVE mode (sam-3.1 via https://api.meta.ai/v1) is not exercised: UNVERIFIED."""
import numpy as np
from common import TIP_DEG

class Tracker:
    mode = "MOCK"
    def __init__(self, seed=0, px_sigma=1.5, deg_sigma=0.7):
        self.rng = np.random.default_rng(seed + 977)
        self.ps, self.ds = px_sigma, deg_sigma

    def track(self, clip, concept="box"):
        cx = np.array(clip["cx_px"]) + self.rng.normal(0, self.ps, len(clip["cx_px"]))
        th = np.array(clip["theta_deg"]) + self.rng.normal(0, self.ds, len(clip["theta_deg"]))
        s = clip["px_per_m"]
        c0, c1 = cx[:3].mean(), cx[-3:].mean()
        return {"cx": float(c1 / s), "disp": float((c1 - c0) / s),
                "wobble": float(max(0.0, np.convolve(th, np.ones(3) / 3, "valid").max())),  # peak of 3-pt smoothed tilt
                "tipped": bool(th[-3:].mean() > TIP_DEG), "jitter_px": float(self.ps)}
