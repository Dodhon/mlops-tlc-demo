# Issue 3 Ingest Raw NYC TLC Yellow Taxi Data

Plan level: L1
Status: Implemented on branch; awaiting review
Working branch: `codex/issue-3-ingest-raw-tlc`
Merge target: `main`
PR URL: `https://github.com/Dodhon/mlops-tlc-demo/pull/13`
Merge commit: TBD
Domains: backend, data, github
Skill hooks: `$github-cli-workflow`
Hook rationale:
- `$github-cli-workflow`: issue `#3` is being executed through the repo's GitHub issue/branch/PR workflow and needs a tracked draft PR.

## Executive Summary

Objective: implement recurring ingest for official NYC TLC yellow taxi monthly parquet files and register each ingested month as a raw `DatasetVersion` artifact in the local metadata store.

Recommendation: use the confirmed TLC monthly parquet URL pattern, store raw data under a predictable repo-local path, compute row count and schema hash with `duckdb`, and block silent duplicates unless the caller explicitly requests replacement. This keeps the ingest narrow, deterministic, and directly useful for later cleaning and feature-generation issues.

Ask: approve the first data dependency (`duckdb`) for this repo because it provides the simplest local parquet inspection path for row counts, schema extraction, and test fixture generation.

## End-user Context

The immediate user is the repo owner building a local MLOps demo. They need a reliable monthly raw-data ingestion path so downstream work can assume versioned raw artifacts, stable metadata, and repeatable input semantics.

## Requirements

- `R1` Download a target yellow taxi parquet month from the official TLC monthly source.
- `R2` Save the raw file under a stable versioned artifact path in the repo-local data layout.
- `R3` Register a raw `DatasetVersion` record with source URI, artifact path, schema hash, row count, and created timestamp.
- `R4` Prevent duplicate raw registrations unless the caller explicitly requests replacement behavior.
- `R5` Add automated validation for URL generation, duplicate handling, and metadata registration behavior without depending on live network in the test suite.

## Non-goals

- Cleaning rules or quality remediation.
- Feature engineering.
- Train/validation split.
- Model training or MLflow wiring.
- Multi-dataset support beyond yellow taxi files.

## Success Metrics

- The repo can ingest at least one live month from the official TLC source.
- The raw artifact lands at a predictable path such as `data/raw/yellow/YYYY-MM/data.parquet`.
- The metadata store reflects the ingested month with the expected stage, row count, and schema hash.
- Re-running the same month without `replace=True` fails explicitly instead of mutating state silently.
- The automated test suite remains offline and deterministic.

## Current Repo State

- Existing foundation from issue `#2`:
  - [pyproject.toml](/Users/thuptenwangpo/Documents/GitHub/wt-issue-3-ingest-raw-tlc/pyproject.toml)
  - [src/mlops_tlc_demo/config.py](/Users/thuptenwangpo/Documents/GitHub/wt-issue-3-ingest-raw-tlc/src/mlops_tlc_demo/config.py)
  - [src/mlops_tlc_demo/contracts.py](/Users/thuptenwangpo/Documents/GitHub/wt-issue-3-ingest-raw-tlc/src/mlops_tlc_demo/contracts.py)
  - [src/mlops_tlc_demo/metadata_store.py](/Users/thuptenwangpo/Documents/GitHub/wt-issue-3-ingest-raw-tlc/src/mlops_tlc_demo/metadata_store.py)
  - [tests/test_contracts.py](/Users/thuptenwangpo/Documents/GitHub/wt-issue-3-ingest-raw-tlc/tests/test_contracts.py)
  - [tests/test_metadata_store.py](/Users/thuptenwangpo/Documents/GitHub/wt-issue-3-ingest-raw-tlc/tests/test_metadata_store.py)
- Current limitations:
  - No ingestion module exists.
  - No data directories are created yet beyond path helpers.
  - No parquet dependency exists for schema/row-count introspection.

### Plan Lifecycle Status + Delivery Tracking

