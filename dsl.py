"""Restricted expression DSL for model patches. Validated by AST whitelist, executed by the
updater inside the forward model. No eval(), no attribute access, no calls except min/max/abs."""
import ast
import numpy as np

STATIC = {"load", "grip", "lean", "g", "c1", "c2"}
DYNAMIC = STATIC | {"moving", "Fa", "v"}
FUNCS = {"min": np.minimum, "max": np.maximum, "abs": np.abs}
MAXLEN = 90


def _ev(node, env, names):
    if isinstance(node, ast.Expression): return _ev(node.body, env, names)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)) and not isinstance(node.value, bool):
        return float(node.value)
    if isinstance(node, ast.Name):
        if node.id not in names: raise ValueError("name not allowed: " + node.id)
        return env[node.id]
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.USub, ast.UAdd)):
        v = _ev(node.operand, env, names); return -v if isinstance(node.op, ast.USub) else v
    if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Add, ast.Sub, ast.Mult, ast.Div)):
        a, b = _ev(node.left, env, names), _ev(node.right, env, names)
        return a + b if isinstance(node.op, ast.Add) else a - b if isinstance(node.op, ast.Sub) else a * b if isinstance(node.op, ast.Mult) else a / b
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in FUNCS and not node.keywords:
        return FUNCS[node.func.id](*[_ev(a, env, names) for a in node.args])
    raise ValueError("construct not allowed: " + type(node).__name__)


def compile_expr(src, names):
    if not isinstance(src, str) or len(src) > MAXLEN: raise ValueError("bad expression")
    tree = ast.parse(src, mode="eval")
    return lambda env: _ev(tree, env, names)


def validate(patch):
    """patch = {"break_force": str|null, "lean_eff": str|null, "free": {"c1":[lo,hi], "c2":[lo,hi]}}
    Returns a spec {brk, lean, free} or None if unparseable / non-executable."""
    try:
        if not isinstance(patch, dict): return None
        brk, lean = patch.get("break_force"), patch.get("lean_eff")
        if brk is None and lean is None: return None
        free = patch.get("free") or {}
        if len(free) > 2 or any(k not in ("c1", "c2") for k in free): return None
        fr = {}
        for k, (lo, hi) in free.items():
            lo, hi = float(lo), float(hi)
            if not (-1.0 <= lo < hi <= 10.0): return None
            fr[k] = (lo, hi)
        dummy = {k: np.array([0.5, 1.0, 2.0]) for k in DYNAMIC}
        dummy["g"] = 9.81; dummy["load"] = np.array([1.0, 2.0, 3.0])
        for k in ("c1", "c2"):
            dummy[k] = np.array([fr[k][0], sum(fr[k]) / 2, fr[k][1]]) if k in fr else np.ones(3)
        if brk is not None:
            r = np.asarray(compile_expr(brk, STATIC)(dummy), float)
            if not np.all(np.isfinite(r)) or np.any(r <= 0): return None
        if lean is not None:
            r = np.asarray(compile_expr(lean, DYNAMIC)(dummy), float)
            if not np.all(np.isfinite(r)): return None
        return dict(brk=brk, lean=lean, free=fr)
    except Exception:
        return None
