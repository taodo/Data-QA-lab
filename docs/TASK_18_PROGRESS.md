# Task 18 — UI redesign checkpoint

Engineering objective: improve visual hierarchy and discovery with a scoped
design system, landing and catalog/overview using existing React/TypeScript/Vite.
Learning objective: explain evidence-based QA, execution versus quality and the
understand → practice → inspect → answer flow before learners enter a course.

Base: origin/feature/develop ba25ccd (guidance release docs), including Task 17.
Branch: feature/task-18-ui-redesign. Initial working tree clean on main; main not
modified. No merge or next task authorized.

## Implementation plan and scope

1. Inspect only routing, localization/preferences, auth/demo gate, course UI,
   styles and existing browser tooling; verify actual catalog counts.
2. Install UI UX Pro Max project-locally and inspect generated changes. Use React
   guidance and user Nexus direction; document reference/tool limitations.
3. Add discovery tokens/CSS, a bilingual landing and improved catalog/course
   overview. Keep lesson/editor/pipeline/account surfaces and all content/grading.
4. Default missing/invalid preferences to ENG; preserve explicitly saved VIE.
5. Build, focused real-browser/auth/demo regressions, responsive/keyboard/motion
   checks; capture and inspect final desktop/mobile images. Final CI on exact head.
6. Commit/push and PR to feature/develop; stop for review, do not merge.

## Implementation checkpoint

- Landing at /, catalog at /courses, working CTAs to catalog and existing gated
  pipeline route. Counts come from course API: nine executable courses/36 lessons.
- Source 10/20/30 versus Target 10/20/40 example shows SUCCESS execution but two
  reconciliation violations; explicitly illustrative, never live telemetry.
- Bento capabilities and learning loop describe existing SQL/ETL/API/evidence
  features. Cloud courses prominently label local SIMULATED/IMPORTED evidence.
- Dark/orange discovery theme, shared distinct navigation/focus, system sans
  typography with Vietnamese; no external fonts, image/CDN scripts or runtime deps.
- Course summaries, introductions, lesson navigation, filters and progress kept.
  Learning workspace and submission/account/backend behavior are not redesigned.
- Language fallback changed only in frontend initial preference: saved VIE kept,
  otherwise ENG. Existing persistence through refresh/navigation unchanged.
- Backend demo public signup remains forbidden; landing has no signup CTA and
  pipeline CTA respects AuthGate. Normal signup/login retain existing mechanisms.
- Skill installation/version/hash, selective recommendations and missing Nexus
  asset limitation documented in design-system/data-qa-lab/MASTER.md.
- CSS-only decorative pulse runs twice; no resource loops/listeners/canvas. Reduced
  motion disables animation/transition; essential content always visible.

## Verification checkpoint

- Initial production build PASS (Vite 3.86s).
- Initial browser attempt executed zero tests: Docker Desktop was stopped.
  Started the existing installation at D:\Apps\Docker. Existing learner PostgreSQL
  entered normal startup recovery/fsync; no reset/delete/data repair attempted.
  Verification uses a separate postgres:16-alpine container data-qa-task18-tests,
  bound only to 127.0.0.1:55418, with data under
  D:\Data-QA-Lab\data\generated\task18-20261009\postgres. No learner DB writes.
- Targeted browser coverage added: actual landing/catalog routes, ENG default,
  saved VIE and invalid fallback, 375/768/1024/1440 both locales, course accordion
  keyboard, focus, reduced motion and authenticated pipeline gate. Existing real
  signup/login test adjusted for the intentional new landing route.
- Final production build PASS (Vite 4.09s, 65 modules).
- Four affected browser tests PASS, 62.072s: discovery language/responsive/keyboard/
  motion; real signup/login/search; nine course introductions ENG/VIE; existing
  learning loop including saved history, language switching and pipeline.
- HTTPS demo integration PASS, one test, 15.494s: secure session login, ENG/VIE
  course navigation, SQL/submission/history, restart persistence, CSRF/host checks,
  anonymous gate and public-signup prohibition. Uses its own temporary test DB.
- Captured and visually inspected final e2e-artifacts/task18-{landing,catalog}-
  {1440,375}.png plus task18-{landing,catalog}-vie-375.png. Screenshot inspection
  identified and fixed top margin collapse and small mobile illustration labels.
  Both locales also checked at 768/1024px; no horizontal page overflow observed.
- Calculated token contrast: body/surface 16.48:1, muted/raised surface 7.97:1,
  accent/surface 7.74:1, dark CTA text/accent 7.99:1. Focus outline exceeds 3:1.
  Focused checks only; not a formal accessibility or screen-reader audit.
- Full suite deferred to exact final-head CI; PR will record commit/run/results.
  No duplicate local full-suite run. No Nexus asset available for fidelity testing.
- Initial CI at 0942eb3: 67 unit and 79 integration tests PASS; packaged-v1 PASS.
  Browser suite found one obsolete assertion in review navigation: clicking the
  home breadcrumb expected catalog, although / now intentionally shows landing.
  Updated it to assert landing, follow the catalog CTA, then retain all existing
  challenge/history/pipeline checks. Affected test re-run locally PASS (one test,
  10.789s); final exact-head CI remains required. UI files unchanged, so no duplicate
  local build or screenshot run for this test-only correction.
