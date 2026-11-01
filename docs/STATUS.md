# ProbeZero STATUS (2026-11-01). Everything below is SIMULATED.
## What runs
sim.py (hidden truth) -> tracker_sam.py (MOCK) -> agent.py (spark|mi_bic|creep|random) -> eval.py CSV (+Wilson CI); ui/replay.py GIF; scripts/check_leak.py; 11 pytest tests (`python -m pytest -q tests`, 11 passed, ~90 s).
Start: `python eval.py --out out/eval.csv` (~2.5 min), `python ui/replay.py --seed 3 --agent mi_bic` (hero GIF out/replay_hero.gif, 468 frames).
## Physics change (documented)
`pip install pybullet` FAILED (no wheel/build tools on this Windows+Py3.12 box). Replaced with own 2D side-view rigid-box model (Coulomb sliding + support-point tipping, tilt = 100*(r-0.75) deg, tip > 25 deg) in sim.py; agent has its own vectorised copy (model.py, neutral names). Hidden: mass, friction, COM_x, anomaly (sliding_weight = lean jumps once moving; stick_slip = break-away > moving threshold), plus a hidden abort latency (6 substeps) the agent does not model. Pusher height restricted to {0.55,0.70,0.85}H so tipping is possible. Not PyBullet: wobble is analytic, not solver output.
## Meta paths
- Spark planner: planner_spark.py subprocess, JSON only. MOCK = deterministic rule stub (NEVER a model result). LIVE code path written (muse-spark-1.3, key read from C:\dev\bs\.env inside the planner process) but NEVER RUN: UNVERIFIED. `spend check meta 0.05` printed ok, no live call made (fuel/budget); no spend recorded.
- SAM 3.1: only a MOCK tracker (noisy centroid/tilt from sim clip, 1.5 px jitter, test <5 px). Live SAM UNVERIFIED.
## Leak check
`python scripts/check_leak.py` = PASS (word grep + import block over agent-side files); tests prove the planner process loads no sim/evaluator/numpy, that the checker catches a planted leak, and that decisions are identical for different hidden truths given identical observations. Caveat: updater/mpc/agent run in-process and are protected by grep/import-block, not by process isolation; only the planner is a true process boundary.
## Eval (30 paired seeds: closed 20 + surprise 10; probe budget 3 for model agents; Wilson 95%)
| group | agent | tipped | tip-rate CI | delivered | wall-steps (no-tip, delivered) | detect recall |
|---|---|---|---|---|---|---|
| closed-20 | spark(MOCK) | 1/20 | 0.009-0.236 | 15/20 | 5.2 | FP 0 |
| closed-20 | mi_bic | 0/20 | 0.000-0.161 | 20/20 | 6.15 | FP 0 |
| closed-20 | creep | 0/20 | 0.000-0.161 | 20/20 | 27.5 | FP 0 |
| closed-20 | random | 1/20 | 0.009-0.236 | 13/20 | 6.0 | FP 0 |
| surprise-10 | spark(MOCK) | 4/10 | 0.168-0.687 | 3/10 | 4.7 | 0/10 |
| surprise-10 | mi_bic | 3/10 | 0.108-0.603 | 4/10 | 6.25 | 0/10 |
| surprise-10 | creep | 3/10 | 0.108-0.603 | 5/10 | 23.8 | 0/10 |
| surprise-10 | random | 5/10 | 0.237-0.763 | 1/10 | 9.0 | 0/10 |
Ambiguity after probe 1 (closed): 6/20 truly ambiguous; both planners flag 20/20 (recall 6/6, precision 6/20: flag is uninformative).
Note: run-to-run, the last full run was after the final sim change; earlier tuning runs used the same 30 seeds (seeds not held out from development: treat as optimistic).
## Drop-gate scorecard (measured so far)
(a) leak-check PASS, PRIOR.md exists (URLs unverified): YES
(b) closed-20: Spark tip-rate lower bound beats creep? NO (0.009 vs 0.000; spark MOCK tipped 1). Time <= creep among no-tip: YES (5.2 vs 27.5). Within 20% of MI: YES on time (5.2 vs 6.15) but delivery 15/20 vs 20/20: NO.
(c) surprise-10: per-family recall >=70%: NO (0/10 for all agents; tips during first-contact probes end runs before detection; stick_slip is not identifiable below break-away). tip <= creep: NO (4 vs 3). Fewer probes-to-detection than MI+BIC: untestable (no detections in this run).
(d) cost <$1 spike: YES, $0 spent (no live call).
VERDICT on these numbers: GATE NOT PASSED. The stub planner cannot show Meta is essential; creep ties tip-rate and MI+BIC beats the stub on delivery. A real Spark run is the only open question and is UNVERIFIED. Demo gate (visible wobble + abort/re-aim on hero seed) not shown: hero seed 3 (mi_bic, closed) delivers with no tip; GIF shows probes + commits.
## Gaps
Surprise detection weak (identifiability + probe-induced tips); tip-rate barely separates agents on closed set; no 3-box, no webcam, no Three.js; the UI is a matplotlib GIF only; no sensitivity analysis of sim constants; eval seeds used during tuning.
