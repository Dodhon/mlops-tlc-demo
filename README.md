# mlops-tlc-demo

Local batch-first MLOps demo for NYC TLC trip-duration prediction with XGBoost, MLflow, Prefect, and Streamlit.

## Current Focus

The repository is being built issue by issue. The first implementation slice establishes the local control-plane foundation:

- Python project skeleton
- metadata contracts
- SQLite-backed metadata store
- baseline tests

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
  metadata_schema.sql
  metadata_store.py
tests/
  test_contracts.py
  test_metadata_store.py
dev_plans/
  issue-2-bootstrap-contracts.md
```

## Local Metadata Entities

- `DatasetVersion`
- `FeatureSetVersion`
- `ModelVersion`
- `PredictionBatch`

These form the repo-local metadata control plane that later issues will build on for ingest, feature generation, training, scoring, and monitoring.
