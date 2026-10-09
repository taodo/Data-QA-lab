# Task 6 — Local API and bilingual learning contracts

Engineering: HTTP access to existing services without bypassing restricted SQL or lifecycle visibility. Learning: read instructions, query evidence and resume sessions in ENG or VIE.

FastAPI/uvicorn serve HTTP; httpx is the test-only client. No automatic privileged provisioning on startup. Run db-init and lab-sql-init explicitly, seed and run the pipeline, then `python -m uvicorn backend.app.api:app --host 127.0.0.1 --port 8000`. Swagger: http://127.0.0.1:8000/docs.

Routes under /api: lessons, sessions (query/submit/hint/reveal), runs (quality), isolated operator faults (quality/reset), health. Lessons exclude hints and solutions. Session serializers control reveal. Historical API contract: language=ENG|VIE defaults to VIE when omitted. Task 18 frontend always requests its explicit preference: first visit/invalid preference defaults to ENG; saved VIE remains respected. Data model names and status codes remain stable. Decimal values remain strings.

Local single-user process: mutation gate prevents overlapping operations; Host and Origin guards and a 64 KiB body limit restrict the local HTTP boundary. Operator fault routes concern separate workspaces, not hidden challenge snapshots. Server exceptions do not expose credentials or SQL schema details.

Verification: unit API contracts and real PostgreSQL HTTP learning loop, forbidden metadata reads, clean QA, bilingual resume, lifecycle conflicts. Windows verification awaits the user's restored GitHub connection. Task 5 approved and merged before this branch.
