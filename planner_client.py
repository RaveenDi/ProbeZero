"""Parent-side wrapper: runs planner_spark.py in a subprocess, JSON in/out only."""
import json, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))


def call(req, live=False):
    env = {k: v for k, v in os.environ.items() if k != "MODEL_API_KEY"}
    env["PROBEZERO_LIVE"] = "1" if live else "0"
    p = subprocess.run([sys.executable, "-I", os.path.join(HERE, "planner_spark.py")],
                       input=json.dumps(req), capture_output=True, text=True, timeout=90, env=env)
    if p.returncode != 0:
        return None
    return json.loads(p.stdout)


def valid(out, cand_pushes):
    """Schema + executability check; invalid output is scored as a miss upstream."""
    try:
        np_ = tuple(out["next_push"])
        ok = any(abs(np_[0] - c[0]) < 1e-6 and abs(np_[1] - c[1]) < 1e-6 for c in cand_pushes)
        patch = out.get("model_patch")
        okp = patch is None or patch.get("kind") in ("late", "brk")
        return bool(ok and okp and isinstance(out["ambiguity"], bool))
    except Exception:
        return False
