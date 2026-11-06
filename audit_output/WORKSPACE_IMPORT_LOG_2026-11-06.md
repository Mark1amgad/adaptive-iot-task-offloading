# Workspace Import and Cleanup Record — 6 November 2026

## Canonicalized Research-folder material

The following external Research-folder content was hash-verified against files already present in the repository and its canonical locations:

- `References/`: all 17 files matched canonical research references.
- `Research_Gap_Download_v29/`: both files matched Mark's research-gap package.
- `rl_model/`: model files matched the canonical Python package; the unique toy prototype was retained under Ayoub's legacy archive. Bytecode was excluded.
- `ifogsim_research_topology_gui/`: all three files matched Ayoub's topology deliverables.
- `_staging_review/overlay/`: all 135 files matched existing Abdo package material.
- `_staging_review/marks/`: all 12 files matched existing handoff/staging records.

Those external duplicate folders were removed only after matching. The external `Research/iFogSim/` directory remains because the current simulation runner uses it as a local upstream dependency.

## Simulator package preservation

- Ayoub's original received simulator ZIP packages remain under `team-work/Ayoub/archives/`.
- The extracted iFogSim-main-rl snapshot was compared by SHA-256 against the three original iFogSim-main-rl ZIP versions: 715 of 717 non-empty entries were already present in the original archives.
- The only two unique files were Eclipse `.classpath` and `.project` metadata; those files were extracted to `team-work/Ayoub/archives/source-workspaces/project-metadata/`. The redundant 14.7 MB snapshot was removed.
- The external extracted `iFogSim-main-rl/` and Eclipse workspace folders were removed. The base `Research/iFogSim/` tree remains external as a required runtime dependency.

## Repository reduction

- Removed placeholder-only planned directories: `shared/`, `experiments/`, `results/`, `integration/`, `rl-agent/`, and `simulator/`.
- Replaced scattered legacy planning Markdown with a short current architecture note and concise root indexes.
- Removed exact duplicate member/audit/dataset Markdown copies only after SHA-256 equality checks. No exact duplicate Markdown files remain.
- Removed 670 generated Java class/Python bytecode files, zero-byte placeholders, old retry runs, and demo-only logs/artifacts.
- Consolidated integration source/runner/validator under `deliverables/10_iFogSim_Simulation/Simulation_Source/`; results analysis utilities are under `deliverables/04_Results/`.
- Removed duplicate copies of Omar's all-in-one archive and nested ZIP files from the extracted package; the original outer archive remains under `team-work/Omar/archives/` and extracted result files remain.
- Removed Ayoub's `Reference.zip` after all six embedded PDFs matched canonical research-reference copies.
- Moved unrelated GitHub GUI tools and Mark's Computer Networks presentation outside the research repository to `Research/_outside_project_material/`.

## Git safety

No commit, push, reset, checkout, or staging was performed. Existing working-tree changes were preserved; review the Git diff before committing.
