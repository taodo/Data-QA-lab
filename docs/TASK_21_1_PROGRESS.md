# Task 21.1 — Automation Course Foundation

## Objectives and state

Engineering: additive typed, versioned tutorial curriculum and dedicated public renderer, independent of executable lab sessions/grading/persistence. Learning: choose worthwhile automation, understand pyramid/ROI, run a local pytest example and independently review generated assertions.

Preflight: clean working tree; fetched origin; `feature/develop` at `72ea6d9` includes merged Task 20.1 PR #32 (`f85a2ef`). Created `feature/task-21-1-automation-course-foundation` from that base. Plan announced before edits: validated source manifest → additive catalog/API → dedicated overview/player/copy → focused tests → PR, no merge/deploy.

Implementation complete; local focused validation complete. PostgreSQL-dependent checks are delegated to final-head CI because Docker Desktop on this host crashes before daemon startup. Final commit/PR/CI are recorded in the PR and handoff. No Task 21.2 implementation.

## Design and API compatibility

- `backend/app/learning/automation_curriculum.json`: 10 stable ordered modules (`m01`–`m10`), each with three stable ordered lessons (`m01-l01` etc.). Only `m01-l01` available; 29 planned metadata entries have no content sections. Each has ENG/VIE titles; estimated full roadmap 600 minutes, available lesson 20 minutes. Estimates are editorial, not measured completion times.
- `tutorials.py`: frozen Pydantic source contracts, extra fields forbidden; nonblank language text, ordering/ID uniqueness, section IDs/types and translated structure validated. Available content requires concept/steps/code/prompt/verification/challenge; planned content forbidden. Invalid authored manifests fail validation rather than serving fake lessons. Existing dependency reused, no migration.
- `GET /api/subjects` and `/api/courses` add the tenth subject/course with `learning_kind: tutorial`. Existing nine entries gain `learning_kind: executable_lab`; all legacy fields and 36 lab payloads preserved. Consumers should distinguish course kind rather than infer execution from `available` alone.
- `GET /api/courses/ai-test-automation` publishes `modules`, hybrid explanation, objectives/prerequisites and availability counts; does not overload lab chapters or SQL fields. Catalog `lesson_count: 30` means roadmap entries for tutorials, not executable labs. Landing/catalog executable statistics remain nine courses/36 lessons; tutorial card explicitly says 1 available/29 planned.
- `GET /api/courses/ai-test-automation/tutorials/m01-l01?language=ENG|VIE` is public, read-only, with typed sections. Planned IDs return 409 `TUTORIAL_PLANNED`; missing/wrong-course IDs 404; invalid language 422. Enrollment for this tutorial returns 409 `TUTORIAL_PROGRESS_UNAVAILABLE`. Existing lab session service rejects tutorial IDs. No new write endpoint, progress storage, upload, code execution or AI provider integration.
- Browser routes `/courses/ai-test-automation` and `/courses/ai-test-automation/tutorials/m01-l01` use separate overview/player. Public access avoids changing AuthGate or safeNext; executable routes stay gated. Narrow SPA fallback addition enables refresh without swallowing assets/API errors.
- Course-specific authored local SVG, semantic Dark/Light tokens, keyboard-focusable horizontally scrollable code, functional clipboard write with live success/failure feedback. Clipboard failure preserves selectable text. No raw HTML content injection.
- Tutorial content explains manual vs automated effort, pyramid as heuristic (no fixed ratio), exact Decimal checks, self-comparison trap and learner self-verification. No viewed-page completion claim, quiz or saved answers.

## Changed files

- Backend: learning manifest/contracts, `courses.py`, API route/enrollment guard, SPA fallback.
- Frontend: `TutorialPages.tsx`, App dispatch/breadcrumbs, course card/catalog and landing kind filtering, CourseCover SVG, TypeScript tutorial contracts, scoped styles.
- Packaging: source JSON included as package data in `pyproject.toml`; dependencies unchanged.
- Tests: new tutorial unit/API integration/public browser modules; existing course/Task 12 assertions explicitly retain nine executable courses, catalog/header counts account for tenth tutorial; SPA deep-link regression.
- Documentation: this checkpoint, ROADMAP and current AGENTS scope.

## Observed local validation

