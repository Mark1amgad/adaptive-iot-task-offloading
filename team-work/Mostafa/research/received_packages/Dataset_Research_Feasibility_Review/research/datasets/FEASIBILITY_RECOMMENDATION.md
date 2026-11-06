# Dataset Research & Feasibility Assessment — recommendation (NOT final approval)

## Recommendation

**Do not select either ECW or SMD as a complete task-offloading training/test dataset.** Both are credible auxiliary real-world telemetry sources with fundamentally different semantics. The available sources do **not** provide a linked table of task arrivals, input bytes, CPU cycles, deadlines, per-option network/queue states, decisions and actual completion outcomes.

1. **Use measured traces only where they actually measure a variable.** ECW can describe temporal variation of normalized edge upload workload and server static descriptors; SMD can describe anonymized machine telemetry and true anomaly **labels** (not necessarily failures). Keep source name, released variant, timestamp granularity, authorship and normalization caveats attached.
2. **Controlled task-level simulation appears necessary** for the current draft of deadline-feasible contextual offloading. If approved, generate task arrival/input size/CPU cycles/deadlines and topology/link/resource configurations from explicitly justified ranges; obtain response outcomes by running a validated simulator, not by assigning guessed labels. Use replayed traces only through a documented, physically meaningful calibration process. This is a recommendation for later experiment design **not authorization to generate files now**.
3. **Do not row-merge ECW and SMD.** No shared node IDs or timelines. A scenario may separately combine calibrated *distributions*, but that does not produce genuine paired measurements. Report “hybrid real-trace-informed simulation”, with a column-level lineage map: `measured / derived with method / configured / generated / simulator-observed outcome`.
4. **Outcome measurement must be audited.** The current `Methodology.md` records latency as simulation time; one-task runs and `energy=null` are insufficient for broad claims about multi-task queue behavior or energy. Multi-task, multi-seed, multiple topology/network scenarios and consistent deadline-miss denominators must be agreed and verified before final comparisons.
5. **Select no final dataset yet.** The supervisor must approve the research question, RL/bandit framing, performance metrics, simulator behavior and candidate provenance mappings. Abdo is responsible for inspecting ECW/SMD raw schemas and data quality; this report does **not** duplicate his inspection or prescribe preprocessing.

## Feature gaps remaining

Task-level input size, CPU cycles, arrival timestamps, deadlines, optional DAG, destination availability/placement choices, true per-task network and queue measurements, observed completion and per-task energy **are not jointly available**. Every missing feature must be independently simulated/experimentally observed or excluded from model objectives. **Not Reported** is used for absent publisher metadata; **Not available** is used when a specified public trace lacks a task-level field.

## Acceptance gates / unresolved questions

- Confirm final research objective and whether partial/dependent tasks are in scope; otherwise do not invent dependencies.
- Confirm if Local, Edge, Cloud are all executable in validated code, and whether queue time/capacity dynamic measurements can be logged without double counting.
- Obtain permission and applicable dataset licenses for ECW and SMD; verify precise versions and native timestamps/scaling.
- Verify whether authors of CORE-01 can provide the derived SMD failure-intensity construction and simulated task-outcome data.
- Resolve team responsibilities: Mostafa = literature provenance/feasibility; Abdo = raw-file inspection/schema/duplicates/missingness; supervisor = final dataset and method approval.
- Define a reproducibility card for every eventual scenario (origin, version/hash, units, scenario config, generated variables, seeds, simulator version, experiment baseline/metric definitions). No preprocessing or dataset construction in this delivery.
