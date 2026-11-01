# ProbeZero

**Don't tell the AI how something works. Give it a goal and let it discover the rules.**

ProbeZero is an experiment-planning agent: given a box it has never touched, it forms competing hypotheses about hidden mass, friction and balance, chooses small probing pushes that would tell the hypotheses apart, updates a Bayesian physical model, and then delivers the box without tipping it. Built for the Meta Global AI Developer Hackathon (Push the Frontier).

## Status: honest summary
- **Simulated proof of concept.** All results are produced in a 2D side-view rigid-body tipping model written for this project (PyBullet would not install in the build environment). Every output is labelled `SIMULATED`.
- **Meta models are not yet shown to be essential.** The planner (muse-spark-1.3) and tracker (sam-3.1) adapters exist, but the evaluated runs so far use a labelled MOCK stub; live Meta runs are UNVERIFIED until the logged calls say otherwise. In the first offline evaluation a non-Meta Bayesian baseline matched or beat the planner, and surprise-anomaly detection was 0/10: the current work is diagnosing and fixing that (see `docs/DIAGNOSIS.md` and `docs/STATUS.md` when present).
- The planner process never sees the simulator's hidden values; `scripts/check_leak.py` and tests enforce this.

## Run it
```
pip install -r requirements.txt
python -m pytest -q tests
python eval.py --out out/eval.csv
python ui/replay.py --seed 3 --agent mi_bic
```
Live Meta calls are off by default. Copy `.env.example` to `.env` and add a Meta Model API key to try live mode.

## Built during the hackathon
Everything in this repository was written during the Meta Global AI Developer Hackathon (Oct 26 to Nov 4, 2026), mainly Oct 31 to Nov 1, with coding agents including Meta's Muse Code, and planned in a multi-agent brainstorming setup. Meta models used or planned: `muse-spark-1.3` (hypothesis and experiment planning) and `sam-3.1` (object tracking). Libraries: numpy, matplotlib, pillow, pytest.

## License
Not yet chosen by the owner.
