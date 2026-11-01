# ProbeZero builder brief (from docs/PLAN.md)

Read docs/PLAN.md and docs/IDEA.md first. Rules: no git init/commit/push; no live Meta call without `python battle-stations.py spend check meta <usd>` (run from the planning repo root, one level up) and `spend add` after; keys only in C:\devs\.env, never print; label every simulated result SIMULATED; planner agent never sees hidden ground truth; run tests yourself; final reply at most 15 lines.

## BUILDER BRIEF (execute now)
1. Folder /probezero, stack PyBullet+Python+matplotlib; no git, no live calls without `python bs.py --check`.
2. Freeze sim.py: 1-box+pusher same mesh+force-cap for all; evaluator.py only holds truth+2 anomalies.
3. Planner subprocess JSON stdin/out only; ban anomaly words in planner/*; log in planner (<1500 tok).
4. Updater pure prior+obs->posterior + BIC expansion; MPC 2-mode creep/commit+abort.
5. M0 spike 12 paired (8+2+2) Spark vs MI+BIC vs creep; PASS leak+CSV.
6. M1-M4 build in order, each with accept test above; stills first, 1 hero video last.
7. M5 full 30 paired (20+5+5), same masks, lexicographic: tip-rate then steps; Wilson CI.
8. M6 matplotlib side-view+tilt-gauge+watermark SIMULATED ONLY; 60s replay, no live calls.
9. Write docs/PRIOR.md (3 URLs) before eval counts; CSV col sim_measured.
10. Report DROP-GATE numbers Mon 14:00; stop at budget 24 Spark+14 SAM spike.
