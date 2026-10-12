# U2 — Unified Homepage & Three Learning Tracks

Status: implementation complete; PR review pending. No merge or deployment.
Branch: `feature/u2-unified-learning-tracks`. Base: current fetched
`origin/feature/develop`, `37734f528d9afec26d2c155c60b00af2ab1d67a4`
(approved U1 PR #34; contains Task 20/20.1 and Task 21.1).
Final commit/CI evidence is recorded in the PR to avoid a self-referential SHA.

## Objectives and decisions

Engineering: provide one shell and exact public track routes while preserving
course IDs, lab/session contracts, auth redirects and persisted preferences.
Learning: distinguish runnable Data QA labs, readable Automation tutorials and
future Banking practice; observations and page views do not prove completion.

U1's four documents and the accepted design-system MASTER were read before
editing. Initial tree was clean; the task branch was created from fetched develop.
No domain repository code, deployed configuration or databases were touched.
No dependencies, migration, banking adapter, progress API or execution service.

## Route and availability contract

| Route | Implemented experience | Evidence |
|---|---|---|
| `/` | ENG/VIE unified hero, three distinct local decorative SVG cards and working track actions | Public browser test, keyboard Enter, both themes and all three widths |
| `/learn/data` | Existing Data landing reused; catalog-derived nine executable course cards / 36 labs | Catalog checks; original Data landing browser assertions moved here without removing them |
| `/learn/banking` | ENG/VIE goals for accounts/API/transfers/ledger/idempotency/transaction integrity; simulator/challenges Planned | No form, iframe, credentials, state mutation or domain request |
| `/learn/automation` | Existing course API, 10 modules / 30 entries; links to overview and available `m01-l01` | 1 available / 29 planned; missing availability has honest error/retry; no invented curriculum |
| Existing course/subject/tutorial URLs | Unchanged dispatch, IDs and players | Catalog/tutorial unit and browser regressions |
| `/my-learning`, `/history`, `/pipeline`, `/account`, executable lessons | Existing account protection and safe login return links | Guest browser redirect assertions; authenticated workflows covered by CI |
| Legacy `/learn/lab_*` | Existing SQL alias retains session query and replaces URL | Browser redirect and SPA tests |
| Unknown `/learn/*` | In-app Not Found; direct HTTP 404 | No indefinite loading; future nested Banking/Automation paths remain 404 |
| Missing `/api/*`, assets, extra path segments | Existing HTTP errors | Bounded SPA unit/browser negative tests; GET/HEAD only, POST rejected |

Backend diff is one SPA pattern extension for three exact public paths. No
catchall or auth/safeNext changes. Frontend dispatch uses the same exact routes.
The track nav lives in the existing breadcrumb bar, below the unchanged header.
Active tracks have a visual underline and `aria-current`; menu stacking is kept.
ENG remains default; explicitly saved language/theme preferences remain intact.

## Changed files

- `frontend/src/TrackPages.tsx`, `tracks_i18n.ts`: bilingual track presentation,
  reused Data landing/course cards and existing Automation API/visuals.
- `frontend/src/App.tsx`, `academy.css`: exact dispatch, shared track navigation,
  scoped token-based layout, flexible CTA alignment and responsive SVGs.
- `backend/app/api/spa.py`: exact refresh allowlist extension only.
- `tests/unit/test_spa.py`, `tests/e2e/test_unified_tracks.py`: route negatives,
  track behavior/preferences/navigation/keyboard/mobile/error recovery.
- `tests/e2e/test_browser.py`: retain original Data landing checks at its new
  route; add tracks to existing theme/contrast matrix and update home breadcrumb.
- `AGENTS.md`, `docs/ROADMAP.md`, `docs/UNIFIED_PLATFORM_ROADMAP.md`,
  `design-system/data-qa-lab/MASTER.md`, this file: accurate U2 checkpoint.

## Executed local verification

Use PowerShell from `D:\Data-QA-Lab` (existing venv/npm installation):

```powershell
$env:PYTHONUTF8='1'
$env:TEMP='D:\Data-QA-Lab\data\generated\u2'
$env:TMP=$env:TEMP
$env:PLAYWRIGHT_BROWSERS_PATH='D:\Data-QA-Lab\data\generated\playwright-browsers'
$env:NPM_CONFIG_CACHE='D:\Data-QA-Lab\data\generated\u2\npm-cache'
.\.venv\Scripts\python.exe -m unittest tests.unit.test_spa tests.unit.test_courses tests.unit.test_tutorials tests.e2e.test_unified_tracks -v
Push-Location frontend
npm run build
Pop-Location
.\.venv\Scripts\python.exe -m unittest tests.e2e.test_unified_tracks tests.e2e.test_tutorial_browser -v
git diff --check
```

- First targeted unit/browser batch: **PASS**, 8 tests in 24.618s.
- Final TypeScript/Vite build after the panel-spacing adjustment: **PASS**,
  74 modules; CSS 71.92 kB, main JS 143.05 kB before gzip.
- Final U2 + existing tutorial browser regression: **PASS**, 3 tests in 38.539s.
- Markdown fences/local references across five changed documents and final
  `git diff --check`: **PASS**.
- Browser tests use Chromium and an actual random-port loopback FastAPI server,
  invalid DB URL for public-only behavior. No mock banking service or public
  domain requests; recorded track requests are GETs to the platform origin only.
- ENG/VIE × Dark/Light × 375/768/1280: action navigation, exact availability,
  refresh, Back/Forward, no horizontal overflow, Subjects hit-testing/Escape/
  focus return, keyboard CTA and reduced motion. Existing tutorial regression
  additionally exercises copy success/failure, planned lessons and guest privacy.

## Screenshots and limits

Ignored local evidence: `e2e-artifacts/u2-before-home-dark-375.png` and
`u2-before-home-light-1280.png`; final `u2-home-{ENG,VIE}-{dark,light}-{375,768,1280}.png`
and `u2-{data,banking,automation}-...png`. Desktop/mobile screenshots were inspected
for text wrapping, card alignment, status clarity and shared theme presentation.
CI uploads final screenshots with its existing `browser-evidence` artifact.
No screenshots, logs, generated assets/cache or credentials are committed.

NOT RUN locally: PostgreSQL-backed SQL/ETL/authenticated history suites and Docker
restart/demo checks; local Docker daemon was unavailable in the existing state.
The unchanged CI workflow runs these on disposable CI-only databases/containers,
not retained deployed data. Full-suite local duplication is intentionally avoided;
final-head CI status and commands are reported in the PR.
NOT RUN: external devices, Firefox/WebKit, screen-reader audit, live domain
verification or deployment. Focused accessibility checks are not WCAG certification.

Banking integration, independent Automation framework/artifact integration and
tutorial progress remain future gated tasks. U3–U10 are not implemented here.
Stop after independent review-ready handoff; no merge/deployment/next task.
