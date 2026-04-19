# Issue 4 Cleaning and Data-Quality Validation

Plan level: L1
Status: Implemented on branch; awaiting review
Working branch: `codex/issue-4-cleaning-quality`
Merge target: `main`
PR URL: `https://github.com/Dodhon/mlops-tlc-demo/pull/14`
Merge commit: TBD
Domains: backend, data, github
Skill hooks: `$github-cli-workflow`
Hook rationale:
- `$github-cli-workflow`: issue `#4` is being executed through the repo's issue/branch/PR workflow and needs a tracked draft PR.

## Executive Summary

Objective: turn raw NYC TLC yellow taxi parquet data into a clean, validated dataset artifact with a machine-readable quality report and explicit lineage back to the raw input dataset.

Recommendation: implement a deterministic raw-to-clean pipeline in one `clean_tlc.py` module that:

- loads the raw dataset version from the metadata store
- validates the required source schema
- filters impossible or obviously broken rows
- writes a clean parquet artifact
- emits a JSON quality report
- registers a clean `DatasetVersion` that includes an `upstream_dataset_id` reference to the raw dataset

The only contract extension required is adding `upstream_dataset_id` to `DatasetVersion` and the SQLite schema, because issue `#4` explicitly needs clean dataset registration to carry its parent raw dataset reference.

## End-user Context

The immediate user is the repo owner building a trustworthy MLOps demo. They need a clean, reproducible dataset artifact that downstream feature generation can depend on without rebuilding ad hoc validation logic.

## Requirements

- `R1` Implement a reproducible raw-to-clean pipeline for a month of raw yellow taxi data.
- `R2` Validate the presence of required raw columns and fail loudly on schema mismatch.
- `R3` Apply explicit cleaning rules for impossible or broken rows.
- `R4` Write a machine-readable quality report to a stable artifact path.
- `R5` Register a clean `DatasetVersion` with a lineage reference back to the raw dataset.
- `R6` Cover representative broken-row behavior and schema-failure behavior with automated tests.

## Non-goals

- Feature engineering.
- Model evaluation or registry work.
- UI work.
- General-purpose data quality framework design.

## Success Metrics

- A clean dataset artifact is produced at a predictable path for a target month.
- The clean dataset row count is lower than or equal to the raw row count and traceable to the raw parent.
- A quality report exists and records removal counts by reason.
- Broken schema or catastrophic data loss stops the pipeline.
- Automated tests cover both row filtering and schema failure cases.

## Current Repo State

- Existing ingest foundation from issue `#3`:
  - [src/mlops_tlc_demo/ingestion/tlc.py](/Users/thuptenwangpo/Documents/GitHub/wt-issue-4-cleaning-quality/src/mlops_tlc_demo/ingestion/tlc.py)
  - [tests/test_tlc_ingest.py](/Users/thuptenwangpo/Documents/GitHub/wt-issue-4-cleaning-quality/tests/test_tlc_ingest.py)
- Existing metadata foundation from issue `#2`:
  - [src/mlops_tlc_demo/contracts.py](/Users/thuptenwangpo/Documents/GitHub/wt-issue-4-cleaning-quality/src/mlops_tlc_demo/contracts.py)
  - [src/mlops_tlc_demo/metadata_schema.sql](/Users/thuptenwangpo/Documents/GitHub/wt-issue-4-cleaning-quality/src/mlops_tlc_demo/metadata_schema.sql)
  - [src/mlops_tlc_demo/metadata_store.py](/Users/thuptenwangpo/Documents/GitHub/wt-issue-4-cleaning-quality/src/mlops_tlc_demo/metadata_store.py)
- Important repo state implication:
  - the current `DatasetVersion` contract does not yet carry parent lineage, so issue `#4` must extend that contract intentionally.

### Plan Lifecycle Status + Delivery Tracking

