# References

The entries below are limited to bibliographic or URL information found in project files. Incomplete metadata is marked accordingly rather than inferred.

## Research Papers Used by the Team

- **Borg: The Next Generation.** The repository bibliography records year 2020 and DOI `10.1145/3342195.3387517` under key `Tirmazi2020`. Full author/title metadata should be verified before formal citation.
- **TON_IoT Telemetry Dataset.** The repository bibliography records year 2020 and DOI `10.1109/ACCESS.2020.3022862` under key `Alsaedi2020`. Full author/title metadata should be verified before formal citation.
- **CICIoT2023.** The repository bibliography records year 2023 and DOI `10.3390/s23135941` under key `PintoNeto2023`. Full author/title metadata should be verified before formal citation.
- **Bot-IoT Dataset.** The repository bibliography records year 2019 and DOI `10.1016/j.future.2019.05.041` under key `Koroniotis2019`. Full author/title metadata should be verified before formal citation.
- **UNSW-NB15.** The repository bibliography records year 2015 and DOI `10.1109/MilCIS.2015.7348942` under key `Moustafa2015`. Full author/title metadata should be verified before formal citation.

These sources are research/dataset references in the wider project documentation. They were not used to produce the integration measurements in `04_Results/`.

## iFogSim / iFogSim2 Software

- **iFogSim repository.** Cloudslab iFogSim, source repository: https://github.com/Cloudslab/iFogSim
- The experiment uses an external local iFogSim source tree. The repository's `LICENSE_STATUS.md` states that iFogSim has its own license and is not vendored or modified here. Verify the upstream license before redistribution.

## Dataset Sources

- **Image Recognition Task Execution Times in Mobile Edge Computing.** UCI Machine Learning Repository dataset 859: https://archive.ics.uci.edu/dataset/859/image+recognition+task+execution+times+in+mobile+edge+computing
- Dataset archive URL recorded by the project: https://archive.ics.uci.edu/static/public/859/image+recognition+task+execution+times+in+mobile+edge+computing.zip
- DOI recorded by the project: https://doi.org/10.24432/C5N617
- License link recorded by the project: https://creativecommons.org/licenses/by/4.0/legalcode

The project audit reports 4,000 execution-time records across four files and describes the UCI data as calibration/reference data. It does not contain Local/Edge/Cloud action labels, deadlines, bandwidth, energy, or resource-utilization fields. It is not a complete offloading-decision dataset and was not used to fabricate the simulator measurements here.

## Other Implementation Documentation

- Project objective and intended research scope: `project_objective.md`, `docs/research-overview.md`.
- Candidate state/action/reward design: `docs/state-action-reward.md`; thresholds and weights are provisional.
- Planned evaluation methodology: `docs/experiment-plan.md`; it is not evidence that those future experiments were run.
- Current integration contract and measurement evidence: `audit_output/integration_prototype/MEASUREMENT_CONTRACT_V1.md` and `FINAL_STATUS.md`.

## Verification Note

The project files contain additional dataset links and abbreviated bibliography entries. They are not expanded here unless their identifying details were explicit in the inspected files. No paper title, author list, or DOI has been invented.
