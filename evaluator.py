"""Evaluator: owns the hidden truth. Generates configs and scores agent outcomes."""
import numpy as np
from sim import Truth, Env
import model


LATE_RANGE = (0.03, 0.05)   # extra lean (m) once moving
BRK_RANGE = (1.3, 1.8)      # break-away / moving threshold ratio


def make_config(seed, group):
    r = np.random.default_rng(10_000 + seed)
    fam = "heavy_slick" if r.random() < .5 else "light_grippy"
    if fam == "heavy_slick":
        m, mu = r.uniform(2.5, 5.0), r.uniform(0.18, 0.35)
    else:
        m, mu = r.uniform(0.6, 1.4), r.uniform(0.55, 0.85)
    c = r.uniform(-0.01, 0.035)
    if group == "closed":
        return Truth(m, mu, c), None, fam
    an = "sliding_weight" if seed % 2 == 0 else "stick_slip"
    st = r.uniform(*LATE_RANGE) if an == "sliding_weight" else r.uniform(*BRK_RANGE)
    return Truth(m, mu, c, an, st), an, fam


def new_env(seed, group):
    t, an, fam = make_config(seed, group)
    return Env(t, seed), an, fam


FAMILY_MAP = {"sliding_weight": "late", "stick_slip": "brk", None: None}


def truly_ambiguous(truth, push=(15.0, 0.55, 12.0), n=600, seed=0):
    """True if some parameter set from the OTHER family reproduces this push's outcome."""
    r = np.random.default_rng(seed)
    d0, w0 = model.simulate(np.array([truth.mass]), truth.friction, truth.com_x, *push)
    slick = truth.friction < 0.45
    m = r.uniform(0.6, 1.4, n) if slick else r.uniform(2.5, 5.0, n)
    mu = r.uniform(0.55, 0.85, n) if slick else r.uniform(0.18, 0.35, n)
    d, w = model.simulate(m, mu, truth.com_x, *push)
    return bool(np.any((abs(d - d0[0]) < 0.015) & (abs(w - w0[0]) < 3.0)))
