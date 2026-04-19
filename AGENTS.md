# AGENTS.md

This repository is a local, batch-first MLOps demo for NYC TLC yellow taxi trip-duration prediction.

The goal is to demonstrate a credible end-to-end lifecycle:

`dataset version -> feature set version -> train/evaluate -> register/promote -> score -> monitor`

## Review guidelines

- Treat broken or missing dataset lineage as `P1`.
- Treat missing or incorrect feature-set metadata as `P1`.
- Treat model registration without explicit evaluation-gate evidence as `P1`.
- Treat prediction batches without monitoring artifacts or report links as `P1`.
- Verify schema or contract changes update tests and metadata handling together.
- Keep changes batch-first unless the task explicitly asks for online serving.
- Do not introduce Feast, Kubernetes, or cloud deployment complexity unless the issue explicitly requires it.
- Prefer small, explicit metadata contracts over hidden or inferred lineage.
- Prefer deterministic, rerunnable pipeline code over notebook-only behavior.
- Flag logging of unnecessary sensitive fields or raw identifiers as `P1`.
- Keep scope minimal and avoid unrelated refactors.

## Repo-specific expectations

- The canonical demo problem is NYC TLC yellow taxi trip-duration prediction.
- The default model family for v1 is XGBoost.
- The default local stack is `Parquet + DuckDB + Prefect + MLflow + Streamlit`.
- Batch scoring is the primary inference path for v1.
- The local catalogs are:
  - `DatasetVersion`
  - `FeatureSetVersion`
  - `ModelVersion`
  - `PredictionBatch`

## Priority heuristics

- `P0`: catastrophic data loss, broken scoring outputs, or a registry/promotion path that can silently mark a bad model as approved.
- `P1`: broken lineage, missing gate evidence, invalid metadata contracts, broken monitoring attachment, or incorrect core training/scoring behavior.
- Lower-priority issues should only be flagged if they materially hurt the demo or make the workflow misleading.
