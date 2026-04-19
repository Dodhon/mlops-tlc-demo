# Issue 5 Deterministic Trip-Duration Feature Pipeline

Plan level: L1
Status: Draft
Working branch: `codex/issue-5-feature-pipeline`
Merge target: `main`
PR URL: TBD
Merge commit: TBD
Domains: backend, data, github
Skill hooks: `$github-cli-workflow`
Hook rationale:
- `$github-cli-workflow`: issue `#5` is being executed through the repo's issue/branch/PR workflow and needs tracked PR state.

## Executive Summary

Objective: build a deterministic feature pipeline for trip-duration regression from the clean TLC dataset, persist the feature artifacts, and register a `FeatureSetVersion` pointing back to the clean dataset.

Recommendation: implement the feature pipeline in one module using `duckdb` SQL. The pipeline should:

- read the clean monthly dataset
- derive `trip_duration_minutes` explicitly as the target
- derive a stable feature row identifier
- produce a feature parquet plus reproducible train/validation split parquet files
- register a `FeatureSetVersion` with the feature list and upstream clean dataset reference

The split should be time-aware and deterministic: order by pickup timestamp and hold out the most recent 20% of rows in the month for validation.

## End-user Context

The immediate user is the repo owner building toward model training. They need a stable, reproducible feature artifact and split contract so training and evaluation do not depend on notebook logic or ad hoc dataframe manipulation.

## Requirements

- `R1` Build a reproducible feature artifact for a cleaned month.
- `R2` Define the target `trip_duration_minutes` explicitly in code.
- `R3` Derive the requested feature columns and persist them.
- `R4` Create deterministic train/validation split artifacts appropriate for time-aware monthly data.
- `R5` Register `FeatureSetVersion` metadata with explicit feature list and upstream clean dataset reference.
- `R6` Add automated tests for required-column expectations and deterministic split behavior.

## Non-goals

- Model training.
- Model evaluation contract.
- Registry/promotion logic.
- Online feature serving or Feast integration.

## Success Metrics

- A feature parquet artifact exists under a stable path for the target month.
- Train/validation split artifacts exist and are deterministic on repeated runs.
- The target definition is explicit and testable.
- The feature metadata record points back to the clean dataset and lists the feature columns.
- Automated tests cover missing-column failure and split determinism at minimum.

## Current Repo State

- Clean-data baseline now exists from issue `#4`:
  - [src/mlops_tlc_demo/data_prep/clean_tlc.py](/Users/thuptenwangpo/Documents/GitHub/wt-issue-5-feature-pipeline/src/mlops_tlc_demo/data_prep/clean_tlc.py)
  - [tests/test_clean_tlc.py](/Users/thuptenwangpo/Documents/GitHub/wt-issue-5-feature-pipeline/tests/test_clean_tlc.py)
- Feature metadata contract already exists from issue `#2`:
  - [src/mlops_tlc_demo/contracts.py](/Users/thuptenwangpo/Documents/GitHub/wt-issue-5-feature-pipeline/src/mlops_tlc_demo/contracts.py)
  - [src/mlops_tlc_demo/metadata_store.py](/Users/thuptenwangpo/Documents/GitHub/wt-issue-5-feature-pipeline/src/mlops_tlc_demo/metadata_store.py)
- Key current gap:
  - no feature-building module or split artifacts exist yet

### Plan Lifecycle Status + Delivery Tracking

