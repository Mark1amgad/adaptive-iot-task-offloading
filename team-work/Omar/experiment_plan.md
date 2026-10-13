# Experiment Plan — IoT Task Offloading (Local / Edge / Cloud)

**Owner:** Omar — Experiment Design & Evaluation  
**Project status:** Draft template. Confirm all settings and output columns with the simulation owner before final experiments.

## 1. Project goal

Evaluate an AI-based task-offloading policy against fixed baseline policies. For each task, the system may execute locally, on an edge server, or in the cloud.

The evaluation asks: **Under which scenarios, if any, does the AI policy improve task completion and deadline performance compared with fixed policies?**

Do not assume the AI policy is better before measuring real simulation results.

## 2. Terms in simple language

- **Task:** A unit of work submitted by an IoT device.
- **Offloading:** Choosing where the task executes.
- **Policy:** The rule used to choose the execution location.
- **Baseline:** A reference policy used for comparison.
- **Scenario:** A defined set of workload, network, deadline, and resource settings.
- **Run:** One execution of a scenario under one policy.
- **Metric:** A numerical measurement used to evaluate the run.
- **CSV:** A text file containing rows and columns, commonly used to store simulation results.

## 3. Policies to compare

Use the same policy names in the CSV wherever possible:

1. **Local Only** — send every task to the local device.
2. **Edge Only** — send every task to an edge server.
3. **Cloud Only** — send every task to the cloud.
4. **AI Model** — let the team's model choose Local, Edge, or Cloud for each task.

Optional additional policies (such as Random or Rule-Based) may be included only after the team documents their exact decision rules.

## 4. Fair-comparison rules

For policies compared inside the same scenario:

- Use the same workload/task definitions.
- Keep the topology and device capabilities the same.
- Keep network bandwidth and latency settings the same.
- Keep task deadlines and other scenario settings the same.
- Use the same random seed across policies when the simulator supports controlled seeds.
- Repeat runs if the simulator has randomness, and save every run separately.
- Record failed, rejected, and unfinished tasks. Do not silently remove them.
- Confirm whether latency means task submission/arrival until task completion, and whether network transmission time is included.
- Change the policy being evaluated, not unrelated simulation settings.
- If any of these conditions cannot be met, record the limitation in the final report.

## 5. Scenario plan

Start with a small set. Fill in the actual configuration values with the simulation owner; labels alone are not enough.

| Scenario ID | Intended condition | Settings that must be recorded |
|---|---|---|
| S1_Normal | Typical conditions | task count/arrival rate, bandwidth, network latency, deadlines, resources |
| S2_HighLoad | Higher task load | exact task count or arrival rate; all other settings |
| S3_LimitedNetwork | More constrained network | exact bandwidth/latency values; all other settings |
| S4_TightDeadline | Tighter deadlines | actual deadline values; all other settings |

Do not invent configuration values. Record the values actually used by iFogSim.

## 6. Metrics and exact definitions

Let **N** be the number of tasks submitted in a single scenario, policy, and run. Failed and unfinished tasks remain in N.

### 6.1 Average latency of completed tasks (ms)

Mean of `latency_ms` for tasks whose `completed` value is true.

- Lower is generally better.
- This metric excludes failed/unfinished tasks, so always report it alongside completion and deadline metrics.
- If no task completed, report the value as blank/NaN, not zero.

### 6.2 Deadline success rate (%)

`100 × number of completed tasks with latency_ms <= deadline_ms / N`

- Higher is better.
- A failed or unfinished task does not count as a success.

### 6.3 Deadline miss rate (%)

`100 × (N - number of tasks meeting their deadlines) / N`

- Lower is better.
- Failed/unfinished tasks count as deadline misses under this project definition.

### 6.4 Task failure rate (%)

`100 × number of tasks not completed / N`

- Lower is better.
- The simulator team must define what counts as failed versus unfinished.

### 6.5 Optional metrics

Only calculate these if the simulator actually records them with documented units and definitions:

- `energy_j`: energy in joules.
- `resource_utilization_pct`: resource utilization from 0 to 100 percent, with the sampling/aggregation method documented.

Never fabricate measurements that the simulator does not provide. If an optional column is absent, the script should simply omit that metric.

## 7. CSV agreement with the simulation owner

Agree on the output schema with Ayoub before final experiments. The starter analysis script expects **one row per task per policy per run**.

Required columns:

| Column | Meaning / rule |
|---|---|
| `task_id` | Stable task identifier |
| `policy` | Local Only / Edge Only / Cloud Only / AI Model |
| `scenario` | Scenario ID such as S1_Normal |
| `run_id` | Repetition ID such as run_01 |
| `completed` | Whether the task completed; use true/false or 1/0 |
| `latency_ms` | End-to-end task latency in milliseconds; blank for unfinished tasks |
| `deadline_ms` | Deadline in milliseconds |

Optional columns: `energy_j`, `resource_utilization_pct`, `selected_location`, `seed`.

Important questions for Ayoub:
1. Does one CSV row represent one task, one event, or one whole simulation run?
2. What exactly starts and ends the latency timer?
3. Are network delays included?
4. How are failures and tasks still running at simulation end represented?
5. Are the same task IDs and random seeds used across policies?
6. What are the exact units for every numeric column?

If the actual CSV has a different structure, adapt the script; do not force it into this schema without understanding the data.

## 8. Analysis workflow

1. Inspect the CSV header and a few rows.
2. Check column names, units, missing values, and duplicate task/policy/scenario/run records.
3. Calculate per-run metrics for each policy and scenario.
4. If multiple runs exist, summarize the run-level metrics with mean, standard deviation, and number of runs.
5. Export the cleaned task-level metrics and summary tables.
6. Plot latency, deadline success, deadline miss, and failure rate.
7. Plot energy/resource utilization only if those columns exist.
8. Compare policies within the same scenario.
9. Explain trade-offs rather than selecting a winner based on one metric alone.

## 9. Repetitions and reporting

If the simulator is stochastic, use multiple independent runs per policy and scenario where feasible. Record the seed and run ID. Report mean, standard deviation, and number of runs. Do not claim statistical significance from a single run. Formal statistical tests should be chosen only after confirming whether runs are paired and checking the assumptions.

## 10. Decision and reporting rules

The AI policy is not automatically better if it improves latency but causes more failures or misses more deadlines. Discuss all important metrics and scenarios. State the tested conditions, number of tasks/runs, data limitations, and any trade-offs.

## 11. Deliverables

- `experiment_plan.md` — updated with the actual experimental configuration.
- `analyze_results.py` — CSV validation, metrics, summaries, and plots.
- `results/` — actual simulator CSVs and analysis outputs.
- A concise report with setup, measurements, plots, limitations, and evidence-based conclusions.

## 12. Pre-run checklist

- [ ] Policy decision rules documented.
- [ ] Scenario settings written down with actual values.
- [ ] Same tasks and conditions used for policy comparisons.
- [ ] Latency boundary and units confirmed.
- [ ] Failed/unfinished tasks included in the denominator.
- [ ] CSV schema agreed with Ayoub and the model owner.
- [ ] Repetitions/seeds recorded if applicable.
- [ ] Analysis tested on the example CSV.
- [ ] No performance claim made until real simulation results are analyzed.
