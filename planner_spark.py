#!/usr/bin/env python
"""Planner process. stdin JSON {sam_obs, posterior, candidates, bic, allowed_patches}
-> stdout JSON {hyps[], ambiguity, next_push, model_patch|null, mode}.
JSON-only boundary: this file imports no simulator/evaluator module and sees only
perception output and posterior summaries.
Modes:  MOCK (default, deterministic rule-based stub; NOT a model result)
        LIVE (muse-spark-1.3 via https://api.meta.ai/v1; only when PROBEZERO_LIVE=1
        was set by the caller after `spend check meta` printed ok). UNVERIFIED."""
import json, os, sys

def mock(req):
    cands = req["candidates"]
    ok = [c for c in cands if c["p_risk"] <= 0.15] or cands
    a = req["posterior"]
    sep = a.get("cluster_sep", 0.0)
    best = max(ok, key=lambda c: c.get("split", 0.0))
    ambiguity = bool(sep > 0.02 or a.get("spread", 0) > 0.03)
    patch = None
    bic = req.get("bic", {})
    if bic and bic.get("base", 0) - min(bic.get("late", 1e9), bic.get("brk", 1e9)) >= 6:
        kind = "late" if bic["late"] <= bic["brk"] else "brk"
        patch = {"kind": kind}
    hyps = ["two parameter sets explain the push equally" if ambiguity else "one parameter set dominates"]
    return dict(hyps=hyps, ambiguity=ambiguity, next_push=best["push"], model_patch=patch, mode="MOCK")

def live(req):
    import urllib.request
    key = None
    for line in open(r"C:\dev\bs\.env", encoding="utf-8"):
        if line.startswith("MODEL_API_KEY="): key = line.split("=", 1)[1].strip()
    prompt = ("You design the next experiment for a pushing robot. Reply with JSON only: "
              '{"hyps":[str],"ambiguity":bool,"next_push":[F,hp,abort],"model_patch":null or {"kind":"late"|"brk"}}. '
              "Choose next_push from candidates. Input: " + json.dumps(req)[:6000])
    body = json.dumps({"model": "muse-spark-1.3", "max_tokens": 300,
                       "messages": [{"role": "user", "content": prompt}]}).encode()
    r = urllib.request.Request("https://api.meta.ai/v1/chat/completions", body,
                               {"Authorization": "Bearer " + key, "Content-Type": "application/json"})
    txt = json.load(urllib.request.urlopen(r, timeout=60))["choices"][0]["message"]["content"]
    out = json.loads(txt[txt.index("{"): txt.rindex("}") + 1]); out["mode"] = "LIVE"
    return out

if __name__ == "__main__":
    if "--selftest-modules" in sys.argv:
        print(json.dumps(sorted(sys.modules))); sys.exit(0)
    req = json.load(sys.stdin)
    use_live = os.environ.get("PROBEZERO_LIVE") == "1"
    print(json.dumps(live(req) if use_live else mock(req)))
