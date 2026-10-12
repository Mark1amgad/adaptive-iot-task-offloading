# 1. Audit of the two supplied files

Both files were found and read. (The Arabic filename of the script arrived as `____________.py`; the content is the 58-line toy prototype. The docx contains text, 4 small tables and only embedded fonts, no images.)
The original script is preserved unchanged at `legacy/toy_prototype_original.py`.

Legend: **[V]** verified by reading/running it · **[A]** assumption · **[?]** cannot be verified from the files.

## 1.1 `تجربه المودل.py` (toy prototype)

I ran it (`python3 legacy/toy_prototype_original.py`, seed 1). It prints average rewards Local −1.486, Edge −0.948, Cloud −0.835, "Adaptive RL" −0.476. **These numbers come from an invented simulator and are not research evidence** (see 3 below).

| # | Finding | Status |
|---|---|---|
| 1 | **Update rule** `Q[s][a] += ALPHA*(r − Q[s][a])` is the Q-learning update with the future term dropped. It is mathematically correct *only* as the terminal / γ = 0 special case (a contextual bandit). It is **not** the requested general rule: there is no `s'`, no `γ·max Q(s',:)`, no terminal flag. | [V] |
| 2 | The new agent implements the general rule `Q(s,a) += α(r + γ·max Q(s',:) − Q(s,a))`, omitting the future term for terminal transitions, with unit tests (`tests/test_agent.py`). | [V] |
| 3 | **Artificial environment**: `run_task` invents latencies (`0.3*size`, `0.1+0.05*size+load`, `wan+0.02*size`), costs (0.1 / 0.4–0.6 / 0.3), noise (±0.05), and deadlines (0.5 / 0.9). The agent is trained *and* evaluated on this same function, so "Adaptive RL beats baselines" holds by construction. | [V] |
| 4 | The simulator is a function of the **discretised labels** (`LAT.index(l)`), so the 20/80 ms and 40/80 % thresholds from the docx are never applied to any measurement. Task-size and deadline thresholds are undefined anywhere. | [V] |
| 5 | States are sampled **uniformly** (`random.choice(STATES)`); a real workload will not be uniform. | [V] |
| 6 | **Silent tie-break bug in evaluation**: `Q[s].index(max(Q[s]))` returns action 0 (Local) for any unvisited / tied row, so the policy silently falls back to Local. Several printed rows differ by ~0.03, below the ±0.05 noise. | [V] |
| 7 | Zero-initialised Q with strictly negative rewards acts as *optimistic initialisation* (forces trying every action). Useful but implicit; it also makes untried actions look best to a greedy evaluator. New code documents it and the frozen policy only considers actions with real training data. | [V] |
| 8 | One global `random.seed(1)`; evaluation continues the training RNG stream; no separate train/test seeds. | [V] |
| 9 | Reward `−(1·lat + 2·miss + 0.5·cost)`: latency clipped to [0,1] by an arbitrary scale; "cost" is an invented constant. Weights and ε schedule (0.3 → 0.02) were kept as *defaults* only. | [V] |
| 10 | No persistence, validation, action mask, logging, tests, or terminal handling. | [V] |

**Preserved**: the 54-cell structure idea (now *derived*, see STATE_SPEC), weights 1/2/0.5, linear ε-decay 0.3→0.02, random tie-breaking in training, and the four-policy comparison structure.

## 1.2 `Qlearning ibrahim attia.docx` (design note, Arabic)

| # | Finding | Status |
|---|---|---|
| 1 | Idea: no fixed best location; Local/Edge/Cloud choice depends on network, edge load, task size. State → Q-table → action. Consistent with the task. | [V] |
| 2 | Typo: output set written `{LOCAL, EDGE, CLAUDE}`; must be CLOUD. | [V] |
| 3 | Inputs listed: task size, network latency, **network load**, Edge utilisation; the state actually built uses task size, latency, Edge utilisation, deadline. **Network load is dropped silently.** | [V] decision needed |
| 4 | Thresholds given: latency <20 / 20–80 / >80 ms (the value 80 itself is ambiguous); Edge utilisation 0–<40 / 40–<80 / 80–100 %. **Not given**: task-size and deadline thresholds, units, or how/when each value is measured. | [V] |
| 5 | `3*3*3*2 = 54` is arithmetically right for those four features. | [V] |
| 6 | The worked example writes rewards directly into cells (−5, +3). The note itself says this is a simplification. Under its own reward formula `−(w1·Lat + w2·Miss + w3·Cost)` a reward of **+3 is impossible** (always ≤ 0). | [V] |
| 7 | The Q-value example tables (−8, −2, −9 …) are illustrative numbers, not measurements. | [V] |
| 8 | "Step 5" (incremental update, future term) is referred to but is not in the file. γ and the MDP-vs-bandit question are never addressed. | [V] |
| 9 | The note cites "the paper" for the feature list; the paper was not supplied. | [?] |

## 1.3 What I did about it
Refactored rather than rewrote: kept the structure and defaults above; moved all thresholds/weights to `config/default.json`; replaced the invented simulator with a protocol where **only real simulator outcomes** train the agent; fixed the update rule, tie-break and train/test issues. Everything the files left open is marked `placeholder` in config and listed in `BLOCKERS.md`.
