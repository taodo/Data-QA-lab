# Task 13 — SQL learning guidance

Engineering objective: reuse the existing bilingual text fields and expandable UI,
with no changes to grading, schemas, APIs, permissions or non-SQL courses.
Learning objective: help beginners explain what each SQL check counts, why it
matters, and how the revealed reference SQL meets the requirement.

## Branch and checkpoint

- Branch: feature/task-13-sql-learning-guidance.
- Base: origin/feature/develop at e46cfdf53c00b9c19de79ca241b0384d2bb37c8f.
- Initial working tree was clean. Existing learner database and Docker data preserved.
- Implementation complete for 13 SQL lessons, each in ENG and VIE.
- Duplicate-groups lesson was the representative draft; local build and browser
  presentation passed before applying the format to the other twelve lessons.
- Commit/push/PR and exact-head CI are the release checkpoint; do not merge.

## Completed scope

Every lesson has what we check, why it matters, an explicitly illustrative miniature
example, a common mistake, the unchanged original challenge contract plus a plain
explanation, and a private step-by-step solution explanation. Native details/summary
accordions reuse current styles and keyboard behavior. The first section opens by
default. Revealed explanations remain inside the existing solution gate; written
answers are retained, not semantically graded.

| Lesson | Illustrative violation_count | Counting meaning |
|---|---:|---|
| SQL basics | 2 | Rows with customer_id <= 0 |
| NULLs | 1 | Rows with NULL net_amount |
| Duplicates | 1 | Duplicate key groups, not excess rows |
| Key completeness | 2 | Missing plus unexpected distinct keys |
| Calculations | 2 | Joined rows with NULL-safe amount mismatches |
| Capstone | 3 | Sum of five diagnostic counts |
| JOIN/grain | 1 | Orders whose reconciled totals differ |
| Latest version | 1 | Current rows inconsistent with deterministic winner |
| UTC dates | 2 | Missing/unexpected or mismatching daily groups |
| Incremental/replay | 2 | Joined mismatches plus duplicate groups |
| Freshness | 2 | Required dataset rows violating freshness rules |
| SCD Type 1 | 1 | Current customer mismatches |
| SCD Type 2 | 2 | Sum of version, overlap, range, duplicate and current diagnostics |

Inspected profiles.py, advanced_profiles.py, workspace.py, advanced_workspace.py,
content.py, advanced_lessons.py and service.py alongside existing tests. Exact
NUMERIC arithmetic, deterministic tie breakers, UTC boundaries, inclusive arrival
cutoffs, replay, SLA boundaries and half-open SCD intervals are explained from the
implemented contracts.

## Observed targeted verification

Run from D:\Data-QA-Lab with .venv Python. Test database is the separate local
`data_qa_task13_browser`; no learner reset was performed. Browser cache and temp
files stay under D:\Data-QA-Lab\data\generated.

- `npm run build` in frontend: PASS (TypeScript and Vite).
- `python -m unittest tests.integration.test_sql_guidance -v`: 2 tests PASS.
  All thirteen miniature datasets execute the actual unchanged reference SQL in
  connection-local temporary tables; ENG/VIE count statements match. UTC example
  also passes with Asia/Bangkok connection timezone. Public catalog coverage and
  solution-explanation privacy are checked for all 26 language entries.
- `python -m unittest tests.unit.test_curriculum tests.unit.test_learning_contracts tests.unit.test_advanced -v`:
  11 tests PASS in the combined targeted run.
- `python -m unittest tests.e2e.test_browser.BrowserTests.test_sql_beginner_guidance_keyboard_language_and_reveal tests.e2e.test_browser.BrowserTests.test_review_navigation_challenge_and_pipeline_guidance -v`:
  2 tests PASS; ENG/VIE, keyboard Enter/Space, reveal gate, submit lock, mobile
  overflow and existing course navigation/challenge presentation checked.
- One initial content assertion failed because the displayed arithmetic was
  `1 + 1 = 2` rather than the test's explicit `violation_count = 2`; clarified the
  ENG/VIE notation and reran the affected reference-SQL/content tests successfully.
- No repeated full-suite run locally. Final-head CI supplies full verification.

## Limits and resuming

These explanations preserve existing counting semantics, not broader guarantees:
SQL basics does not include NULL customer_id; calculations use matched rows;
capstone trusts the Gold daily baseline; incremental mismatches are joined rows,
not unique bad orders; an entirely missing SCD customer has no Target current group.
The original challenge contracts stay visible. No grader discrepancy was found.
Miniature examples illustrate rules and do not expose generated hidden scenarios.
No SQL, scoring or account behavior was changed. No new dependencies.

Pending release actions: commit/push, open PR to feature/develop, and inspect full
CI on the final head. Record the tested head and CI link in the PR/handoff so no
post-verification documentation commit invalidates that evidence. No merge.
