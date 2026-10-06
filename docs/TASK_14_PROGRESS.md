# Task 14 - Beginner ETL guidance

Engineering objective: follow Task 13 existing text fields and GuidanceText, with
only a SQL-or-ETL rendering condition. No changes to grading, fixtures, simulation,
permissions, scoring, schemas, APIs, accounts or history.
Learning objective: understand each ETL requirement, how to practice with real
session controls, and how to interpret data and execution evidence in ENG/VIE.

## Resumable checkpoint

- Branch: feature/task-14-etl-learning-guidance.
- Base: 2588f03 (latest origin/feature/develop, merged Task 13 PR #18).
- Initial working tree clean; existing learner database and Docker data preserved.
- Five lessons x two languages authored in backend/app/learning/etl_guidance.py.
- Representative transformation lesson passed build/browser before the other four.
- Reuse theory, requirement and private explanation; original contracts remain
  unchanged prefixes. First accordion open; existing reveal/completion gate retained.
- All lessons contain checking, purpose, illustrative example, practice controls,
  challenge explanation, common mistake and private reference-SQL walkthrough.
- Written answers are saved, not semantically graded. No new dependencies.

## Example results checked with actual reference SQL

| Lesson | violation_count | What contributes |
|---|---:|---|
| Mapping | 3 | Wrong customer mapping + missing key + unexpected key |
| Transformation | 2 | One-cent mismatch + NULL amount; valid zero passes |
| Quarantine | 2 | Missing reject + one duplicated reject-key group |
| Replay | 3 | Two stale joined rows + one duplicated Target-key group; future batch excluded |
| Recovery | 2 | One missing Target key + one latest-step defect, even with two bad step fields |

Inspected task10_content.py, etl.py (SQL, fixtures, load/advance/state), profiles.py,
service.py lifecycle, Task10Workspace.tsx controls and existing task10 tests.
Guidance describes actual Reset/Run ETL, Next batch/Replay batch, Recover load;
compares Source/Target/context/rejects/steps before and after; distinguishes
execution SUCCESS from correctness. A final snapshot does not prove every earlier
execution. Only ACTIVE SANDBOX enables controls. Replay/recovery limits and latest
20-step UI view are documented where relevant.

## Existing contract limitations (not changed)

- Recovery original wording implies a latest successful step is required, but the
  reference SQL contributes zero for missing etl_steps: MAX(step_no) is NULL and
  no step qualifies. Added explicit ENG/VIE limitation and a reference-query check.
  An empty step history is incomplete evidence, never proof a load ran.
- Mapping expected uses an inner reference lookup: unknown Source codes are not
  independently flagged. Lookup correctness is trusted; money is not compared.
- Quarantine assumes non-NULL strings as fixtures provide; a NULL predicate enters
  neither valid nor invalid set. It checks routing/reasons/reject duplicates,
  not accepted money or customer mapping.
- Replay ranks visible events by distinct event_id as fixtures provide, not by
  amount/row position; it checks event_id and money, not customer_id or past steps.
- Joined differences count rows, duplicates count groups; sums may include multiple
  diagnostics for the same key. These scopes are explicit in both languages.

## Observed targeted validation

From D:\Data-QA-Lab, using .venv Python and the existing separate test database
`data_qa_task13_browser` (not the learner database). New temporary files are under
D:\Data-QA-Lab\data\generated\task14-20261006; browser cache remains on D.

- `npm run build --prefix frontend`: PASS (TypeScript/Vite).
- `python -m unittest tests.integration.test_etl_guidance tests.integration.test_sql_guidance tests.integration.test_task10.Task10IntegrationTests.test_recovery_replay_and_other_session_are_actual_and_isolated tests.unit.test_curriculum tests.unit.test_learning_contracts -v`:
  12 PASS. All five illustrative datasets use unchanged actual reference SQL in
  connection-local temporary tables. Bilingual coverage/privacy, missing-step
  limitation, SQL guidance regression and actual simulation isolation checked.
- Representative browser test: PASS, controls/language/keyboard/reveal/mobile.
- `python -m unittest tests.e2e.test_browser.BrowserTests.test_etl_beginner_guidance_practice_language_keyboard_and_reveal tests.e2e.test_browser.BrowserTests.test_task10_etl_api_courses_actual_grading_language_and_resume tests.e2e.test_browser.BrowserTests.test_sql_beginner_guidance_keyboard_language_and_reveal -v`:
  3 PASS in 105.986s. All ten ETL language versions show actual control guidance;
  reveal and completion gates, actual grading/simulations/resume, keyboard/mobile,
  and SQL presentation regression passed.
- Independent-process catalog comparison: PASS. All 31 non-ETL lessons unchanged;
  all ten original ETL contracts and other fields preserved. Separate processes
  avoid shared import dictionaries contaminating the baseline comparison.
- No full suite repeated locally; exact-head CI supplies final full verification.

Pending: commit/push, PR targeting feature/develop, final-head CI. Record final
commit, commands/results and CI URL in PR and ignored D-drive handoff artifact.
No merge or next task. Resume with git status and PR workflow runs.
