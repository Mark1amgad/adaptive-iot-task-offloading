# References and Source Notes

The authoritative paper collection and classification are in [`research/references/`](../../research/references/), with its [reference index](../../research/references/REFERENCES_INDEX.md). This file only records implementation and dataset-source context.

## Simulator and implementation

- iFogSim upstream source: https://github.com/Cloudslab/iFogSim
- The experiment uses an external local iFogSim source tree at the sibling `Research/iFogSim` path. Its source is not vendored into this repository.
- The Java/Python integration and its measurement limitations are documented in [Simulation Source](../10_iFogSim_Simulation/Simulation_Source/).

## Dataset sources

- UCI Image Recognition Task Execution Times in Mobile Edge Computing: https://archive.ics.uci.edu/dataset/859/image+recognition+task+execution+times+in+mobile+edge+computing
- Dataset DOI recorded by the project: https://doi.org/10.24432/C5N617
- Dataset license recorded by the project: https://creativecommons.org/licenses/by/4.0/legalcode

The dataset audit describes this UCI data as calibration/reference data. It does not provide Local/Edge/Cloud action labels, deadlines, bandwidth, energy, or resource-utilization fields, so it is not a complete offloading-decision dataset.

## Citation quality

Use the metadata in the canonical reference index and verify author/title/venue details before formal publication. Incomplete bibliography fields must remain marked as incomplete rather than inferred.
