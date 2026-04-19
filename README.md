# mlops-tlc-demo

Local batch-first MLOps demo for NYC TLC trip-duration prediction with XGBoost, MLflow, Prefect, and Streamlit.

## Current Focus

The repository is being built issue by issue. The first implementation slices establish:

- Python project skeleton
- metadata contracts
- SQLite-backed metadata store
- baseline tests
- official NYC TLC raw monthly ingest for yellow taxi parquet files

## Local Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -e '.[dev]'
python3 -m pytest
python3 -m ruff check .
```

## Initial Repo Layout

```text
src/mlops_tlc_demo/
  config.py
  contracts.py
  ingestion/
    tlc.py
  metadata_schema.sql
  metadata_store.py
tests/
  test_contracts.py
  test_metadata_store.py
  test_tlc_ingest.py
dev_plans/
  issue-2-bootstrap-contracts.md
  issue-3-ingest-raw-tlc.md
```

## Local Metadata Entities

- `DatasetVersion`
- `FeatureSetVersion`
- `ModelVersion`
- `PredictionBatch`

These form the repo-local metadata control plane that later issues will build on for ingest, feature generation, training, scoring, and monitoring.

## Raw TLC Ingest

To ingest a raw yellow taxi month from the official TLC monthly source:

```bash
. .venv/bin/activate
python -m mlops_tlc_demo.ingestion.tlc --month 2026-02
```

The raw artifact is stored under `data/raw/yellow/YYYY-MM/data.parquet`, and the corresponding raw `DatasetVersion` is registered in the local SQLite metadata store.
