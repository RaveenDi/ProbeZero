"""Leak check. (1) grep: hidden-quantity words must not appear in agent-side .py files.
(2) import block: agent-side files must not import sim/evaluator/eval.
Exit 0 = pass, 1 = fail."""
import ast, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ALLOW = {"sim.py", "evaluator.py", "eval.py"}
SKIP_DIRS = {"tests", "scripts", "out", "__pycache__", "docs", "ui"}
WORDS = re.compile(r"mass|friction|\bCOM\b|anomal|getBasePosition|sliding", re.I)
BANNED_IMPORTS = {"sim", "evaluator", "eval"}


def scan(root=ROOT):
    bad = []
    for dp, dn, fn in os.walk(root):
        dn[:] = [d for d in dn if d not in SKIP_DIRS and not d.startswith(".")]
        for f in fn:
            if not f.endswith(".py") or f in ALLOW:
                continue
            src = open(os.path.join(dp, f), encoding="utf-8").read()
            for i, line in enumerate(src.splitlines(), 1):
                if WORDS.search(line):
                    bad.append(f"{f}:{i}: word: {line.strip()[:70]}")
            for node in ast.walk(ast.parse(src)):
                mods = []
                if isinstance(node, ast.Import):
                    mods = [a.name.split('.')[0] for a in node.names]
                if isinstance(node, ast.ImportFrom) and node.module:
                    mods = [node.module.split('.')[0]]
                for m in mods:
                    if m in BANNED_IMPORTS:
                        bad.append(f"{f}: imports {m}")
    return bad


if __name__ == "__main__":
    bad = scan()
    print("LEAK CHECK:", "FAIL" if bad else "PASS")
    for b in bad:
        print("  ", b)
    sys.exit(1 if bad else 0)
