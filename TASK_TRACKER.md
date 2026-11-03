# Task Tracker

Repository organization was completed on 2026-11-03. The research workstream
starts on 2026-11-04 with collection and verification of the agreed full-text
papers. Statuses below describe the handoff at the end of the organization
phase; they do not imply that research tasks have already been completed.

Statuses: `Not Started`, `In Progress`, `Under Review`, `Approved`, and
`Blocked`. Update this table through a pull request.

| Task | Owner | Status | Deliverable Location | Dependencies | Last Updated |
| --- | --- | --- | --- | --- | --- |
| Retrieve and verify the agreed full-text journal papers and the ICC 2026 comparison paper | Omar (Mark reviews the corpus) | Not Started | `team-work/Omar/research/` and `shared/Research/Approved_Papers/` / `Comparison_Papers/` | Confirmed reference list and metadata | 2026-11-03 |
| Extract each paper's model, formulation, experiments, numerical results, datasets, and limitations with page/section citations | Omar | Not Started | `team-work/Omar/deliverables/` and `shared/Research/Paper_Extractions/` | Verified full-text papers | 2026-11-03 |
| Inventory datasets and data sources actually used by the selected papers, including older datasets | Mostafa | Not Started | `team-work/Mostafa/deliverables/` and `shared/Datasets/Dataset_Inventory/` | Full-text papers and source/license checks | 2026-11-03 |
| Validate, clean, and harmonize selected data; document schema, units, missing fields, and provenance | Abdo | Blocked | `team-work/Astta-Abdo/deliverables/` and `shared/Datasets/Processed_Data/` | Mostafa's inventory, approved objective, and schema | 2026-11-03 |
| Finalize the real-world use case, research objective, formulation, contributions, and evaluation metrics | Mark | Not Started | `team-work/Mark/deliverables/` and `shared/Project_Documentation/Research_Objective/` | Core paper extraction and comparison with the ICC 2026 paper | 2026-11-03 |
| Approve the canonical simulator/model protocol and measurement semantics | Mark, Ayoub | Blocked | `docs/decisions/` and `shared/Project_Documentation/Decisions/` | Objective, state/action/reward, units, and failure/deadline semantics | 2026-11-03 |
| Integrate the approved benchmark and run controlled experiments with baselines, multiple seeds, logs, and checkpoints | Ayoub | Blocked | `team-work/Ayoub/deliverables/`, `experiments/`, and `results/` | Approved objective, protocol, metrics, and benchmark dataset | 2026-11-03 |

## Experiment gate

Ayoub must not start final comparative experiments until Mark has approved
the research objective and metrics, and the team has approved the protocol and
benchmark dataset. Existing prototype work may be inspected, but provisional
configurations must not be presented as final research results.

The dates above record the organization-phase handoff, not dates on which
research findings were produced.
