# Results

> **Status: empty placeholders — no results exist or are claimed.**

This directory stores experiment output. It is created now so the structure exists,
but **it contains no data**, and nothing here should be interpreted as a research
finding.

## Layout

- `raw/` — raw per-run output produced by `experiments/scripts/` (CSV/JSON logs,
  per-task records keyed by `task_id`). Mostly **Git-ignored** by default (see
  `.gitignore`) to avoid committing large/local data; specific files can be added
  intentionally when needed for the report.
- `processed/` — cleaned/aggregated results and figures used in the write-up
  (tracked by Git when the team decides to include them).

## Conventions (to finalize)

- Each result should be traceable to: scenario config, policy, random seed, and the
  repository commit that produced it.
- Report central tendency and spread across repeated runs, not single runs.
- Include only metrics the simulator reliably measures.

Placeholders (`.gitkeep`) keep the empty directories in Git. Do not fabricate data
to fill these folders.
