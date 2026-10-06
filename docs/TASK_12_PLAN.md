# Task 12 — approved cloud foundations

Approved scope 12.1–12.4, 2026-10-06. Base: reviewed Task 11 merge
34064470c681816e5ea72e03a82cecabb57dbfb8. Branch:
feature/task-12-cloud-foundations. No merge, main changes or next task.

Engineering objective: six runnable bilingual lessons using isolated PostgreSQL,
read-only bounded SQL, deterministic independent contracts and retained accounts.
Learning objective: prove classification, version updates, fact/dimension mapping,
reporting grain, file routing and completeness; distinguish access errors from
data defects and missing evidence.

1. Databricks classification: accepted/rejected/quarantined routing, lost rows,
   wrong classification, duplicate publication.
2. Databricks versions: reconcile before/incoming/after using explicit versions;
   stale overwrite, replay duplicates and unintended deletion, without watermarks.
3. Synapse publication: staging/fact keys and dimension lookup mapping.
4. Synapse reporting: daily/region grain, independent exact totals, JOIN fanout.
5. Azure manifest: file keys, paths and routing against required files.
6. Azure access: denied, unknown identity/scope, missing observations and valid
   evidence. Never an authorization emulator or a data-quality verdict.

Reuse existing SQL roles/allowlists, 100 output rows, 2s statement limit and
watchdog. No new dependency or learner DB reset. Foundation JSON uses a distinct
typed envelope with explicit lesson/contract identity, UTC context and checkpoint
claims; expected tables are local built-in contracts, never imported truth.
Keep 48KiB file / 64KiB request, 100 rows/dataset, 400 rows total, 101 runs,
100 steps and eight imports. Missing context stays unknown; local mutation
revisions invalidate checks. Old Task 11 files and sessions stay compatible.

Check current official vendor references and record precise simulation limits.
Targeted tests during changes; full required suites on exact-final-head CI.
Verify bilingual course introductions, challenge-before-answer, mobile, written
answers/history, ownership and packaged restart. Save checkpoints on D.
