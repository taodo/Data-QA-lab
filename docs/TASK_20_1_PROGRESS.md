# Task 20.1 — Header UI polish

## Objectives and checkpoint

Engineering: one accessible search focus indicator and consistent disclosure icons, preserving the shared header's existing interaction/layout behavior. Learning: keep course discovery, ENG/VIE selection and account navigation usable with keyboard and pointer.

Branch: `feature/task-20-1-header-polish`, based on current `origin/feature/develop` at `727f6c65993fa9b571c671c3e47bc7c1351047b8` (Task 20, PR #30). Initial working tree was clean. Implementation and local verification complete; wait for review, no merge/deployment.

## Root cause and changes

- The global `:focus-visible` outline applied to the nested search input, whose bounds exclude the search icon/padding. Combined with the container border this produced the offset/double-ring appearance. A scoped `:focus-within` outline now surrounds the complete container; only its input outline/shadow is suppressed. A 3px outline with 3px offset uses existing paired theme focus tokens without changing layout geometry.
- Both dropdowns used a font-dependent Unicode pseudo-element. Shared decorative `DisclosureChevron` renders a 16px SVG with 2-unit stroke and existing 8px flex gap. Native markers are suppressed; `[open]` rotates the SVG. Existing details/summary handlers remain unchanged.
- Account-name truncation now uses an explicit class so adding the icon does not invalidate the previous last-child selector. Narrow rows continue to wrap rather than overflow.
- Focused browser regression asserts styles, contrast >=3:1 against the header, unchanged search geometry, search submission, icon alignment/state, menu containment/link hit-testing, Enter/Space/Escape, outside click, focus restoration/exit and mutual exclusion in both languages/themes at 375/768/1280px.

No backend, authentication policy, learning contract, database, Docker or tunnel configuration changes. No dependencies.

## Observed verification

- Final frontend `npm run build`: PASS, TypeScript + Vite, 71 modules.
- `test_task20_1_header_focus_chevrons_and_interactions`: PASS (23.394s), 12 theme/language/viewport combinations.
- Existing `test_task18_review_subject_menu_and_course_presentation`: PASS. Initial combined run's new assertion timed out because it tried to click Account through the intentionally overlaid Subjects panel at 375px; a second run exposed the same test assumption at 768px. Corrected to keyboard switching for those widths, pointer switching at 1280px; product handlers unchanged. Final focused rerun passed.
- Before capture: PASS using existing real browser/HTTP/disposable PostgreSQL fixture. Inspected before/after mobile Dark, after mobile Light/VIE, desktop Dark/Light and tablet Light/VIE menu screenshots.
- Full backend suite deliberately not run for this frontend-only task. Existing GitHub workflow runs on push/PR; its status is reported in the handoff, not assumed successful.

PowerShell from `D:\Data-QA-Lab` (existing disposable test database only):

```powershell
$env:NPM_CONFIG_CACHE='D:\Data-QA-Lab\data\generated\task20-1\npm-cache'
Push-Location frontend
npm run build
Pop-Location
$env:PYTHONUTF8='1'
$env:TEMP='D:\Data-QA-Lab\data\generated\task20-1'
$env:TMP=$env:TEMP
$env:PLAYWRIGHT_BROWSERS_PATH='D:\Data-QA-Lab\data\generated\playwright-browsers'
$env:DATA_QA_TEST_DATABASE_URL='postgresql://data_qa_lab:data_qa_lab@127.0.0.1:55419/data_qa_task19'
docker start data-qa-task19-tests
.venv\Scripts\python.exe -m unittest tests.e2e.test_browser.BrowserTests.test_task20_1_header_focus_chevrons_and_interactions tests.e2e.test_browser.BrowserTests.test_task18_review_subject_menu_and_course_presentation -v
docker stop data-qa-task19-tests
```

## Evidence and limits

Local PNGs are retained on D in ignored `e2e-artifacts/`. Before: `task20-1-before-search-{dark,light}-{375,768,1280}.png` and `...-before-menu-...`. After: `task20-1-after-search-{dark,light}-{ENG,VIE}-{375,768,1280}.png` and `...-after-header-{subject,account}-links-...`. Existing CI uploads after screenshots as `browser-evidence`; no lengthy logs or screenshots committed.

Automated Chromium viewport checks and visual inspection are not real-device, screen-reader, Safari or Firefox certification. Those checks and live production verification were not performed. The isolated test container was stopped after verification with data retained; learner/demo data untouched. No public access, deploy or merge performed.
