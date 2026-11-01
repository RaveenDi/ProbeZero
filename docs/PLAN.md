> Written by the ProbeZero planning room (Meta Spark panel, no web search), Sun Nov 1. Panel plan: UNVERIFIED until the MVP runs.

# ProbeZero FINAL MVP PLAN (corrected, all BLOCKs applied)

## 1. MVP definition
Smallest loop proving core claim: identical pusher pokes mystery 1-box twice, admits confusion after tap1, then delivers no-tip. PyBullet sim https://pybullet.org/wordpress/ with hidden `[mass,friction,COM_x,anomaly]` where anomaly = 2 families in evaluator only (e.g. sliding-weight + soft-edge/stick-slip). Planner never sees words for them. WIN = Spark ties MI+BIC on closed ambiguous pairs on safety-first clock, beats cage-creep on time among no-tip runs, and detects BOTH anomaly families pre-commit. No 3-box, no real robot, no Three.js.

## 2. Architecture / repo
`/probezero sim.py evaluator.py tracker_sam.py planner_spark.py updater_bayes.py mpc.py eval.py ui/ bs.py docs/PRIOR.md scripts/check_leak.sh`
- `sim.step(push{dx,dy,force,capped}) -> clip.mp4 + gt` gt only to evaluator.
- `tracker_sam(clip,concept="box") -> {cx,cy,theta,wobble,disp}` stills in spike, video only for 1 hero.
- `planner_spark stdin JSON {sam_obs,posterior} -> stdout JSON {hyps[],ambiguity,next_push,model_patch|null}` no sim import, subprocess only. Trial log lives in planner context only (<1500 tokens, last 2 obs+posterior).
- `updater_bayes(prior,obs) -> posterior` pure function, no Spark, no 1M log.
- `mpc.commit(posterior) -> creep/commit + abort-on-wobble` 2-mode only.
- Leak: `check_leak.sh` greps `mass|friction|COM|anomaly|getBasePosition|sliding` outside `sim.py/evaluator.py` + CI import-block; evaluator/ untouchable.

## 3. Milestones (~10h, start after Mon 02:30 reset, Sonnet-parallel)
M0 Spike 2h: 12 paired configs end-to-end. Accept: runs, leak passes, CSV written.
M1 Sim+harness 2.5h: frozen mesh+force-cap for all agents, paired heavy-slick vs light-grippy matched disp + offset-COM tip + 2 anomaly families. Accept: 20 seeds reproducible.
M2 SAM track 1.5h: stills centroid/wobble, 1 hero video track. Accept: <5px jitter clean sim UNVERIFIED, fallback centroid.
M3 Spark planner 2h: short prompt, JSON tool-call, ambiguity flag. Accept: 95% valid JSON first-try.
M4 Bayes(BIC)+2-mode MPC 1h: frozen updater + abort. Accept: displacement error shrinks with 2 probes.
M5 Eval/ablation 1.5h: 30-run paired script. Accept: CSV + Wilson CI.
M6 UI 0.5h: matplotlib replay + side-view + tilt-gauge + SIMULATED ONLY watermark. Accept: 60s renderable, no live calls.

## 4. Evaluation protocol
Spike: 12 (8 ambiguous + 4 surprise 2+2). Full: 30 unseen paired seeds (20 closed ambiguous + 10 surprise 5+5). Baselines: Spark vs MI+BIC-expansion vs cage-creep (compliant cage, same mesh/force-cap) vs random, same SAM masks, 2-probe budget. MI gets same expansion operator (base vs extended via BIC); Spark must win on probes-to-detection, not permission. Truth in `evaluator.py` only. Metrics lexicographic: (1) tip-rate (tip=z-tilt>25deg), (2) wall-steps incl probes among no-tip only, (3) predicted-disp error sanity (no mass/friction RMSE — coupled via limit surface), (4) ambiguity P/R, (5) per-family surprise P/R + probes-to-detection. Stats: paired seeds, Wilson 95% CI https://en.wikipedia.org/wiki/Binomial_proportion_confidence_interval . Require `docs/PRIOR.md` with 3 URLs + differentiator before eval counts, else auto NO-GO.

## 5. Meta essential + ablation
SAM-3.1: only perception (mask+trail/wobble). Spark-1.3: only brain (masks+log -> hyps+ambiguity+next_push+model_patch). Updater/MPC/masks frozen, swap planner only. Spark essential iff: (a) closed-20 tip-rate <= creep and time competitive with MI, AND (b) beats MI+BIC on surprise probes-to-detection + per-family recall. Text-only hyps without executable patch = fail. Else decoration -> kill.

## 6. Risks / cut list
(1) MI+BIC + creep already solve closed set -> mitigated by surprise + lexicographic clock. (2) Spark patch hallucinates -> must parse/execute or scored miss. (3) PyBullet wobble solver artifact UNVERIFIED -> tip defined strictly, watermarked. (4) Credit burn -> stills + token cap. CUT: 3 boxes, webcam, Three.js, wonder-1.0, open-weights, COM_y/full pose, RMSE gate, warehouse ROI claim.

## 7. Demo storyboard (60s)
0-10s WOW side-view: box, banner `Never touched. Heavy? Tippy? 2 pokes.` Tap1 slides identical. Spark caption `Can't tell heavy-slick vs light-grippy. Need tap2.` Tap2 off-axis, SAM trail + red wobble bar + tilt-gauge spike, Bayes bars shrink, commit aborts on wobble then re-aims low-force home. Creep only as 4s timelapse inset with step-clock. P-A-V-R captions: PLAN/ ACT/ VERIFY/ RECOVER(ABORT/RE-AIM). Seed typed on screen. Pitch: mystery box poked twice then shoved home.

## 8. Call / cost budget
Per config: 2x Spark (~1.5k in/300 out) + 2x SAM stills (1 concept). Spike-12: 24 Spark + 14 SAM <$1 UNVERIFIED. Full-30 once, cache masks reuse for all baselines. No live UI calls, replay logs. `python bs.py --check` before any live call; stop if cap blocks (cut surprise-10 first, never leak-check).

## 9. Real-help check
1 sim cube helps nobody Mon morning. Frontier-demo only, not deployment. Warehouse SKU-changeover story cut unless 1 engineer quote + URL by Mon 10:00, else keep UNVERIFIED. CSV column `sim_measured`, UI watermark SIMULATED ONLY, never claim real help. If creep ties on safety-first clock, ship creep.

## 10. DROP-GATE scorecard (Mon 14:00 measured)
GO ProbeZero iff all: (a) leak-check passes + PRIOR.md exists; (b) closed-20: Spark tip-rate lower-bound beats creep (Wilson) and time <= creep among no-tip; within 20% of MI; (c) surprise-10: per-family recall >=70% pre-commit AND tip-rate <= creep AND fewer probes-to-detection than MI+BIC; (d) cost <$1 spike. Else KILL theater, keep NullLab. Demo gate: visible wobble + abort/re-aim on hero seed, else kill.
Candid: ~30% chance to pass UNVERIFIED. Biggest risk: identical-mesh cage-creep ties tip-rate and MI+BIC matches Spark detection, leaving Spark as narration.

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
