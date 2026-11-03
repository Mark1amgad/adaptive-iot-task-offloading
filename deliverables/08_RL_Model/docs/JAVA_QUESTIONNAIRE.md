# Message to the Java / iFogSim developer

Hi — the Python Q-learning component is ready and tested against *scripted* messages only (`rl_model/docs/PROTOCOL.md`, `schemas/`, `examples/`). I have **not** seen the iFogSim code, so I assumed nothing about its APIs. Please confirm or correct the points below (short answers are fine).

**Decision hook**
1. Where in your code is a task's placement decided? Can we block there until Python replies (synchronous call per task)? Roughly how many tasks per run and how many decisions can overlap in time?
2. Is Local/Edge/Cloud one choice per task, and can the chosen target be forced for that task?
3. Can Edge or Cloud be unavailable (mask via `available_actions`)? What should happen if Python replies with an error or times out (default policy, timeout value)?

**State features (must be known *before* the decision)** — for each, tell me the exact source, unit and staleness:
4. Task computational length (MI?), input/output data size (bytes), per-task deadline (ms from creation?).
5. WAN latency to the Cloud: configured link latency or measured RTT? How fresh is the value at decision time?
6. Edge utilisation: fraction of MIPS (or RAM?) in use on the edge node at that moment? Is there more than one edge node?
7. Is the originating IoT device's CPU load available (optional `device_utilization`)? Is any network-load value available?
8. Please give realistic min/median/max values for each so we can set bin thresholds (the current task-size/deadline thresholds are placeholders).

**Outcome**
9. When a task finishes, can you report `latency_ms` (creation → result received), `deadline_met`, `status` (completed/failed + reason), `bandwidth_bytes` (which links count?), `energy_joules`, and `executing_node_utilization`? Which of these does your simulator really measure? Are failures possible (what causes them)?
10. Can a *next decision point* be defined per task (for the optional sequential/MDP mode), or are tasks effectively independent? (I default to independent decisions.)

**Run control**
11. Can you launch a persistent child process (`python -m rl_model.server ...`), pass `run_id`, `phase` and `sim_seed` in `hello`, and use *different* simulator seeds for train and test runs? Is the simulation deterministic for a given seed?
12. Which JSON library is already in the project? Java version?
13. Can you run the four test policies (Local / Edge / Cloud / trained Q) on the same seeds and write nothing but protocol lines to the process's stdin?

Deliverable I need back: answers above + one captured sample session (`stdin` lines you send) so I can replay it against the server.