- Issue: [#3](https://github.com/Dodhon/mlops-tlc-demo/issues/3)
- Branch: `codex/issue-3-ingest-raw-tlc`
- PR URL: TBD after plan push
- Evidence pointers:
  - `. .venv/bin/activate && python -m pytest` -> pass
  - `. .venv/bin/activate && python -m ruff check .` -> pass
  - `. .venv/bin/activate && python -m mlops_tlc_demo.ingestion.tlc --month 2026-02 --replace` -> pass

### Code Style & Quality Bar References

- Repo-local governance:
  - [AGENTS.md](/Users/thuptenwangpo/Documents/GitHub/wt-issue-3-ingest-raw-tlc/AGENTS.md)
- Relevant quality expectations from `AGENTS.md`:
  - broken dataset lineage is `P1`
  - deterministic, rerunnable pipeline code is preferred
  - scope should stay batch-first and minimal

## Architecture / System Impact Diagram

```text
+-----------------------------+
| TLC monthly source URL      |
| yellow_tripdata_YYYY-MM     |
+-------------+---------------+
              |
              v
+-----------------------------+
| ingest module               |
| - build URL                 |
| - download parquet          |
| - inspect schema + rows     |
| - register DatasetVersion   |
+-------------+---------------+
              |
              v
+-----------------------------+
| repo-local artifact store   |
| data/raw/yellow/YYYY-MM/... |
+-------------+---------------+
              |
              v
+-----------------------------+
| SQLite metadata store       |
| dataset_versions            |
+-----------------------------+
```

## Assumptions and Constraints

### Assumptions

- The TLC monthly yellow taxi file naming pattern remains `yellow_tripdata_YYYY-MM.parquet`.
- It is acceptable for issue `#3` to add `duckdb` as a runtime dependency.
- The repo can store at least one live monthly parquet file locally for development.

### Constraints

- Runtime/environment: local macOS development, Python 3.12 virtual environment.
- Budget/cost: no paid infrastructure.
- Tooling/dependency: keep new dependencies low; prefer one multipurpose parquet tool over several narrow ones.
- Timeline: implement one reliable source path rather than generalized dataset plugins.

### Feasibility Matrix

| Option | Constraint fit | Dependencies | Risks | Fallback | Validation signal | Confidence |
| --- | --- | --- | --- | --- | --- | --- |
| `urllib` + `duckdb` | High | `duckdb` | one new runtime dep | use manual URL override if pattern changes | live file fetch + schema/row count inspection | High |
| `requests` + `pyarrow` | Medium | `requests`, `pyarrow` | heavier dependency surface than needed | swap to duckdb later | works, but adds more weight now | Medium |
| manual URL input only, no generated pattern | Medium | none/duckdb | more user friction and weaker recurring-ingest story | add pattern later | technically works but weakens demo | Low |

Recommended option: `urllib` + `duckdb`.

## Work Breakdown

- `E1` Add the ingestion module and raw-path conventions.
  - Maps to: `R1`, `R2`
- `E2` Add parquet inspection helpers for schema hash and row count.
  - Maps to: `R3`
- `E3` Implement metadata registration and duplicate-protection behavior.
  - Maps to: `R3`, `R4`
- `E4` Add offline tests using a generated local parquet fixture.
  - Maps to: `R5`
- `E5` Run one live ingest against an official TLC month and capture evidence.
  - Maps to: `R1`, `R2`, `R3`

## Validation Plan

- `V1` (`R1`, `R2`): generated TLC source URL resolves to a real file and downloads successfully.
- `V2` (`R3`): row count and schema hash are computed and persisted into `DatasetVersion`.
- `V3` (`R4`): duplicate ingest without replacement fails explicitly.
- `V4` (`R5`): automated tests pass without network access by using a local parquet fixture.
- `V5` (`R1-R3`): one live month is present locally and visible through metadata lookup.

## Issue / PR Test Suite

Preconditions:
- Create `.venv` using Python 3.12, not the machine-default Python 3.14.
- Install the updated project dependencies.

Commands to run in this PR:
- `. .venv/bin/activate && python -m pytest`
- `. .venv/bin/activate && python -m ruff check .`
- `. .venv/bin/activate && python -m mlops_tlc_demo.ingestion.tlc --month 2026-02 --replace`

Failure policy:
- Any contract/metadata registration failure blocks completion.
- Any duplicate-behavior mismatch blocks completion.
- Live ingest failure blocks completion unless the official source is unavailable and the failure is confirmed to be external.

## Risks and Mitigations

- Risk: the TLC file pattern changes.
  - Mitigation: keep an explicit `source_url` override in the ingest entrypoint.
- Risk: network-based tests become flaky.
  - Mitigation: keep the test suite offline and run only one manual/live ingest as execution evidence.
- Risk: first data dependency adds avoidable weight.
  - Mitigation: use only `duckdb`, which is already aligned with the planned stack.

## Top 10 Reader Questions

1. Why ingest only yellow taxi data?
   - Because v1 needs one stable source, not generalized dataset support.
2. Why not use pandas?
   - It adds more weight than needed for file download plus schema/row-count inspection.
3. Why `duckdb` now?
   - It is the cleanest local parquet tool and is already part of the intended stack.
4. Why store the raw file locally instead of streaming every time?
   - Because later issues need persistent, versioned raw artifacts.
5. Why schema hash at raw stage?
   - To detect upstream structural changes before cleaning or feature generation.
6. Why block duplicates?
   - Silent overwrite would break dataset lineage.
7. Why keep tests offline?
   - To keep CI and local validation deterministic.
8. Why not add quality validation here?
   - That belongs to issue `#4`.
9. Why not register a quality report path now?
   - Raw ingest should mark quality as `pending`; validation is a later concern.
10. Is one live month enough?
   - Yes for issue `#3`; recurrence is proven by the month-parameterized path and CLI.

## Open Questions

- Should the live proof month be `2026-01` or `2026-02` in the docs/examples?
- Should the CLI entrypoint default to `replace=False` with a separate explicit flag for replacement?
- Should the metadata layer expose list/query helpers now, or wait until the UI issue?

## Core PR vs Optional Follow-ups

### Core PR

- add `duckdb` dependency
- add ingestion module and CLI entrypoint
- add metadata registration and duplicate checks
- add tests
- run one live ingest and capture evidence

### Optional Follow-ups

- support green taxi or FHV datasets
- add dataset-list query helpers
- add checksum of full file bytes in addition to schema hash

## Recommendation

Proceed with a yellow-taxi-only ingest implementation using `duckdb` for parquet inspection and keep all non-source-specific behavior narrow and explicit.

## Next Steps

1. Commit this plan on the issue branch.
2. Extend the local `br` graph for issue `#3`.
3. Open the draft PR.
4. Implement `E1-E5`.

## Ready for Execution

- [ ] Scope is limited to raw yellow taxi ingest and metadata registration.
- [ ] Lineage-sensitive duplicate behavior is explicit.
- [ ] The first data dependency is justified and limited to `duckdb`.
- [ ] Offline automated tests cover the ingest logic without live network.
- [ ] One live ingest proof is part of the issue evidence bundle.
