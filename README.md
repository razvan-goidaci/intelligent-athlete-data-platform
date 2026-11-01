# intelligent-athlete-data-platform
Intelligent data platform for data quality analysis, anomaly detection, and athlete performance insights using heterogeneous and time-series data.

This is a bachelor thesis project, using a personal Garmin export as its case study. The export is personal health data and is not included in this repository.

**Status:** source-data reconnaissance is complete. Ingestion and data modeling are next, so the repository does not yet contain a pipeline.

## Setup

Developed with Python 3.14.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Reconnaissance scripts

Place the export at `data/raw/GarminExport.zip`, then run these from the repository root:

| Script | Purpose | Output |
|---|---|---|
| `src/extract_files.py` | Extracts the export, including nested ZIPs, into `data/raw/<extension>/` | Raw files by type |
| `src/inventory.py` | Counts raw files and records JSON structure | `data/processed/inventory/` |
| `src/reconnaissance.py` | Records FIT messages, FIT fields and JSON structure | `data/processed/reconnaissance/` |
| `src/profile_retained_dataset.py` | Profiles the fields of the retained FIT and JSON sources | `data/processed/profiling/` |

## Documentation

- [Reconnaissance findings](docs/recon.md)
- [Data dictionary](docs/data_dictionary.md)
