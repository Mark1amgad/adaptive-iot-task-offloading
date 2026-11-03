# Workspace Audit Report

Audit date: 2026-11-03

## Executive summary

The main Git repository is `adaptive-iot-task-offloading`. The external workspace also contains `References/`, iFogSim source trees, archives, team documents, and other research materials. The repository already contains working code, simulator evidence, datasets, reports, and team workspaces. Those existing areas were preserved.

This audit added a canonical `research/` library and copied the 14 external PDFs plus three research DOCX files into documented destinations. A second review added the unique Research Gap v29 records, the proposed methodology draft, bilingual simulator technical audits, and missing RL design documentation. No original external file was deleted, moved, or overwritten. No source code, simulator tree, configuration, experiment output, Git metadata, branch, remote, or unrelated uncommitted change was modified.

## Git safety baseline

Before reorganization, `git status --short --branch` reported:

```text
## main...origin/main
 M team-work/Astta-Abdo/adaptive_offloading/adaptive_offloading.py
 M team-work/Astta-Abdo/adaptive_offloading/test.py
```

These pre-existing changes were not touched. The final status must be checked after this report is committed to the working tree; no staging or commit was performed.

## Workspace structure observed

### External workspace

- `References/`: 14 PDFs and 3 DOCX research documents.
- `adaptive-iot-task-offloading/`: the main Git repository and canonical project source.
- `iFogSim/`, `iFogSim-main-rl/`, and `eclipse-workspace/`: simulator/development workspaces kept outside the documentation reorganization.
- `rl_model/`, `Research_Gap_Download_v29/`, and related archives: external working materials preserved in place.
- Root-level DOCX files: simulator audit and methodology planning documents preserved in place.
- Root-level ZIP files: archives preserved in place and not unpacked or deleted.

### Repository

- `shared/`: shared research, datasets, project documentation, and final deliverables.
- `deliverables/`: numbered overview, methodology, source code, results, references, reproduction, limitations, RL model, datasets, and iFogSim simulation material.
- `docs/`: research design and team documentation.
- `team-work/`: member-owned workspaces. The two pre-existing Astta-Abdo edits remain untouched.
- `audit_output/`: prior audit and integration evidence.
- `experiments/`, `results/`, `integration/`, `rl-agent/`, and `simulator/`: implementation and experiment areas preserved as existing sources of truth.
- `research/`: new canonical research-library index and classified reference copies.

## Complete inventory

The complete hash-backed inventory is [research/WORKSPACE_FILE_INVENTORY.csv](research/WORKSPACE_FILE_INVENTORY.csv). It includes repository and external-workspace records while excluding only Git internals and known dependency/generated directories: `.git/`, `node_modules/`, Python cache directories, `jars/`, simulator `output/`, `topology-gui-classes/`, and virtual environments. These exclusions avoid reading build/dependency internals that are not research records; their existence is noted by the workspace structure above.

The inventory records relative path, scope, extension, byte length, and SHA-256. Scope values are `repository`, `external-references`, and `external-workspace`.

## Classification findings

### References

- **Core journal papers:** 6 local full texts, all verified from PDF text/metadata as 2025 or 2026 journal papers from IEEE or ScienceDirect and directly relevant to task offloading, reliability, uncertainty, or device-edge-cloud execution.
- **Supporting literature:** 2 local full texts: one IEEE Access survey and one IEEE Internet of Things Magazine article.
- **Conference papers:** 5 local full texts, including the required IEEE ICC 2026 chance-constrained paper.
- **Excluded archive:** 0. No paper was silently discarded; relevant conference material was retained in the conference category, and uncertain material was retained as unverified.
- **Unverified/incomplete:** 1 CAV taxonomy/review PDF whose local metadata does not establish venue, DOI, or publication type.
- **Pending core full text:** two agreed papers are absent: “Distributed Optimization of Task Offloading and Resource Allocation for Mobile Edge Computing With Multifactorial Uncertainty” (IEEE Transactions on Mobile Computing, 2026, DOI `10.1109/TMC.2025.3603064`) and “Adaptive Task Offloading and Resource Allocation for Tasks With Time-Varying Statistical Characteristics in MEC Systems” (IEEE Internet of Things Journal, 2026; DOI not verified locally). Neither is counted as a local paper.