- Issue: [#4](https://github.com/Dodhon/mlops-tlc-demo/issues/4)
- Branch: `codex/issue-4-cleaning-quality`
- PR URL: TBD
- Evidence pointers:
  - `. .venv/bin/activate && python -m pytest` -> pass
  - `. .venv/bin/activate && python -m ruff check .` -> pass
  - `. .venv/bin/activate && python -m mlops_tlc_demo.ingestion.tlc --month 2026-02 --replace` -> pass
  - `. .venv/bin/activate && python -m mlops_tlc_demo.data_prep.clean_tlc --month 2026-02 --replace` -> pass

### Code Style & Quality Bar References

- Repo-local governance:
  - [AGENTS.md](/Users/thuptenwangpo/Documents/GitHub/wt-issue-4-cleaning-quality/AGENTS.md)
- Relevant quality expectations:
  - broken dataset lineage is `P1`
  - metadata and tests must evolve together
  - deterministic pipeline behavior is preferred over hidden state

## Architecture / System Impact Diagram

```text
+-----------------------------+
| Raw DatasetVersion          |
| stage=raw                   |
| artifact_path -> parquet    |
+-------------+---------------+
              |
              v
+-----------------------------+
| clean_tlc pipeline          |
| - schema validation         |
| - row filtering             |
| - quality summary           |
+-------------+---------------+
              |                     \
              v                      v
+-----------------------------+   +-----------------------------+
| clean parquet artifact      |   | JSON quality report         |
| data/clean/yellow/YYYY-MM   |   | artifacts/data_quality/...  |
+-------------+---------------+   +-------------+---------------+
              \                      /
               v                    v
               +--------------------+
               | Clean DatasetVersion|
               | upstream_dataset_id |
               +--------------------+
```

## Assumptions and Constraints

### Assumptions

- Issue `#3` raw ingest is already available for the month being cleaned.
- It is acceptable to extend the dataset contract/schema in this issue.
- The cleaning rules can remain conservative and batch-oriented rather than fully domain-optimized.

### Constraints

- Runtime/environment: local Python 3.12 virtual environment.
- Budget/cost: local-only.
- Tooling/dependency: reuse `duckdb`; do not add a second dataframe stack if unnecessary.
- Timeline: keep cleaning logic narrow and explicit.

### Feasibility Matrix

| Option | Constraint fit | Dependencies | Risks | Fallback | Validation signal | Confidence |
| --- | --- | --- | --- | --- | --- | --- |
| `duckdb` SQL-based cleaning + JSON report | High | existing `duckdb` | SQL rule changes need care | revise thresholds in code/tests | deterministic filter counts + parquet output | High |
| pandas-based cleaning | Medium | pandas | extra dependency surface | switch back to duckdb | works but heavier than needed | Medium |
| manual ad hoc Python row iteration | Low | none extra | slower, noisier, less aligned with later stack | rewrite to SQL later | weak long-term fit | Low |

Recommended option: `duckdb` SQL-based cleaning.

## Work Breakdown

- `E1` Extend `DatasetVersion` and the metadata schema with `upstream_dataset_id`.
  - Maps to: `R5`
- `E2` Implement schema validation and cleaning rules for raw TLC data.
  - Maps to: `R1`, `R2`, `R3`
- `E3` Emit quality report artifacts and register the clean dataset metadata.
  - Maps to: `R4`, `R5`
- `E4` Add automated tests for representative bad rows and schema failure.
  - Maps to: `R6`
- `E5` Run one live clean pass using the locally ingested raw month and capture evidence.
  - Maps to: `R1-R5`

## Validation Plan

- `V1` (`R5`): metadata contract/schema can persist a dataset with `upstream_dataset_id`.
- `V2` (`R2`, `R3`): cleaning removes expected bad rows from a local fixture dataset.
- `V3` (`R2`): missing required columns raise a schema error.
- `V4` (`R4`, `R5`): quality report artifact and clean dataset metadata are both written.
- `V5` (`R1-R5`): one live month from local raw ingest can be cleaned successfully.

## Issue / PR Test Suite

Preconditions:
- Create `.venv` using Python 3.12.
- Install dependencies from `pyproject.toml`.
- Ensure a raw month exists locally for the live validation step.

Commands to run in this PR:
- `. .venv/bin/activate && python -m pytest`
- `. .venv/bin/activate && python -m ruff check .`
- `. .venv/bin/activate && python -m mlops_tlc_demo.data_prep.clean_tlc --month 2026-02 --replace`

Failure policy:
- Any schema-contract mismatch blocks completion.
- Any quality-report generation failure blocks completion.
- Live clean failure blocks completion unless the raw input artifact is missing due to an external/local setup problem that is explicitly identified.

## Risks and Mitigations

- Risk: cleaning thresholds are too aggressive and drop too much data.
  - Mitigation: emit removal counts and fail on catastrophic loss.
- Risk: lineage is lost between raw and clean datasets.
  - Mitigation: extend `DatasetVersion` with explicit `upstream_dataset_id`.
- Risk: schema evolution in TLC data breaks the cleaning path.
  - Mitigation: required-column validation with a loud failure path.

## Top 10 Reader Questions

1. Why extend `DatasetVersion` now?
   - Because issue `#4` explicitly requires parent dataset lineage.
2. Why not store lineage only in the quality report?
   - Because lineage belongs in the metadata control plane, not only in an artifact sidecar.
3. Why SQL-based cleaning?
   - It fits the planned stack and keeps the rules easy to inspect.
4. What counts as a catastrophic anomaly?
   - Missing required schema or a near-empty clean dataset after filtering.
5. Why generate a JSON report?
   - So later issues can consume it programmatically.
6. Why not normalize every field now?
   - That is feature-pipeline work and belongs mostly to issue `#5`.
7. Why allow warnings?
   - Some months may have meaningful row loss without being invalid.
8. Why not add Great Expectations or another quality framework?
   - That is overbuild for this stage.
9. Does cleaning derive the target column?
   - Not necessarily for v1; the issue is about trustable clean data first.
10. Is one live clean proof enough?
   - Yes for issue `#4`; it proves the raw-to-clean path works on real data.

## Open Questions

- What exact threshold should separate `passed` from `warning` on row removal fraction?
- Should `trip_duration_minutes` be derived in this issue or deferred to feature engineering?
- Should quality report paths be grouped by month only or also by dataset stage/version?

## Core PR vs Optional Follow-ups

### Core PR

- contract/schema extension for upstream lineage
- cleaning pipeline module and CLI
- JSON quality report generation
- tests
- one live clean run

### Optional Follow-ups

- richer quality heuristics
- additional report summary helpers
- more detailed anomaly slices by vendor or location

## Recommendation

Proceed with a conservative, SQL-based cleaning pass that preserves lineage explicitly and produces machine-readable quality evidence for later stages.

## Next Steps

1. Commit this plan on the issue branch.
2. Extend the local `br` graph for issue `#4`.
3. Open the draft PR.
4. Implement `E1-E5`.

## Ready for Execution

- [ ] `DatasetVersion` contract extension is treated as part of the scoped change, not a side effect.
- [ ] Cleaning rules are explicit and deterministic.
- [ ] A quality report artifact is part of the normal pipeline output.
- [ ] Automated tests cover both filtering behavior and schema failure.
- [ ] One live clean proof is part of the issue evidence bundle.
