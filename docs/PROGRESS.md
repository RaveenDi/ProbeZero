M0 done: pybullet install failed -> own 2D tipping sim; 12-config smoke ran, leak PASS, CSV written (sim_measured=SIMULATED).
M1 done: sim.py frozen (same force cap FMAX=45, same pusher for all agents), 2 anomaly families, 20 seeds reproducible (test).
M2 done (MOCK only): tracker jitter 1.5 px < 5 px (test); live SAM UNVERIFIED.
M3 done (MOCK only): planner_spark.py JSON subprocess, schema+patch validation; live path unrun, UNVERIFIED.
M4 done: Bayes particles + BIC expansion + 2-mode MPC with abort; prediction spread shrinks after 2 probes (test); BIC flags late-lean (test).
M5 done: eval.py 30 paired seeds, Wilson CIs; closed mi_bic 20/20 delivered in 6.15 steps vs creep 27.5; surprise recall 0/10 all agents.
M6 done: ui/replay.py matplotlib GIF (SIMULATED ONLY watermark), 60 s hero render ok; 11/11 pytest pass.
