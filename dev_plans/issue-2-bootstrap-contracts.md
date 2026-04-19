# Issue 2 Bootstrap Contracts and Metadata Store

Plan level: L1
Status: Draft
Working branch: `codex/issue-2-bootstrap-contracts`
Merge target: `main`
PR URL: TBD
Merge commit: TBD
Domains: backend, data, github
Skill hooks: `$github-cli-workflow`
Hook rationale:
- `$github-cli-workflow`: issue `#2` is being executed through the repo's issue/branch/PR workflow and needs PR hygiene.

## Executive Summary

Objective: bootstrap the repository so all later MLOps work sits on explicit metadata contracts and a lightweight local control plane instead of ad hoc files. This change will add the initial Python project structure, define the four canonical metadata entities, create a SQLite-backed metadata layer, and add baseline tests and developer setup guidance.

Recommendation: keep the implementation intentionally small and local-first. Use `pydantic` for metadata contracts, the standard-library `sqlite3` module for the metadata store, `pytest` for automated validation, and a minimal `pyproject.toml` so later issues can layer data, MLflow, Prefect, and Streamlit on top without reworking the foundation.

Ask: approve this as the core issue `#2` implementation scope and treat follow-on tooling such as MLflow, Prefect, and UI as later issues rather than part of this bootstrap PR.

## End-user Context

The immediate user is the repo owner building and demoing a local XGBoost-first MLOps system. The practical need is a trustworthy foundation for dataset, feature set, model, and prediction batch lineage before data ingest, training, or orchestration work begins.

## Requirements

- `R1` Define explicit code-level contracts for `DatasetVersion`, `FeatureSetVersion`, `ModelVersion`, and `PredictionBatch`.
- `R2` Create a local metadata store with a stable schema that can persist and read each contract type.
- `R3` Establish a Python project layout that later issues can extend without structural churn.
- `R4` Add baseline automated validation for contracts and metadata persistence behavior.
- `R5` Document the local developer setup and repo structure clearly enough that later issues can build on it consistently.

## Non-goals

- Implement NYC TLC ingestion.
- Implement cleaning, feature engineering, training, scoring, or monitoring logic.
- Add MLflow, Prefect, Streamlit, or cloud deployment wiring.
- Design a generalized metadata platform beyond this repo's four contract types.

## Success Metrics

- A developer can create and retrieve each of the four metadata entities locally.
- The repo has a reproducible Python entrypoint and test workflow.
- The metadata schema is explicit enough that later issues do not need to redefine the contract surface.
- Tests cover the contract and metadata-store happy path plus at least one invalid-input failure per contract family.

## Current Repo State

- Root files:
  - [README.md](/Users/thuptenwangpo/Documents/GitHub/wt-issue-2-bootstrap-contracts/README.md)
  - [AGENTS.md](/Users/thuptenwangpo/Documents/GitHub/wt-issue-2-bootstrap-contracts/AGENTS.md)
- Current state observations:
  - The repo currently contains no Python packaging files, no source tree, no tests, and no metadata schema.
  - The repo-level `AGENTS.md` already sets the quality bar: broken lineage, missing evaluation evidence, and missing monitoring links are `P1` defects.

### Plan Lifecycle Status + Delivery Tracking

