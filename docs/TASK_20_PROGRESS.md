# Task 20 — Global UI and persistent themes

Engineering objective: unify every frontend route with semantic Dark/Light tokens without changing backend behavior. Learning objective: keep instructions, challenge, execution evidence and quality feedback readable and distinct.

Branch: `feature/task-20-global-ui-redesign`. Base: `9e47ede1a738b83dc695cb415e787d6735015429` (Task 19 merged). Working tree was clean before branch creation.

## Audit and implementation plan

- CSS order: style → review → advanced → platform → discovery. Early mint styles and later purple styles are overridden by route-scoped orange/black discovery styles. Header and CodeMirror gutters have their own fixed colors; responsive typography shrinks several important labels to 10–12px.
- Retain established layouts, nine authored course SVGs and lesson content. Replace historical color declarations with shared semantic tokens, then use a global component stylesheet for consistent typography, controls, panels and responsive navigation. Keep existing layout files rather than introduce a framework.
- Initialize document theme using a blocking same-origin external script in the HTML head, compatible with the existing CSP. Default Dark, safely restore explicit localStorage preference. React controls changes independently of auth/language. Reconfigure CodeMirror theme with a compartment to retain its document, selection and undo history.
- Keep Subjects disclosure layering and keyboard behavior; give Account disclosure equivalent Escape/outside/focus-exit behavior. Use wrapping header rows rather than positioned account controls.
- Verify targeted theme/mobile/editor/navigation checks and existing demo/learning/pipeline flows against disposable local test data. Build once final UI settles; inspect screenshots at 375/768/1280/1920 in both themes. No full local backend suite or live deployment.

## Design research

Reviewed [UI UX Pro Max](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill) and its [MIT license](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill/blob/main/LICENSE). Local skill research returned Dark Mode/OLED: useful contrast and focus guidance, but its pure-black/violet palette, light-mode exclusion and testimonial suggestions do not fit the approved requirements. Use navy/blue paired themes and existing truthful content instead. No reference code, fonts or artwork copied; no new dependencies or external font requests.

## Completed implementation

- Both palettes now apply to landing, catalog, subjects, overview, login/signup, lesson/editor, history/My Learning, account, pipeline and error/loading/empty panels. Blue primary actions and restrained orange labels share accessible paired semantic colors.
- Persistent translated Dark/Light toggle, head bootstrap, blocked/invalid-storage fallback and cross-tab sync. English/language selection and auth are independent.
- Native Subjects and Account disclosures have bounded scrolling, open-layer pointer ownership, keyboard toggling, Escape/focus restoration, outside-pointer and focus-exit dismissal. Header controls wrap in normal flow at all breakpoints. Screenshot inspection caught inherited positioned offsets; removed those and added header containment assertions.
- Learning panels, tables, challenge and status evidence have readable shared type, spacing and code surfaces. CodeMirror appearance reconfiguration retains document/undo and saved answers. Read-only editor text retains full contrast; original editing restrictions remain. Fixed the legacy `:not(.badge)` selector that shrank result/curriculum metadata.
- Nine existing authored course visuals, instructional content and all Task 19 demo actions/policies are preserved. Backend, dependencies, schemas, fixtures, Docker/scripts and live environments have no changes.

## Observed verification

All tests used the existing disposable PostgreSQL container on `127.0.0.1:55419`, D-drive Playwright cache and D-drive temporary files. No live learner/demo database was touched.

