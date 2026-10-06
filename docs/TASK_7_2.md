# Task 7.2 — Usable local V1 release

Engineering: packaged React/API/PostgreSQL app, idempotent bootstrap, health checks, Windows/D-drive workflow, backup, recovery and integration evidence. Learning: start without installing a developer toolchain and resume the complete learning loop.

Compose exposes only 127.0.0.1:8000 and existing 127.0.0.1:5432. The app container runs as a non-root OS user with one API worker; privileged DB provisioning is separate from restricted learner SQL. Startup preserves existing successful run/history, creates a 1,000-order baseline only when needed and explicitly hardens the dedicated lab database. Build assets are local. D-drive paths and Docker image storage distinction are documented.

Validation includes fresh DB/bootstrap restart, full browser flow across all six ENG/VIE lessons, packaged container HTTP/SQL smoke and container restart retention. Actual user Windows verification remains pending while the machine cannot reach GitHub. See V1_GUIDE.md and VERIFICATION.md.