- Issue: [#2](https://github.com/Dodhon/mlops-tlc-demo/issues/2)
- Branch: `codex/issue-2-bootstrap-contracts`
- PR URL: TBD after plan commit/push
- Evidence pointers: to be populated with `pytest` and lint output in this PR

### Code Style & Quality Bar References

- Repo-local governance:
  - [AGENTS.md](/Users/thuptenwangpo/Documents/GitHub/wt-issue-2-bootstrap-contracts/AGENTS.md)
- Resulting quality bar for this issue:
  - contracts must be explicit rather than inferred
  - deterministic, rerunnable code is preferred over hidden state
  - unrelated refactors are out of scope
  - metadata and tests must evolve together

## Architecture / System Impact Diagram

```text
+-------------------------------+
| Python package                |
| mlops_tlc_demo                |
| - contracts                   |
| - metadata store              |
| - config                      |
+---------------+---------------+
                |
                v
+-------------------------------+
| SQLite metadata DB            |
| dataset_versions              |
| feature_set_versions          |
| model_versions                |
| prediction_batches            |
+-------------------------------+
                ^
                |
+-------------------------------+
| Tests                         |
| - contract validation         |
| - persistence round-trips     |
+-------------------------------+
```

## Assumptions and Constraints

### Assumptions

- Python 3.12+ is acceptable for local development.
- Later issues will introduce third-party runtime services, but issue `#2` should remain standalone and local.
- A single SQLite file is sufficient for the metadata control plane in v1.

### Constraints

- Runtime/environment: local macOS development in a Git worktree.
- Budget/cost: near-zero; no paid cloud services for this issue.
- Security/compliance: avoid logging unnecessary sensitive/raw identifiers into metadata examples.
- Tooling/dependency: keep dependency count low; prefer standard library where reasonable.
- Timeline: this issue should unblock later implementation, not become a platform rewrite.

### Feasibility Matrix

| Option | Constraint fit | Dependencies | Risks | Fallback | Validation signal | Confidence |
| --- | --- | --- | --- | --- | --- | --- |
| `pydantic` contracts + `sqlite3` store | High | `pydantic`, `pytest`, optional `ruff` | Slightly more setup than dataclasses | Can fall back to dataclasses later if needed | contract parsing + DB round-trip tests | High |
| `dataclasses` + `sqlite3` only | High | `pytest` | weaker validation at boundaries, more manual checks | add pydantic later | tests would need more hand-written validation | Medium |
| ORM-heavy bootstrap (`sqlmodel`/`sqlalchemy`) | Medium | larger dependency set | overbuilds issue `#2` and raises churn risk | revert to raw sqlite layer | slower first PR, more structure to change later | Low |

Recommended option: `pydantic` contracts + `sqlite3` store.

## Work Breakdown

- `E1` Create the Python project skeleton and package layout.
  - Maps to: `R3`, `R5`
- `E2` Define the four metadata contract models in code.
  - Maps to: `R1`
- `E3` Create the SQLite schema and a minimal metadata access layer.
  - Maps to: `R2`
- `E4` Add developer-facing config and README updates for local setup.
  - Maps to: `R5`
- `E5` Add automated tests for contract validation and metadata-store persistence.
  - Maps to: `R4`

## Validation Plan

- `V1` (`R3`, `R5`): package imports cleanly from the repo checkout.
  - Pass signal: module import and test discovery succeed.
- `V2` (`R1`): contract models reject invalid payloads and accept valid payloads.
  - Pass signal: automated contract tests pass.
- `V3` (`R2`): metadata round-trip persistence works for all four entity types.
  - Pass signal: automated DB tests pass against a temp SQLite database.
- `V4` (`R5`): README/setup guidance matches the actual commands introduced in this PR.
  - Pass signal: setup commands run successfully in the worktree.

## Issue / PR Test Suite

Pre-change repo commands:
- No repo-native validation commands exist yet.

Post-change commands to be added in this PR:
- `python3 -m pytest`
- `python3 -m ruff check .`

If `ruff` is introduced but not wired through `python3 -m ruff`, update this section in the PR to the exact installed command.

### Testing Execution Protocol

Preconditions:
- Run from the active worktree root.
- Install dependencies from the new project config before running validation.

Run order:
1. dependency install command introduced by this PR
2. `python3 -m pytest`
3. `python3 -m ruff check .`

Failure policy:
- `pytest` failure blocks completion.
- schema/contract failure blocks completion.
- lint failure blocks completion unless the lint command itself is missing and is explicitly marked as a follow-up gap in the PR.

Evidence bundle:
- exact command output captured in the final implementation note / PR summary

## Risks and Mitigations

- Risk: the metadata schema is too vague and later issues need to rewrite it.
  - Mitigation: keep fields explicit and tied to the four known control-plane entities only.
- Risk: introducing too much framework structure too early.
  - Mitigation: avoid ORMs and service wiring in this issue.
- Risk: tests become stale as contracts evolve.
  - Mitigation: couple tests directly to the initial contract models and DB access layer.

## Top 10 Reader Questions

1. Why bootstrap metadata first?
   - Because lineage and evaluation evidence are core repo quality requirements.
2. Why not wait for MLflow to own all metadata?
   - MLflow will only own part of the story later; datasets and prediction batches still need repo-local control-plane records.
3. Why SQLite?
   - It is local, deterministic, simple, and enough for a single-user demo.
4. Why `pydantic`?
   - It gives explicit boundary validation with less hand-written boilerplate than plain dataclasses.
5. Why not add Feast now?
   - This issue needs a feature catalog contract, not a feature-serving platform.
6. Why not add Prefect now?
   - Orchestration should wrap working scripts, not precede them.
7. Why not add MLflow now?
   - Training and registry belong to later issues and would blur the bootstrap scope.
8. Will this lock us into one schema?
   - It sets the v1 schema, but in a small enough surface that later changes are tractable.
9. What if later issues need more fields?
   - Additive schema evolution is fine; the risk is only if we under-specify the core entities now.
10. Is this enough to open a draft PR?
   - Yes; this issue is explicitly foundational and should be visible early.

## Open Questions

- Should the repo use `uv` explicitly for dependency management, or keep the initial docs package-manager-agnostic with `pip` commands?
- Should timestamps be stored as ISO strings at the contract layer or normalized to Python `datetime` objects before persistence?
- Should the metadata access layer expose only CRUD primitives now, or also query helpers for catalog views?

## Core PR vs Optional Follow-ups

### Core PR

- `pyproject.toml`
- package skeleton under `src/`
- contract models
- SQLite schema + minimal store layer
- tests
- README/bootstrap updates

### Optional Follow-ups

- add repository-wide pre-commit hooks
- add a dedicated CI workflow for lint/test
- add richer query helpers for catalog listing/search

## Recommendation

Proceed with a narrow bootstrap PR that establishes the Python package, contract models, SQLite metadata store, and tests. Do not mix in data ingest or MLflow setup yet.

## Next Steps

1. Commit this plan on the issue branch.
2. Create the local `br` graph artifacts for the execution tasks.
3. Open the draft PR linked to issue `#2`.
4. Implement `E1-E5`.

## Ready for Execution

- [ ] Scope is limited to issue `#2` and excludes ingest/training/orchestration.
- [ ] Contract entities are explicitly defined in code before later issues build on them.
- [ ] Style references from repo `AGENTS.md` are acknowledged and mapped to validation.
- [ ] Automated tests for changed stateful logic (metadata persistence) are included in core scope.
- [ ] Validation commands are concrete and will be updated to exact repo commands in this PR.
- [ ] Rollback is straightforward: revert the bootstrap files and remove the metadata DB artifacts if created locally.