- Final `npm run build` (includes `tsc --noEmit`): PASS; 70 modules, no new dependencies. CSS gzip 12.79 kB. `git diff --check`: PASS.
- Final six focused browser regressions: PASS, 93.713s, no skips: three Task 20 methods, Task 18 menu/course presentation, learning/history/pipeline loop, and simulated-HTTPS demo login test.
- After the last metadata selector refinement, reran affected Task 20 methods: **3 PASS**, 34.446s, no skips. Initialization before React with CSP retained, missing/invalid/blocked storage, keyboard switching, reload/navigation/logout/cross-tab persistence; 11 routes × 2 languages × 2 themes × 4 widths, header containment and document overflow; text/status/code contrast ≥4.5:1; 375/390 disclosures and editor node/undo/draft preservation.
- Additional targeted signup/search and SQL/ETL/API guidance/reveal tests each passed during iteration. The exploratory eight-test command had seven passing tests and one test assertion failure: DOM `textContent` concatenates editor line nodes while `innerText` inserts visible newlines. Corrected the undo assertion to compare like-for-like textContent; subsequent focused runs pass. Initial TypeScript build caught an editor extension syntax typo, corrected before successful builds.
- No full suite was run locally. Existing CI automatically performs its configured suite on the pushed head; final SHA/results belong in the PR handoff, without duplicating CI locally.

Commands (PowerShell, from `D:\Data-QA-Lab`; test database only):

```powershell
Set-Location D:\Data-QA-Lab
$env:DATA_QA_TEST_DATABASE_URL='postgresql://data_qa_lab:data_qa_lab@127.0.0.1:55419/data_qa_task19'
$env:PLAYWRIGHT_BROWSERS_PATH='D:\Data-QA-Lab\data\generated\playwright-browsers'
$env:PYTHONUTF8='1'
$env:TEMP='D:\Data-QA-Lab\data\generated\task20'
$env:TMP=$env:TEMP
# This existing container holds disposable test data, never learner/demo data.
docker start data-qa-task19-tests
Push-Location frontend
npm run build
Pop-Location
.venv\Scripts\python.exe -m unittest tests.e2e.test_browser.BrowserTests.test_task20_theme_before_app_storage_fallback_and_persistence tests.e2e.test_browser.BrowserTests.test_task20_global_theme_routes_contrast_and_responsive tests.e2e.test_browser.BrowserTests.test_task20_mobile_disclosures_and_editor_theme_reconfiguration -v
.venv\Scripts\python.exe -m unittest tests.e2e.test_browser.BrowserTests.test_task18_review_subject_menu_and_course_presentation tests.e2e.test_browser.BrowserTests.test_browser_learning_loop_language_history_and_pipeline tests.e2e.test_demo_browser.DemoBrowserTests.test_secure_cookie_login_mobile_courses_sql_submit_resume -v
docker stop data-qa-task19-tests
```

## Screenshots and review

34 Task 20 screenshots remain on D in ignored `e2e-artifacts/`; CI uploads browser evidence. Representative pairs:

- `task20-{dark,light}-landing-1280.png` and `...-landing-375.png`
- `task20-{dark,light}-courses-{1280,375}.png`
- `task20-{dark,light}-login-{1280,375}.png`
- `task20-{dark,light}-pipeline-{1280,375}.png`
- `task20-{dark,light}-account-{1280,375}.png`
- `task20-{dark,light}-lesson-{375,768,1280,1920}.png`
- `task20-{dark,light}-editor-{375,1280}.png`
- `task20-dark-public-demo-375-ENG.png`, `task20-light-public-demo-390-VIE.png` (masked credentials only).

Inspected desktop/mobile landing, login, pipeline, editor and demo screenshots in both themes; stable header containment, coherent surfaces and readable controls. No screenshots with revealed passwords, network traces or long logs are committed.

## Limits and preservation

Automated Chromium viewport verification is not a real-device or screen-reader certification. Safari/Firefox and external public-domain/device checks were not performed. No live deployment or tunnel was started. Existing JSON editor remains plain text; no new syntax-language dependency. Learning examples/results and simulation rules are unchanged; written answers are still saved without semantic grading. Existing learner/demo accounts, budgets, sessions, query/submission history and database isolation remain unchanged; the real simulated-HTTPS test verifies explicit demo autofill/login, masked/reveal/copy controls, Coming Soon signup, password lock, Secure cookies, SQL submission and saved resume behavior.

Implementation and targeted validation complete. Commit/push and review-ready PR pending; do not merge or start another task.