- `npm run build`: PASS, TypeScript + Vite, 72 modules (final frontend).
- Focused tutorial/course/API/public browser batch: 10 tests PASS, 14.956s. Browser covers 12 ENG/VIE × Dark/Light × 375/768/1280 combinations, Subjects discovery, all 30 entries, one actionable lesson, refresh/back/forward, each real clipboard copy, refusal feedback, planned/invalid links, no POST requests and anonymous private endpoints 401. Server uses an unusable PostgreSQL URL to prove public reads are database independent.
- Additional SPA/Task 12 focused regressions: 5 tests PASS, 0.191s, including new tutorial refresh paths, invalid route boundaries and retained nine executable courses/36 lab contracts.
- Exact authored Python block executed from ignored D folder: original 4 passed, controlled addition mutation 1 failed/3 passed (110.00 versus 90.00), restored 4 passed. Exit codes checked 0/1/0. pytest installed only as local verification tooling in ignored `.venv`, no application dependency added.
- Initial browser-test fixes: normalize standard Windows CRLF clipboard readback; wrap failure injection so Playwright does not invoke the assigned function during setup. Product clipboard remained functional.
- Docker Desktop startup failed at Secrets Engine socket rename before Linux daemon existed. No factory reset/socket manipulation/data deletion attempted. Local PostgreSQL integration and existing SQL/ETL browser executions unavailable; existing CI `tests` job runs them on disposable PostgreSQL. CI validation is required before declaring those regressions verified.
- No full local suite run; final-head CI is used for broader verification. Existing Starlette/httpx deprecation warning observed; no unrelated dependency upgrade.

Commands (PowerShell, `D:\Data-QA-Lab`):

```powershell
$env:PYTHONUTF8='1'
$env:TEMP='D:\Data-QA-Lab\data\generated\task21-1'
$env:TMP=$env:TEMP
$env:NPM_CONFIG_CACHE='D:\Data-QA-Lab\data\generated\task21-1\npm-cache'
$env:PLAYWRIGHT_BROWSERS_PATH='D:\Data-QA-Lab\data\generated\playwright-browsers'
Push-Location frontend
npm run build
Pop-Location
.venv\Scripts\python.exe -m unittest tests.unit.test_tutorials tests.unit.test_courses tests.unit.test_api tests.unit.test_spa tests.unit.test_task12 tests.e2e.test_tutorial_browser -v
# Once Docker is healthy: this container is disposable test data only.
docker start data-qa-task19-tests
$env:DATA_QA_TEST_DATABASE_URL='postgresql://data_qa_lab:data_qa_lab@127.0.0.1:55419/data_qa_task19'
.venv\Scripts\python.exe -m unittest tests.integration.test_tutorial_api tests.e2e.test_browser.BrowserTests.test_browser_learning_loop_language_history_and_pipeline tests.e2e.test_browser.BrowserTests.test_etl_beginner_guidance_practice_language_keyboard_and_reveal -v
docker stop data-qa-task19-tests
```

## Requirement-to-test traceability

| Requirement | Evidence |
|---|---|
| 01 taxonomy/discovery | Tutorial unit/public API tests; browser Subjects→course discovery; executable count regressions |
| 02 typed contract | Invalid manifest mutations (IDs/order/languages/status/missing or planned content/invalid section/empty code/extra SQL fields); unchanged legacy API tests |
| 03 10×3, one available | Manifest validator + unit count/order/availability; browser 30 entries/one link |
| 04 bilingual overview | API module metadata; browser overview screenshots at 375/768/1280, both themes/languages |
| 05 player/examples/copy | Exact pytest 4-pass/controlled-fail/restored-pass evidence; browser clipboard reads and error feedback; explicit self-verification notices |
| 06 navigation | Public refresh/back/forward; SPA route tests; existing SQL deep-link browser regression in CI |
| 07 safety/compatibility | Database-independent anonymous API/browser with no POST; integration rejects tutorial enrollment/session and preserves account session/enrollment counts; existing SQL/ETL browser tests in CI |

## Screenshots, references and limitations

Ignored D `e2e-artifacts/`: `task21-1-{catalog,overview,player,code}-{ENG,VIE}-{dark,light}-{375,768,1280}.png`. Inspected mobile Dark code, desktop Light/VIE code and both catalog/overview compositions; horizontal scrolling is contained within code blocks. Existing before-catalog evidence `task18-review-catalog-ENG-{375,1440}.png` from Task 20.1 remains available. Tutorial overview/player did not exist before this task, so there is no fabricated before image. CI uploads browser-evidence. No screenshots/logs/database files/credentials committed.

Primary references checked 2026-10-12: [pytest parametrization](https://docs.pytest.org/en/stable/example/parametrize.html), [pytest documentation](https://docs.pytest.org/en/stable/contents.html). Parametrized cases and exception assertions are used locally; website performs neither execution nor automatic verification.

Chromium viewport evidence is not Safari/Firefox, screen-reader or physical-device certification. Windows setup assumes installed Python `py` launcher and internet for learner-side pytest installation. Clipboard requires browser support/secure context; fallback feedback directs manual selection. Local Docker startup is an environment limitation. Existing 15 public demo accounts, data, secrets, schema and deployment remain untouched; no live tunnel, merge or deploy.

Deferred: 29 authored lessons, quizzes and personal progress need separate approval. No Task 21.2 APIs or persistence introduced.
