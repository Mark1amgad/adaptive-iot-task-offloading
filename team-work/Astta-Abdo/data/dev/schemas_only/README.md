# Schema-only CSV templates

These files contain header rows only. They intentionally contain **zero records**. Populate them only from the simulator adapter / policy integration:

- `decision_contexts.csv` — decision-time candidate observations
- `decisions.csv` — policy decisions and fallback data
- `task_outcomes.csv` — measured branch events and final task outcomes
- `calibration_log.csv` — prediction/actual residual audit after simulations

The workload generator does not write to these files. Field definitions and null semantics are in `../../schemas/DATA_DICTIONARY.md` and the matching JSON Schemas.
