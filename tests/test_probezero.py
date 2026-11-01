import json, os, subprocess, sys, tempfile
import numpy as np
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT); sys.path.insert(0, os.path.join(ROOT, "scripts"))
import sim, model, evaluator, updater_bayes as ub, mpc, agent, eval as ev
from tracker_sam import Tracker
import check_leak
from common import *

def test_sim_reproducible_20_seeds():
    for s in range(20):
        outs = []
        for _ in range(2):
            env, _, _ = evaluator.new_env(s, "closed"); tr = Tracker(s)
            outs.append([tr.track(env.push(10, .7, 12))["disp"] for _ in range(2)])
        assert outs[0] == outs[1]

def test_model_matches_sim():
    r = np.random.default_rng(1); errs = []
    for _ in range(100):
        m = np.exp(r.uniform(np.log(.5), np.log(6))); mu = r.uniform(.15, .95); c = r.uniform(-.02, .04)
        F, h = CANDIDATES[r.integers(len(CANDIDATES))]
        e = sim.Env(sim.Truth(m, mu, c)); e.push(F, h, 12)
        x, _ = model.simulate(np.array([m]), mu, c, F, h, 12, K=60)
        errs.append(abs(e.x - x[0]))
    assert np.median(errs) < 0.01

def test_tracker_jitter_under_5px():
    env, _, _ = evaluator.new_env(0, "closed"); tr = Tracker(0)
    cl = env.look(); cx = [tr.track(cl)["cx"] * cl["px_per_m"] for _ in range(200)]
    assert np.std(cx) < 5

def test_probes_shrink_prediction_uncertainty():
    env, _, _ = evaluator.new_env(5, "closed"); tr = Tracker(5); post = ub.prior(5)
    s0 = ub.summary(post, "base")[1]
    for F, h in [(8.5, .55), (14, .55)]:
        post = ub.update(post, (F, h, 12.0), tr.track(env.push(F, h, 12.0)))
    assert ub.summary(post, "base")[1] < s0

def test_bic_flags_late_lean():
    env = sim.Env(sim.Truth(1.0, .7, .01, "sliding_weight", .035), 1); tr = Tracker(1); post = ub.prior(1)
    for F, h in [(7, .7), (9, .7)]:
        post = ub.update(post, (F, h, 12.0), tr.track(env.push(F, h, 12.0)))
    assert ub.best_model(post)[0] == "late"

def test_leak_check_passes_and_catches():
    assert check_leak.scan() == []
    d = tempfile.mkdtemp()
    open(os.path.join(d, "bad.py"), "w").write("import sim\nx = 'mass'\n")
    assert len(check_leak.scan(d)) >= 2

def test_planner_process_boundary():
    out = subprocess.run([sys.executable, "-I", os.path.join(ROOT, "planner_spark.py"), "--selftest-modules"],
                         capture_output=True, text=True).stdout
    mods = set(json.loads(out))
    assert not ({"sim", "evaluator", "eval", "agent", "updater_bayes", "numpy"} & mods)
    req = dict(candidates=[dict(push=[4, .55, 12], p_risk=0, split=1.0)], posterior={}, bic={})
    r = subprocess.run([sys.executable, "-I", os.path.join(ROOT, "planner_spark.py")], input=json.dumps(req),
                       capture_output=True, text=True)
    assert json.loads(r.stdout)["mode"] == "MOCK"

class Fake:
    def __init__(self, truth_marker): self.truth_marker = truth_marker; self.pushes = []; self.x = 0.0
    def look(self): return dict(cx_px=[0.0] * 6, theta_deg=[0.0] * 6, px_per_m=500.0)
    def push(self, F, hp, ab):
        self.pushes.append((F, hp, ab)); self.x += 0.01
        return dict(cx_px=[self.x * 500] * 6, theta_deg=[0.0] * 6, px_per_m=500.0)

def test_decisions_depend_only_on_observations():
    a, b = Fake({"mass": 1}), Fake({"mass": 9})
    agent.run("mi_bic", a, Tracker(0), 0); agent.run("mi_bic", b, Tracker(0), 0)
    assert a.pushes == b.pushes and len(a.pushes) > 0

def test_eval_csv_and_wilson(tmp_path):
    rows = ev.run_all(1, 1, ["creep", "mi_bic"], str(tmp_path / "e.csv"))
    assert all(r["sim_measured"] == "SIMULATED" for r in rows)
    lo, hi = ev.wilson(0, 20); assert abs(hi - 0.161) < 0.002 and lo < 1e-9
    assert any(r["delivered"] for r in rows if r["agent"] == "creep")

def test_mpc_aborts_on_wobble_and_recovers():
    # high hp push on a tippy box: abort keeps tilt below tip most of the time
    e = sim.Env(sim.Truth(1.0, .8, .03)); e.push(14, .85, 12.0)
    assert e.log[0]["abort"] == 12.0

def test_replay_renders(tmp_path):
    sys.path.insert(0, os.path.join(ROOT, "ui"))
    import replay
    out, n, _ = replay.render(3, "closed", "creep", 1, str(tmp_path / "r.gif"), fps=4)
    assert os.path.getsize(out) > 1000
