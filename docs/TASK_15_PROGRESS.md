# Task 15 - Beginner API guidance

Engineering objective: reuse existing theory/requirement/private explanation fields
and GuidanceText; extend its course condition only for API. Preserve execution,
grading, retries, fixtures, simulation, schemas, APIs, permissions, scoring and data.
Learning objective: help beginners interpret local HTTP response contracts,
pagination, bounded retries, and API-to-PostgreSQL ingestion/replay in ENG/VIE.

## Checkpoint

- Branch: feature/task-15-api-learning-guidance.
- Base: latest origin/feature/develop, 221e1b4 (Task 14 merge, PR #19).
- Initial working tree clean. Preserve original learner database and Docker data.
- All four API lessons x two languages complete in api_guidance.py.
- Representative response-contract lesson passed build/browser before other three.
- Seven sections per lesson: checking, purpose, illustrative example, practice,
  challenge explanation, common mistake, private step-by-step reference explanation.
- Original eight challenge strings remain unchanged prefixes; JSON starter plans,
  hints, objectives and all other fields remain unchanged. 32 non-API lessons match base.
- Reference explanations stay inside existing reveal/completion gates. JSON plans,
  not learner SQL, are submitted; the executor creates its diagnostic count.
- Written answers are retained, not semantically graded. No new dependencies.

## Actual illustrative outcomes

Three reference keys 10/20/30, customer IDs 7/8/7 and exact amounts 10.01/0.00/7.00.
Examples are explicitly illustrative; they are not generated hidden scenario data.

| Lesson | Outcome verified through unchanged HTTP executor |
|---|---|
| Response contract | HTTP 200 with a missing amount: transport SUCCESS, quality FAIL, count 1; missing/type rules do not double-count one record |
| Pagination | Two correct pages: 0; response omits key 30 while total agrees with its own items: 1; duplicated key 30 group: 1 |
| Bounded retries | 429/503/200 on two pages: 6 requests, count 0; two attempts stop first page: one final-status defect + three missing keys = 4; three timeouts also 4 |
| Ingestion/replay | Two idempotent replays retain three actual Target rows: 0; append retains six rows/three duplicate groups: 3; key missing from response and Target: 2 |

Tests use three-row reference data in an isolated transaction schema, invoke the
real loopback server/client and PostgreSQL Target, then rollback all example writes.
They also verify a new ingesting run resets Target and a non-ingesting send leaves
previous stored Target intact. No external API calls or credentials.

Inspected task10_content.py, http_exercises.py parser/executor/fixtures/checks,
profiles.py, service.py query/submission/reveal lifecycle, Task10Workspace.tsx,
SqlEditor.tsx, LessonPlayer.tsx and existing Task 10 tests.

## Existing behavior and limitations (not changed)

- Submission compares resulting counts with independent expectations across clean,
  shifted and defective cases. It does not structurally demand one exact JSON plan.
  Local quality uses enabled learner checks; status-only PASS can omit data checks.
- Shared query-result SUCCESS means the executor returned evidence; HTTP execution
  FAILED and quality FAIL can coexist with it. Recovered intermediate HTTP attempts
  are trace evidence, not final-status defects. Infrastructure errors remain ERROR.
- Retry-After is recorded, but retries use a fixed short pause, not provider backoff.
- Page cap is ten; no separate total/next_page field validator is implemented.
  Completeness compares collected keys with the independent expected keys.
- Ingestion replays twice within one run, starts a fresh Target per ingesting run,
  and checks actual persisted data. It does not prove replay across historical runs.
  Non-ingesting sends leave stored Target untouched; grading rolls back its writes.
- Reconciliation uses a final value per duplicate Target key plus a group check;
  it does not independently inspect every duplicate member's value.
- Windows timeout fixtures can log ConnectionAbortedError/WinError 10053 after
  clients abort. Targeted assertions passed; this pre-existing executor logging
  behavior is left unchanged. No unresolved mismatch in the authored outcomes.

## Observed local validation

Run from D:\Data-QA-Lab with .venv Python; dedicated existing test database
`data_qa_task13_browser`, not learner database. Artifacts/temp under
D:\Data-QA-Lab\data\generated\task15-20261006; browser cache remains on D.

- `npm run build --prefix frontend`: PASS, TypeScript/Vite.
- `python -m unittest tests.integration.test_api_guidance tests.unit.test_task10 tests.integration.test_task10.Task10IntegrationTests.test_http_graders_reject_incomplete_checks_and_preserve_real_target -v`:
  7 PASS in 14.368s. Actual execution/reference checks, four-by-two content/privacy,
  JSON limits and real grading/Target preservation verified.
- `python -m unittest tests.integration.test_sql_guidance tests.integration.test_etl_guidance -v`:
  4 PASS in 2.849s; unchanged SQL/ETL examples and private content gates.
- Representative API browser check: PASS in 7.931s, JSON editor, actual HTTP trace,
  controls, ENG/VIE, keyboard, reveal lock and mobile.
- `python -m unittest tests.e2e.test_browser.BrowserTests.test_api_beginner_guidance_json_evidence_language_and_reveal tests.e2e.test_browser.BrowserTests.test_task10_etl_api_courses_actual_grading_language_and_resume tests.e2e.test_browser.BrowserTests.test_sql_beginner_guidance_keyboard_language_and_reveal tests.e2e.test_browser.BrowserTests.test_etl_beginner_guidance_practice_language_keyboard_and_reveal -v`:
  4 PASS in 116.680s. Four-by-two API practice/private content, JSON editor,
  real HTTP controls/evidence, reveal locks, bilingual completion, history/resume,
  keyboard/mobile and SQL/ETL rendering regressions verified.
- Independent-process catalog comparison: PASS, 32 non-API entries unchanged and
  all eight original API contracts/other fields preserved.
- No full suite duplicated locally; exact final-head full CI provides verification.

Pending release: commit/push, open PR targeting feature/develop, inspect full CI
on exact head. Record head and results in PR and D-drive handoff artifact; avoid
post-verification commits. No merge or next task. Resume by checking git status,
branch and PR workflow runs, particularly if workspace branch changes externally.