- Caches/temp/tooling/generated artifacts on D. Learner DB/accounts/history and
  Docker data preserved. No public tunnel opened.

## Local commands

```powershell
Set-Location D:\Data-QA-Lab
git fetch origin
git switch feature/task-18-ui-redesign
git pull --ff-only
docker compose up -d --build --wait
# Open http://127.0.0.1:8000
```

Targeted verification (dedicated test DB must already exist):

```powershell
$env:DATA_QA_TEST_DATABASE_URL = 'postgresql://data_qa_lab:data_qa_lab@127.0.0.1:55418/data_qa_task18'
$env:PLAYWRIGHT_BROWSERS_PATH = 'D:\Data-QA-Lab\data\generated\playwright-browsers'
$env:TEMP = 'D:\Data-QA-Lab\data\generated\task18-20261009\tmp'
$env:TMP = $env:TEMP
npm run build --prefix frontend
.venv\Scripts\python.exe -m unittest tests.e2e.test_browser.BrowserTests.test_task18_discovery_language_responsive_keyboard_and_motion tests.e2e.test_browser.BrowserTests.test_public_courses_search_routes_and_real_signup_login tests.e2e.test_browser.BrowserTests.test_course_introductions_all_courses_language_keyboard_mobile tests.e2e.test_browser.BrowserTests.test_browser_learning_loop_language_history_and_pipeline -v
.venv\Scripts\python.exe -m unittest tests.integration.test_demo.DemoIntegrationTests.test_https_navigation_sql_submission_history_and_csrf -v
```

Resume by checking branch/status, local database health, recorded results and PR
exact-head CI. Never reset learner data or merge as part of this task.

## Focused review follow-up

Continued on the existing feature/task-18-ui-redesign branch from 40fac4f with a
clean working tree. No new task branch, merge or backend/auth-policy change.

- Root cause of mobile Subjects overlap: dropdown and later account disclosure
  were positioned siblings with automatic stacking. Account could paint over the
  dropdown. The existing header now owns an isolated overlay context; open native
  disclosures use layer 1 above normal siblings. No huge z-index or clipping hack.
- Subjects keeps native keyboard toggle and exposes aria-expanded/controls. Added
  Escape close/trigger focus, outside-pointer close, Tab-exit close, listener cleanup
  and mutually exclusive account disclosure on Subjects opening. Panel has bounded
  height, scrolling, viewport width and wrapped subject titles.
- Shared discovery tokens: 14px section labels, 13px small labels, 16px body/1.6,
  14px captions/metadata, 21px card headings, 12–16px label/heading spacing. Essential
  mobile text reflows without shrinking. Hero stages stack vertically on mobile.
- Flex-column card bodies align CTAs per row without fixed text heights. Active
  subject links have current-page semantics plus underline/background. Removed
  generic FOUNDATION TO ADVANCED card label; overview now says hands-on learning.
- Nine authored decorative inline SVG schematics cover the nine course subjects,
  reused in overview. Cover links have accessible course names. No external assets,
  licenses/attribution dependencies, runtime image requests or new dependencies.
- Final production build PASS (Vite 2.59s, 66 modules).
- Four existing affected browser regressions PASS in the initial targeted group:
  ENG/VIE persistence/responsive/motion, signup/login/search, nine introductions and
  learning/history/pipeline. The new test initially clicked search behind the menu
  as an outside target, which correctly could not receive a click. Fixed the test
  to use an uncovered brand link; focused re-run PASS (14.777s).
- After final listener guards, review test PASS (13.923s). Checks actual account
  overlap hit-testing, all nine routes at ENG/VIE 375/390px, bounded panel scrolling
  at 480px viewport height, keyboard/Space/Escape/focus, outside dismissal, active
  filter, nine distinct SVGs, CTA alignment at 375/390/768/1024/1440px, font sizes,
  vertical mobile evidence and absence of horizontal overflow.
- Captured ENG/VIE desktop/mobile landing/catalog, menu and pipeline evidence as
  e2e-artifacts/task18-review-*.png. Visually inspected landing/catalog desktop and
  mobile, ENG 375/VIE 390 menus, VIE mobile pipeline and nine-banner contact view.
  Screenshots will also be available in final CI browser-evidence artifact.
- No unchanged backend suite or full suite run locally for this visual follow-up.
  Existing automatic final-head CI and its artifact/results are recorded on PR #25.
  External-device verification and formal screen-reader audit remain unavailable.

Focused browser command (same dedicated test DB/environment as above):

```powershell
.venv\Scripts\python.exe -m unittest tests.e2e.test_browser.BrowserTests.test_task18_review_subject_menu_and_course_presentation -v
```

Local app remains available through generated, ignored port-8001 Compose config:

```powershell
docker compose --project-directory D:\Data-QA-Lab -p data-qa-lab -f data/generated/docker-compose.local-8001.yml up -d --build --wait
# Open http://127.0.0.1:8001
```
