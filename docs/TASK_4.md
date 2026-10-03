# Task 4 — Deterministic fault injection

Status: implemented on `feature/task-4-fault-injection`, awaiting review and merge into `feature/develop`.

## Objectives

Engineering: apply reproducible data defects to a run-scoped workspace, retain exact mutation evidence, validate the corrupted copy, and reset it without changing the real pipeline output.

Learning: investigate why a technically successful pipeline can still contain missing, duplicate, null or incorrectly calculated data, and identify which quality rule exposes each defect.

## Delivered behavior

- Four allowlisted scenarios select the lowest `order_id`: `missing_order`, `duplicate_order`, `null_net_amount` and `wrong_net_amount` (`+ 0.01`).
- Apply copies both Target datasets into `fault_workspace` and mutates the copy in one transaction.
- `metadata.fault_runs` retains scenario, lifecycle, before/after evidence and linked validation run.
- A pipeline run can have only one active fault; the database also enforces this invariant.
- The fault suite reuses count, uniqueness, null and reconciliation checks against the workspace.
- The original Target is never changed, and unrelated pipeline runs are never copied, mutated or reset.
- Reset is idempotent. Reapplying the same scenario to the same deterministic run selects the same key and produces the same evidence.

## Commands

Existing databases must initialize once to create the workspace and metadata table:

```text
python -m backend.app.main db-init
python -m backend.app.main fault-list
python -m backend.app.main fault-apply wrong_net_amount --run-id <pipeline UUID>
python -m backend.app.main fault-quality-run --fault-run-id <fault UUID>
python -m backend.app.main fault-inspect --fault-run-id <fault UUID>
python -m backend.app.main fault-reset --fault-run-id <fault UUID>
python -m backend.app.main quality-run --run-id <pipeline UUID>
```

Expected lifecycle: fault validation is `FAIL`, the pipeline's execution remains `SUCCESS`, reset succeeds, and the normal quality suite returns `PASS` on the unchanged Target.

## Limitations

Task 4 is local and single-user. Scenarios operate only on the built-in orders pipeline and one fault may be active per pipeline run. It does not expose arbitrary mutation SQL, an API, a UI or multi-user concurrency controls.
