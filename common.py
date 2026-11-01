"""Shared task constants (visible geometry + task spec). No hidden quantities here."""
W = 0.24        # box width (m), visible in the mask
H = 0.16        # box height (m)
G = 9.81
T = 0.25        # push duration (s)
FMAX = 45.0     # force cap, identical for every agent
TIP_DEG = 25.0  # tipped if tilt exceeds this
GOAL = 0.30     # distance to the home area (m)
TOL = 0.03      # delivery tolerance (m)
ABORT_DEG = 12.0
ROT = 24.0      # elastic base rotation (deg) per unit overturning ratio r, below tipping onset r=0.75
PX_PER_M = 500.0
FORCES = [1.5, 2, 2.5, 3, 4, 5, 6, 7, 8.5, 10, 12, 14, 17, 20, 24, 29, 35, 45]
HEIGHTS = [0.30, 0.55, 0.70, 0.85]   # 0.30 = low reach (added in pass 2: needed for safe probing)
CANDIDATES = [(float(f), float(h)) for f in FORCES for h in HEIGHTS]


def tilt(r):
    """Visible rotation (deg) vs overturning ratio r (floats or arrays). Pass 2: observable at every force."""
    import numpy as np
    return ROT * np.minimum(r, 0.75) + 60.0 * np.maximum(0.0, r - 0.75)
