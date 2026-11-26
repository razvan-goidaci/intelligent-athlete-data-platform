# intelligent-athlete-data-platform
Intelligent data platform for data quality analysis, anomaly detection, and athlete performance insights using heterogeneous and time-series data.

This is a bachelor thesis project, using a personal Garmin export as its case study. The export is personal health data and is not included in this repository.

**Status:** source-data reconnaissance is complete, and the Bronze layer is being built.

## Setup

Developed with Python 3.14. PySpark and Delta Lake also need Java 17.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Code layout

```text
src/
├── bronze/   the pipeline's Bronze layer: raw export to Delta tables
└── recon/    finished investigations behind docs/recon.md, kept to reproduce its results
```

Place the export at `data/raw/GarminExport.zip`, then run scripts from the repository root, for example `.venv/bin/python src/bronze/extract_files.py`.

### Bronze

| Script | Purpose | Output |
|---|---|---|
| `src/bronze/extract_files.py` | Extracts the export, including nested ZIPs, into `data/raw/<extension>/` | Raw files by type |
| `src/bronze/fit_to_rows.py` | Turns one FIT file into Bronze rows per table, with lineage columns | Used by `load_fit.py` |
| `src/bronze/load_fit.py` | Loads FIT rows into Delta tables (in progress) | `data/bronze/<table>/` |

### Reconnaissance

| Script | Purpose | Output |
|---|---|---|
| `src/recon/inventory.py` | Counts raw files and records JSON structure | `data/processed/inventory/` |
| `src/recon/reconnaissance.py` | Records FIT messages, FIT fields and JSON structure | `data/processed/reconnaissance/` |
| `src/recon/profile_retained_dataset.py` | Profiles the fields of the retained FIT and JSON sources | `data/processed/profiling/` |
| `src/recon/verify_activity_coverage.py` | Compares the JSON activity list with the FIT files and finds coverage gaps | `data/processed/validation/` |
| `src/recon/verify_monitoring_timestamps.py` | Reconstructs and checks monitoring `timestamp_16` values | `data/processed/validation/` |
| `src/recon/check_sdk_message_counts.py` | Checks that Garmin's FIT SDK finds the same messages as `fitparse` | Printed counts |

## Documentation

- [Reconnaissance findings](docs/recon.md)
- [Data dictionary](docs/data_dictionary.md)
- [Bronze layer design](docs/bronze_design.md)
