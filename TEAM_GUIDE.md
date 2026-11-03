# Team Guide

## Working rule

Use the named folder under `team-work/` for personal drafts and handover
material. Use `shared/` for material that the whole team needs. Use the existing
`deliverables/`, `experiments/`, and implementation directories for their
current technical purposes.

## Member workspaces

| Member | Workspace | Primary responsibility |
| --- | --- | --- |
| Mark | `team-work/Mark/` | Research coordination, objective, final analysis |
| Omar | `team-work/Omar/` | Literature extraction |
| Mostafa | `team-work/Mostafa/` | Dataset research and collection |
| Abdo | `team-work/Astta-Abdo/` | Dataset engineering and benchmark dataset |
| Ayoub | `team-work/Ayoub/` | Model development and experiments |

Each workspace contains `drafts/`, `research/`, `datasets/`, `deliverables/`,
and `notes/`. Existing legacy files stay in place until their classification is
reviewed.

## Status workflow

1. Put new work in the appropriate personal `drafts/` or workstream folder.
2. Add a short note with Owner, Status, Last Updated, Related Paper, Related
   Dataset, and Dependencies.
3. Request review through a pull request and link the relevant task in
   `TASK_TRACKER.md`.
4. Mark the item `Under Review` while feedback is pending.
5. After agreement, place the approved shared document in the appropriate
   `shared/` folder and mark it `Approved`.

## Shared research

- Approved 2025-2026 journal references belong in `shared/Research/Approved_Papers/`
  only after their source and metadata are checked.
- Conference and comparison references belong in `shared/Research/Comparison_Papers/`.
- Omar's structured extractions belong in `shared/Research/Paper_Extractions/`.
- Dataset inventories, schemas, and provenance belong in `shared/Datasets/`.
- Do not duplicate raw datasets merely to make them visible. Link to the
  authoritative copy and record its checksum.

## Reviews and safety

Use feature branches and pull requests. Shared protocol, dataset inventory,
experiment configuration, and final-report changes require a second reviewer.
Never commit secrets, credentials, generated build output, or unverified
research claims. Do not edit the existing executable source directories as part
of repository organization work.
