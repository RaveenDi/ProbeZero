"""Pure Bayes updater: particles over (load, grip, lean) plus the free constants of each model
patch; BIC model comparison. Models are DSL specs (dsl.py), executed inside the forward model.
No LLM, no simulator import."""
import numpy as np
import model
from common import ABORT_DEG

NP = 20000
BASE = dict(brk=None, lean=None, free={})
# Privileged finite menu: used ONLY by the 'menu' upper-bound baseline. The spark and fixed agents never see it.
MENU = {
    "late": dict(brk=None, lean="lean + c1*moving", free={"c1": (0.02, 0.06)}),
    "brk": dict(brk="c1*grip*load*g", lean=None, free={"c1": (1.2, 2.0)}),
}

def sigma_d(pred): return 0.006 + 0.08 * np.abs(pred)
SIG_W = 1.2


def _particles(spec, seed, n):
    r = np.random.default_rng(seed)
    p = dict(load=np.exp(r.uniform(np.log(0.5), np.log(6.0), n)),
             grip=r.uniform(0.15, 0.95, n), lean=r.uniform(-0.02, 0.04, n),
             c1=np.ones(n), c2=np.ones(n), ll=np.zeros(n))
    for k, (lo, hi) in spec["free"].items():
        p[k] = r.uniform(lo, hi, n)
    return p


def prior(seed=0, menu=False, n=NP):
    post = dict(m={}, spec={}, hist=[], n_obs=0, seed=seed, n=n)
    add_model(post, "base", BASE)
    if menu:
        for k, s in MENU.items(): add_model(post, k, s)
    return post


def predict(p, spec, push, K=60):
    F, hp, ab = push
    return model.simulate(p["load"], p["grip"], p["lean"], F, hp, ab, spec, p["c1"], p["c2"], K)


def _ll(p, spec, push, obs):
    d, w = predict(p, spec, push)
    z1 = (obs["disp"] - d) / sigma_d(d); z2 = (obs["wobble"] - w) / SIG_W
    return -0.5 * (z1 ** 2 + z2 ** 2) - np.log(sigma_d(d)) - np.log(SIG_W)


def add_model(post, name, spec):
    """Add a model (possibly proposed mid-run); replays past observations into its likelihood."""
    p = _particles(spec, post["seed"] * 7 + len(post["m"]), post["n"])
    for push, obs in post["hist"]:
        p["ll"] = p["ll"] + _ll(p, spec, push, obs)
    post["m"][name] = p; post["spec"][name] = spec


def update(post, push, obs):
    new = {}
    for name, p in post["m"].items():
        q = dict(p); q["ll"] = p["ll"] + _ll(p, post["spec"][name], push, obs); new[name] = q
    return dict(m=new, spec=post["spec"], hist=post["hist"] + [(push, obs)], n_obs=post["n_obs"] + 1,
                seed=post["seed"], n=post["n"])


def bic(post):
    n = 2 * post["n_obs"]
    return {name: (3 + len(post["spec"][name]["free"])) * np.log(max(n, 1)) - 2 * p["ll"].max()
            for name, p in post["m"].items()}


def best_model(post, margin=6.0):
    """Best extension beating base by `margin` BIC, else base."""
    b = bic(post)
    ext = [k for k in b if k != "base"]
    if not ext: return "base", b
    e = min(ext, key=lambda k: b[k])
    return (e, b) if b["base"] - b[e] >= margin else ("base", b)


def weights(p):
    w = np.exp(p["ll"] - p["ll"].max()); return w / w.sum()


def sample(post, name, n=200, seed=0):
    p = post["m"][name]; w = weights(p)
    idx = np.random.default_rng(seed).choice(len(w), n, p=w)
    return {k: v[idx] for k, v in p.items() if k != "ll"} | {"ll": np.zeros(n)}


def summary(post, name):
    s = sample(post, name, 200)
    d, w = predict(s, post["spec"][name], (15.0, 0.55, ABORT_DEG))
    return float(d.mean()), float(d.std()), float((w > 18).mean())


def misfit_chi2(post, name="base"):
    """Average chi2 per datum of the best particle of a model (generic residual-misfit alarm)."""
    return float(-2 * post["m"][name]["ll"].max() / max(2 * post["n_obs"], 1))


def residuals(post, name="base", k=250):
    """Compact residual summary per probe (predicted vs seen). All the planner gets."""
    s = sample(post, name, k, 1)
    out = []
    for push, obs in post["hist"]:
        d, w = predict(s, post["spec"][name], push)
        out.append(dict(F=push[0], hp=push[1], obs_disp=round(obs["disp"], 4), pred_disp=round(float(d.mean()), 4),
                        pred_sd=round(float(d.std()), 4), obs_wob=round(obs["wobble"], 1), pred_wob=round(float(w.mean()), 1),
                        moved=bool(obs["disp"] > 0.004), pred_moved=bool(d.mean() > 0.004)))
    return out
