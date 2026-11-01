# ProbeZero (owner-chosen idea, Nov 1)

**Category:** Push the Frontier, robotics. **Tagline:** Don't tell the AI how something works. Give it a goal and let it discover the rules.

An AI that learns how the physical world works by conducting its own experiments.

## The concept
Three identical-looking boxes sit in front of a robot. One is heavy. Another is light but has high friction. The third tips over easily. The robot has never touched them and does not know their physical properties. The task: *move all three boxes into the designated area without tipping them over.*

Instead of blindly executing a plan, the AI behaves like a scientist: it forms hypotheses, selects small experiments, observes results, updates its understanding, and then attempts the real task.

## How it works
1. **Observe the unknown environment.** SAM 3.1 identifies and tracks objects. Muse Spark interprets the task and available actions.
2. **Form competing hypotheses.** "The box may be heavy, or the surface may have high friction."
3. **Choose an experiment.** Apply a small controlled push, measure the response, decide whether another experiment is needed.
4. **Update its physical model.** A numerical estimator narrows the range of plausible mass, friction and stability values.
5. **Execute a safer plan.** Choose a pushing strategy using the experimentally updated model.

## The feature that could impress judges
The robot says: *"I cannot distinguish these two explanations from the first experiment. I need another measurement."* Then it designs that next experiment itself, rather than interacting randomly.

## Architecture (owner's sketch)
| Component | Technology |
|---|---|
| Visual perception | Meta SAM 3.1 |
| Hypothesis and experiment planning | Meta Muse Spark |
| Physical simulation | PyBullet |
| Physical-property estimation | Bayesian inference |
| Action optimization | Model predictive control |
| Interactive visualization | React + Three.js |

Grounded in existing research (e.g. MIT robots estimating hidden physical properties through controlled interactions). The originality is not inventing active physical learning, but showing a general-purpose AI experiment planner integrated with perception, uncertainty estimation and physical control.

## Four-day plan (sketch)
Day 1 simulated environment with hidden properties and controllable pushes. Day 2 Muse Spark with structured hypothesis generation. Day 3 experiment selection, Bayesian updates, task execution. Day 4 SAM perception, evaluation against random experiments, record the demo.

**Critical validation:** the planning agent must NOT see the simulator's hidden mass or friction values. Those are accessible only to the benchmark evaluator. Otherwise the demonstration proves nothing.

Use a simulated robot as the guaranteed demo; if time permits, reproduce one experiment with a real object and a webcam. Present it honestly as a simulated proof of concept with measurable results (deliberate experiments vs random actions on unseen configurations).

## Candid notes from the tower
- It is a SIMULATED proof of concept. Earlier the owner rejected simulated demos as "not real help"; this one must earn its place on measured results and on the frontier story.
- It shares the core pattern of the earlier TwinTap and Figure Falsifier (two hypotheses, find the discriminating experiment). What is new here: closed loop with physical control, perception, and an executed task.
- Meta must be ESSENTIAL: show by ablation that Spark's hypothesis/experiment design beats a scripted or pure-Bayesian experiment selector, or it is decoration.