Detailed stable IDs, DOI values, local paths, reasons, and pending records are in [research/references/REFERENCES_INDEX.md](research/references/REFERENCES_INDEX.md).

### Existing repository materials already correctly organized

- Shared literature concepts: `shared/Research/Approved_Papers/`, `shared/Research/Comparison_Papers/`, `shared/Research/Literature_Review/`, and `shared/Research/Paper_Extractions/`.
- Dataset sources and provenance: `shared/Datasets/` and `deliverables/09_Datasets/Original/`.
- Methodology and architecture: `docs/`, `deliverables/02_Methodology/`, and `shared/Project_Documentation/`.
- Experiments and evidence: `experiments/`, `results/`, `deliverables/04_Results/`, and `audit_output/`.
- Simulator and model implementation: `deliverables/08_RL_Model/`, `deliverables/10_iFogSim_Simulation/`, `integration/`, and the team workspaces.

These were indexed rather than duplicated into `research/`.

## Destination map

| Source material | Repository destination | Action |
| --- | --- | --- |
| Six verified core PDFs | `research/references/01_Core_Journal_Papers/` | Copied; source preserved |
| Two supporting PDFs | `research/references/02_Supporting_Literature/` | Copied; source preserved |
| Five conference PDFs | `research/references/03_Conference_Papers/` | Copied; source preserved |
| One uncertain CAV review PDF | `research/references/05_Unverified_or_Incomplete/` | Copied; source preserved |
| Literature review DOCX | `research/literature_review/paper_extractions/` | Copied; source preserved |
| Rebuilt links DOCX | `research/literature_review/comparative_analysis/` | Copied; source preserved |
| Dataset/download notes DOCX | `research/datasets/documentation/` | Copied; source preserved |
| Research Gap v29 report and matrix | `research/literature_review/research_gaps/` | Copied; source and ZIP archive preserved |
| Proposed methodology and experimental plan | `deliverables/02_Methodology/` | Copied as draft; source preserved |
| Bilingual Member 3 simulator technical audit | `audit_output/` | Copied as audit evidence; sources preserved |
| RL documentation absent from canonical package | `deliverables/08_RL_Model/docs/` | Copied; executable package was already equivalent |
| Existing repository datasets | Existing `shared/Datasets/` and `deliverables/09_Datasets/Original/` | Not moved |
| Existing code, simulator files, configurations, results, and team work | Existing project locations | Not moved |

No files were moved. The operation used copies because the external workspace must remain recoverable and the repository already has meaningful ownership boundaries.

## Duplicate and version findings

- No exact SHA-256 duplicates were found among the 14 PDFs and 3 DOCX files in `References/`.
- The existing `FILE_INDEX.md` records known duplicate dataset candidates in `team-work/Mostafa/Dataset/` and `deliverables/09_Datasets/Original/`; both copies remain preserved and were not consolidated.
- The HAL deposit of the IEEE ICC paper is treated as one paper version, not a second paper.
- The review DOCX bibliographic entries without matching PDFs are pending records, not duplicate papers.
- The external RL executable package is hash-equivalent to the repository package for the compared source, test, configuration, and README files; it was not copied again. Its missing design/audit documents were copied into the canonical package.
- The external `iFogSim/results/` files are DCNS/VRGame workbooks and reports, not hash-equivalent to the repository adaptive offloading evidence. They remain external because their provenance and relationship to the current study are not established well enough to make them canonical.
- No version was overwritten.

## Metadata and classification risks

- A PDF filename is not treated as authoritative. Classification used title, venue, year, DOI, article identifiers, and first-page content where available.
- CORE-06 now has the verified DOI `10.1109/TCE.2025.3611973` recorded in the reference index.
- CONF-02 has a HAL deposit and conference identifiers but no confirmed DOI in the local copy.
- UNV-01 needs independent venue, DOI, and publication-type verification.
- The review DOCX contains useful bibliographic leads, but its entries are not promoted to full-text references without a matching source.
- Publisher access, licensing, and redistribution terms should be checked before public release of copied PDFs.

