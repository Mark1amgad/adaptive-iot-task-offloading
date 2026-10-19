# Dataset Description

## Provenance

The complete copied tree is under `Original/` and preserves the source files from `team-work/Mostafa/Dataset/`. The project audit identifies the UCI Image Recognition Task Execution Times in Mobile Edge Computing dataset as the directly relevant reference source:

- UCI page: https://archive.ics.uci.edu/dataset/859/image+recognition+task+execution+times+in+mobile+edge+computing
- Dataset DOI recorded by the project: https://doi.org/10.24432/C5N617
- License link recorded by the project: https://creativecommons.org/licenses/by/4.0/legalcode

The tree also contains EUA location/user tables and research metadata/comparison files. The current integration does not use these datasets to generate decisions or measurements.

## Original Tabular Files

The copied CSV/TSV inventory contains 10 files:

| File group | Files | Rows and columns | Columns / units |
| --- | --- | --- | --- |
| EUA site | `01_EUA/raw/site-optus-melbCBD.csv` | 125 × 10 | Site identifiers, coordinates, names, state, postcode, elevation, and related metadata; units are source-defined |
| EUA users | `01_EUA/raw/users-aus.csv` | 4,748 × 7 | IP, Latitude, Longitude, PostCode, City, State, Country; coordinates are source fields |
| EUA generated users | `01_EUA/raw/users-melbcbd-generated.csv` | 816 × 2 | Latitude, Longitude; units are source coordinates |
| UCI image recognition | `08_UCI_Image_Recognition_MEC/raw/uci_extracted/final/TATDescriptionDataset/*.csv` | 4 files × 1,000 × 2 | `Time`, `Execution Time`; project audit reports execution time in seconds |

The four UCI filenames are `MacBookPro1.csv`, `MacBookPro2.csv`, `RasberryPi.csv`, and `VM.csv`. They contain no Local/Edge/Cloud action labels, task size, deadline, bandwidth, energy, or utilization fields.

## Quality and Statistics

Run `Dataset_Statistics/generate_statistics.py` to regenerate:

- `dataset_file_statistics.csv`: rows, columns, names, missing cells, duplicate rows, and numeric columns.
- `numeric_column_statistics.csv`: count, mean, median, min, max, and IQR-rule outlier count for fully numeric columns.

The generated statistics are descriptive checks of the copied source files. They do not transform the data or create offloading labels. The project audit reports the four UCI CSVs have 1,000 rows each, no missing values, and no duplicate rows; the generated files provide the reproducible local check.

## Use and Limitations

These files are reference/calibration material, not the source of the accepted Local/Edge/Cloud simulation measurements. The UCI data record image-recognition execution/turnaround times on named server environments and cannot be treated as a complete learned offloading dataset. EUA files provide location/context data, not task outcomes or action labels. No dataset value is presented as a measured result of the iFogSim experiment.