# Task 11 proposal — Microsoft cloud data QA foundations

Status: proposed; implementation awaits review of this plan. The user's approval
of Task 10 authorizes its merge and preparation of this next plan, not deployment
or provisioning of cloud services.

Task 10 was approved and merged through PR #12 into feature/develop at
6799950642e2a3b621826268dfe10a7f8ff06aa0. The Task 11 branch is
feature/task-11-cloud-qa, created from that exact merge. Main remains unchanged.

## Objectives and outcome

Engineering: extend the existing course platform with auditable cloud evidence,
bounded imports and repeatable local simulations, retaining personal history,
progress, restricted SQL and the 22 existing lessons.

Learning: trace cloud pipelines from run/activity evidence to Source/Target data;
prove completeness, schema, partitions, freshness and replay correctness rather
than trusting a successful job or matching row counts.

Recommended core delivery: eight ENG/VIE lessons in three courses, increasing the
catalog to 30 lessons. All core lessons must work with the current local Docker
setup and require no cloud account. Existing Fabric, ADF and OneLake subject
pages become real course pages with chapters, prerequisites and personal progress.

## Core implementation, after plan approval

| Part | Deliverable | Review evidence |
|---|---|---|
| 11.1 Evidence runtime | Versioned run/activity, file manifest and data snapshot contracts; session-owned simulator and JSON/CSV importer | Validated provenance, bounded files/rows/bytes, ownership and independent clean/fault fixtures |
| 11.2 Fabric course | Three lessons: trace run lineage; detect schema/type drift; reconcile Bronze/Silver/Gold keys and exact amounts | Actual local PostgreSQL checks and observable run-to-dataset links |
| 11.3 ADF and OneLake courses | Three ADF lessons on copy evidence, incremental watermark/replay and failed dependency/recovery; two OneLake lessons on partition completeness and stale shortcut/reference evidence | Persisted simulation actions, independent data defects, explicit UTC/as-of boundaries |
| 11.4 UI and release | Evidence viewer, import validation feedback, bilingual instructions/hints/solutions, challenge flow, course progress and Docker packaging | Browser completion of all eight lessons; regression of all 22 existing lessons; account isolation and restart retention |

Each lesson follows instruction, guided practice, observable evidence, challenge,
submission, explanation and resume. Submissions require checks that accept clean
data and detect independent fault cases. Written answers remain saved, not
automatically semantically graded; reveal alone does not award completion.

Suggested lesson inventory (catalog IDs assigned during implementation):

1. Fabric: trace run IDs and dataset lineage across pipeline layers.
2. Fabric: detect a schema/type contract change before publication.
3. Fabric: reconcile keys and exact amounts across Bronze/Silver/Gold snapshots.
4. ADF: compare activity copy metrics with actual Source/Target keys.
5. ADF: prove watermark boundaries and replay idempotency with late arrivals.
6. ADF: investigate failed dependencies and verify recovery publication.
7. OneLake: identify missing, unexpected and duplicate partition/file evidence.
8. OneLake: check a referenced dataset's freshness using a fixed as-of clock.

## Evidence and simulation design

Represent datasets by explicit grain, schema, business keys, UTC timestamps and
exact decimal amounts. Run metadata includes provider, workspace/factory/item
identifiers, run/activity IDs, execution state, time bounds and source references.
Normalized fields retain their original raw evidence and mapping version; a
missing provider field is UNKNOWN, not a fabricated zero or success.

Display provenance prominently as SIMULATED or IMPORTED. A local simulator is
not a Microsoft service emulator. Lakehouse data snapshots use bounded CSV/JSON
loaded into isolated PostgreSQL tables; this scope does not run Spark, implement
Delta/Iceberg transaction engines or claim real OneLake shortcut resolution.

Use ordinary file inputs, strict versions and size/row limits. Do not extract ZIP
archives, accept arbitrary server paths/URLs, execute imported code, fetch links
from evidence or treat imported conclusions as grading truth. Derive expected
contracts independently. Imports carry account/session ownership and capture
time. No credentials are requested or retained by the core learning workflow.

Faults are named and repeatable: missing/unexpected keys, equal-count swaps,
schema drift, wrong amounts, skipped partitions, duplicate replay, late records,
stale references and failed/partial publication. Session actions never modify
another learner's tables. SQL remains read-only and bounded. Execution, quality
and incomplete evidence remain distinct.

## Separate live-cloud stage (11.5)

Actual adapters are a separate proposed checkpoint after the core is reviewed
and an environment is specified. They are not required for completion of 11.1–11.4.
Do not mark a live adapter verified using only mocks or imported JSON.

The first recommended live pilot reads Fabric job-instance metadata and imports
preselected Source/Target snapshots. Expand to ADF monitoring and OneLake reads
only after confirming tenant/subscription IDs, resource scopes, required read
permissions, auth method and acceptable data/cost bounds. No resource creation,
pipeline start/cancel or write operation is included in the pilot. Keep raw
provider execution states distinct from quality evidence.

Before implementing live access, record the selected sandbox, operator-owned
credential delivery and retention approach, permissions, connectivity, fixture
datasets, calls/bytes/timeout limits and observed live acceptance tests. Missing
credentials or permission means NOT_VERIFIED or ERROR, never data-quality FAIL.
The UI may offer LIVE only for a configured, verified adapter; no mock-live label.

Databricks, Synapse and broader Azure courses are a following curriculum phase,
with their own plan and task branches. This is the proposed breakdown of the
broader cloud roadmap, subject to user review.

## Exit criteria and model

- Eight new runnable bilingual lessons, independent clean/fault grading, retained
  query/evidence/submission history and separate progress for all six active courses.
- Unit and real PostgreSQL tests for import boundaries, independent defect counts,
  session/account isolation, permissions, unknown evidence and migration retention.
- Browser tests for every new lesson, ENG/VIE, imports, challenge/reveal, drafts,
  mobile layout and correct history routes; existing 22-lesson regression retained.
- Docker startup/restart and source ZIP verified; Windows review remains under
  D:\Data-QA-Lab and preserves the existing PostgreSQL data.
- Observed results recorded on the final PR head. Merge only after user review.

Recommended model: retain GPT-6.1 Sol High. It matches the combined backend,
grading, UI and regression work. High is an engineering recommendation, not a
guarantee; escalate reasoning only for a specific unresolved architecture or
authentication issue rather than changing models for the whole task.

## Official references checked on 2026-10-05

- [OneLake overview and ADLS Gen2 compatibility](https://learn.microsoft.com/en-us/fabric/onelake/onelake-overview)
- [ADF copy activity monitoring and output metrics](https://learn.microsoft.com/en-us/azure/data-factory/copy-activity-monitoring)
- [Fabric list item job instances, scopes and continuation](https://learn.microsoft.com/en-us/rest/api/fabric/core/job-scheduler/list-item-job-instances)
- [GPT-6.1 Sol model guidance and reasoning settings](https://developers.openai.com/api/docs/guides/latest-model?model=gpt-6.1-sol)
