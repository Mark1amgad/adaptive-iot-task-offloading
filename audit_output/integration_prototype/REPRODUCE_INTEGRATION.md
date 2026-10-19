# Reproduce the integration

From the repository root, run:

```powershell
& .\audit_output\integration_prototype\run_acceptance.ps1
```

The runner creates a new `runs\acceptance_YYYYMMDD_HHMMSS` directory, compiles the experiment into its `classes` child, runs one real `train` session and deterministic `baseline` Local/Edge/Cloud sessions, validates every generated `java_trace.jsonl`, and writes `policy_comparison.json`. It refuses to reuse an existing output directory. Override `-PythonExe`, `-IFogSimRoot`, `-JdkHome`, or `-RunRoot` when the local installations differ.

The validator can also check the retained evidence without rerunning Java:

```powershell
& python .\audit_output\integration_prototype\validate_integration.py
```

Create a compact preliminary policy comparison from an existing run without rerunning the simulator:

```powershell
& python .\audit_output\integration_prototype\compare_policies.py `
	--root .\audit_output\integration_prototype\runs\acceptance_20261013_220748 `
	--output .\audit_output\integration_prototype\runs\acceptance_20261013_220748\policy_comparison.json
```

The comparison reports measured destination, latency, deadline flag, and task-attributed bytes for the RL train trace and deterministic Local/Edge/Cloud references. It is a one-task integration comparison, not evidence of model superiority or a statistically independent RL evaluation.

The validator requires exactly one decision, execution, terminal, outcome acknowledgement, shutdown acknowledgement, and clean process exit per trace. It recomputes link bytes from transfer rows and checks Local/Edge/Cloud totals of 0/14,000/28,000 bytes. Train additionally requires a saved model and an updated outcome; baselines must not save or update.

The current Java experiment is deliberately one-task only. A multi-task count is not exposed: the registry, terminal shutdown, and per-task transfer hooks would need a task map and coordinated final shutdown before multiple tasks could be measured without cross-task attribution errors.

Run the focused error and terminal-condition cases in a new isolated directory with:

```powershell
& .\audit_output\integration_prototype\run_acceptance.ps1 -RunErrorTests
```

This adds `--fault timeout` and `--fault malformed` adapter-boundary tests. The fault is injected before the observation is sent, so the RL service has no pending task and can acknowledge shutdown with `orphaned_tasks=0`; fallback still executes on Edge and sends no outcome. It also runs `--deadline-ms 0`, where the measured terminal latency is evaluated against the configured zero deadline and the normal completed outcome carries `deadline_met=false`.