- Issue: [#5](https://github.com/Dodhon/mlops-tlc-demo/issues/5)
- Branch: `codex/issue-5-feature-pipeline`
- PR URL: TBD
- Evidence pointers: to be populated with `pytest`, `ruff`, and one live feature-build run

### Code Style & Quality Bar References

- Repo-local governance:
  - [AGENTS.md](/Users/thuptenwangpo/Documents/GitHub/wt-issue-5-feature-pipeline/AGENTS.md)
- Relevant quality expectations:
  - feature-set metadata must stay explicit
  - deterministic pipeline behavior is preferred
  - avoid introducing Feast or cloud complexity in this issue

## Architecture / System Impact Diagram

```text
+------------------------------+
| Clean DatasetVersion         |
| stage=clean                  |
+-------------+----------------+
              |
              v
+------------------------------+
| feature pipeline             |
| - target derivation          |
| - feature derivation         |
| - deterministic split        |
+------+------+----------------+
       |      |
       v      v
+-----------+ +----------------+
| train.parq| | validation.parq|
+-----------+ +----------------+
       \      /
        v    v
    +----------------------+
    | FeatureSetVersion    |
    | input_dataset_id=... |
    +----------------------+
```

## Assumptions and Constraints

### Assumptions

- A clean month is already available locally and can be rebuilt if needed.
- The clean dataset retains the raw timestamp/location fields needed for feature derivation.
- A 20% tail holdout is acceptable for the first validation split.

### Constraints

- Runtime/environment: local Python 3.12 virtual environment.
- Tooling/dependency: reuse `duckdb`; avoid pandas/Feast for this issue.
- Timeline: keep the feature set narrow and aligned with the issue body.

### Feasibility Matrix

| Option | Constraint fit | Dependencies | Risks | Fallback | Validation signal | Confidence |
| --- | --- | --- | --- | --- | --- | --- |
| `duckdb` SQL-based feature build + time-ordered split | High | existing `duckdb` | SQL expressions need care | adjust expressions in one place | deterministic artifact counts and split boundary | High |
| Python row-wise transforms | Medium | none extra | noisier and less aligned with later batch paths | switch to SQL later | works but weaker long-term fit | Medium |
| full feature-store abstraction now | Low | Feast and extra config | overbuilds issue | defer | poor scope fit | Low |

Recommended option: `duckdb` SQL-based feature build and split.

## Work Breakdown

- `E1` Implement the feature-building module and artifact path conventions.
  - Maps to: `R1`, `R3`
- `E2` Derive the target and deterministic feature row identifier.
  - Maps to: `R2`, `R3`
- `E3` Implement the deterministic train/validation split.
  - Maps to: `R4`
- `E4` Register `FeatureSetVersion` metadata.
  - Maps to: `R5`
- `E5` Add automated tests and run one live feature-build proof.
  - Maps to: `R6`

## Validation Plan

- `V1` (`R1-R3`): feature parquet is created with the expected feature columns and target.
- `V2` (`R4`): train and validation parquet artifacts are produced with deterministic row counts.
- `V3` (`R5`): feature set metadata is persisted with the upstream clean dataset ID.
- `V4` (`R6`): missing required columns fail loudly in automated tests.
- `V5` (`R1-R5`): one live month can be ingested, cleaned, and featurized end to end.

## Issue / PR Test Suite

Preconditions:
- Create `.venv` using Python 3.12.
- Install dependencies from `pyproject.toml`.
- Rebuild raw and clean artifacts locally if they are absent.

Commands to run in this PR:
- `. .venv/bin/activate && python -m pytest`
- `. .venv/bin/activate && python -m ruff check .`
- `. .venv/bin/activate && python -m mlops_tlc_demo.ingestion.tlc --month 2026-02 --replace`
- `. .venv/bin/activate && python -m mlops_tlc_demo.data_prep.clean_tlc --month 2026-02 --replace`
- `. .venv/bin/activate && python -m mlops_tlc_demo.features.trip_duration --month 2026-02 --replace`

Failure policy:
- Any missing-column or target-definition mismatch blocks completion.
- Split non-determinism blocks completion.
- Live feature-build failure blocks completion unless it is traced to missing upstream raw/clean artifacts that can be rebuilt locally.

## Risks and Mitigations

- Risk: no stable entity key exists in the clean dataset.
  - Mitigation: derive a deterministic hash-based feature row ID from stable row fields.
- Risk: split logic leaks future rows into training.
  - Mitigation: use pickup timestamp ordering and a tail holdout.
- Risk: feature metadata drifts from the real artifact columns.
  - Mitigation: register the explicit feature list from the code path that writes the parquet.

## Top 10 Reader Questions

1. Why not use Feast now?
   - This issue needs a feature catalog artifact, not a feature-serving platform.
2. Why define the target here?
   - Because training needs an explicit label contract, and the issue body calls it out.
3. Why not random split?
   - A time-aware monthly dataset should not pretend time ordering doesn’t matter.
4. Why keep all logic in one module?
   - To make the first feature contract easy to inspect and test.
5. Why use a synthetic row ID?
   - Because the source data does not provide a stable trip primary key in this demo.
6. Why not engineer many more features?
   - Scope discipline; this issue only needs a useful deterministic first feature set.
7. Why store separate train/validation files?
   - So later training/evaluation steps can consume explicit artifacts, not re-split ad hoc.
8. Why keep raw/clean rebuild commands in validation?
   - Because the live proof for features depends on those upstream artifacts.
9. Why not store split metadata in the contract?
   - The issue only requires feature set metadata plus explicit split logic in code; richer split metadata can come later.
10. Is one live month enough?
   - Yes for this issue; the month parameterized CLI proves recurrence.

## Open Questions

- Should `trip_duration_minutes` be integer minutes or fractional minutes?
- Should the holdout be exact 20% by ordered row count or a date-based cutoff?
- Should the feature row ID use a hash of raw columns or an ordered row number after stable sorting?

## Core PR vs Optional Follow-ups

### Core PR

- feature-building module and CLI
- target derivation
- deterministic train/validation split
- feature set registration
- tests
- one live feature-build proof

### Optional Follow-ups

- split manifest artifact
- additional temporal or fare-based derived features
- typed feature manifest docs

## Recommendation

Proceed with a narrow, SQL-based feature pipeline that builds one well-defined feature set and makes the train/validation split explicit and reproducible.

## Next Steps

1. Commit this plan on the issue branch.
2. Extend the local `br` graph for issue `#5`.
3. Open the draft PR.
4. Implement `E1-E5`.

## Ready for Execution

- [ ] The feature set remains catalog-only; no feature store is introduced.
- [ ] The target and split logic are explicit in code.
- [ ] Deterministic split behavior is covered by automated tests.
- [ ] One live feature-build run is part of the issue evidence bundle.