## Second review: external materials and final dispositions

| Material | Evidence reviewed | Disposition | Reason |
| --- | --- | --- | --- |
| `Research_Gap_Download_v29/` | DOCX text, XLSX presence, file hashes, and matching ZIP presence | **Copied and preserved externally** | Unique research-gap report/matrix; belongs in literature-gap records. The ZIP remains a recoverable external archive. |
| `Proposed_Methodology_Experimental_Plan-1.docx` | DOCX text and hash | **Copied and preserved externally** | Unique draft methodology plan; retained as draft under the existing methodology deliverable area. |
| `Member3_iFogSim2_Simulator_Technical_Audit.docx` and English version | DOCX text, dates, technical findings, and hashes | **Copied and preserved externally** | Unique bilingual technical audit of current simulation validation; retained under audit evidence. |
| External `rl_model/rl_model` | Representative source, tests, configuration, README hashes; missing documentation list | **Executable package kept external; missing docs copied** | Code is equivalent to `deliverables/08_RL_Model/`; avoid duplicate implementation. Five missing Markdown design/audit files are now in `deliverables/08_RL_Model/docs/`. External legacy toy code remains external because it is historical code, not validated evidence. |
| `iFogSim/results/` and `iFogSim/output/` | Result filenames, sizes, external result tree, and repository evidence paths | **Kept external and documented** | DCNS/VRGame outputs and generated simulator output are not the current adaptive offloading evidence and are not hash-equivalent to repository results. No duplicate copy was made. |
| iFogSim archives | ZIP entry listings and archive presence | **Kept external and documented** | Archives contain source/build/output bundles or packaged results; preserving them is safer than unpacking parallel trees. |

The repository’s canonical current experiment evidence remains `audit_output/`, `deliverables/04_Results/`, and `deliverables/10_iFogSim_Simulation/`. External simulator workspaces remain recoverable for provenance and future reconciliation.

## Post-operation verification plan

- Confirm every classified copy exists and matches the source SHA-256.
- Confirm external source files still exist.
- Check `git diff --check`.
- Review `git status --short --branch` and verify the two original Astta-Abdo modifications remain the only pre-existing code changes, with new audit/library files shown separately.
- Search repository documentation for stale paths before final publication.

## Verification results and final Git status

- All 14 classified PDF copies exist and match their external SHA-256 values.
- All three copied DOCX research documents exist and match their external SHA-256 values.
- The second-review DOCX/XLSX copies, methodology draft, bilingual audits, and five RL documentation files exist in their documented destinations and match their external source hashes.
- Reference directory counts are 6 core, 2 supporting, 5 conference, 0 excluded, and 1 unverified.
- The external `References/` source files remain present.
- `git diff --check` completed without whitespace errors; Git emitted only normal CRLF-to-LF normalization warnings.
- No files were staged or committed.

Final working-tree status:

```text
## main...origin/main
 M FILE_INDEX.md
 M README.md
 M team-work/Astta-Abdo/adaptive_offloading/adaptive_offloading.py
 M team-work/Astta-Abdo/adaptive_offloading/test.py
?? WORKSPACE_AUDIT_REPORT.md
?? audit_output/Member3_iFogSim2_Simulator_Technical_Audit.docx
?? audit_output/Member3_iFogSim2_Simulator_Technical_Audit_EN.docx
?? deliverables/02_Methodology/Proposed_Methodology_Experimental_Plan-1.docx
?? research/
?? deliverables/08_RL_Model/docs/
```

The two `team-work/Astta-Abdo` modifications are pre-existing and unrelated to this audit. The remaining modified/untracked paths are the audit, documentation copies, and research-library deliverables created by this operation. The exact current status should be rechecked before staging or review because Git may display paths under a common directory differently.

## Deliverables

- [REFERENCES_INDEX.md](research/references/REFERENCES_INDEX.md)
- [WORKSPACE_FILE_INVENTORY.csv](research/WORKSPACE_FILE_INVENTORY.csv)
- [FILE_INDEX.md](FILE_INDEX.md)
- [README.md](README.md)
