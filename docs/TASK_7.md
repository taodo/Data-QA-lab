# Task 7 — Browser learning workspace

Engineering: React/TypeScript frontend with CodeMirror SQL highlighting, real API and responsive local assets. Learning: complete Lab 001 using instructions, visible schema, queries, hints, grading and retained evidence.

UI: learning catalog/progress, ENG/VIE picker persisted in browser, instruction/concept/practice/challenge panels, SQL and conclusion drafts, query result table, submission feedback, reveal confirmation, learning history, run stages, QA evidence and isolated fault controls. Language switch retains session/draft/progress. Server state is authoritative; revealing does not mark completion.

Dependencies: React renders interactive state, TypeScript validates contracts, Vite bundles local assets, CodeMirror provides SQL highlighting/editing. Playwright is test-only for the browser loop. No remote fonts or runtime CDN.

Development: API on 127.0.0.1:8000; `cd frontend`, `npm ci`, `npm run dev`. Production local build: `npm run build`, then start API and browse http://127.0.0.1:8000. Frontend dev proxy preserves same-origin behavior. Container startup is Task 7.2.

Verification: TypeScript + production build; browser E2E with actual PostgreSQL/API, language-switch/draft preservation, count-only failure, key-check pass, resume and reveal lifecycle. Task 7.1 expands from Lab 001 to six lessons.
