# Task 9 proposal — Learning platform UI and local accounts

Status: approved for implementation on 2026-10-04. Task 8 merged into
`feature/develop` at `973fed8e5cbc10551c2b274b49fcddf88fea06c9`.
All four parts are implemented on `feature/task-9-learning-platform` and await
completed-task review before merge. See [delivery and operation](TASK_9.md).

## Goal and user flow

Turn the current lab collection into a learning platform with course browsing,
structured course pages and a focused lesson player. Use familiar course-platform
patterns, with an original Data QA Lab design. Preserve ENG/VIE, real PostgreSQL
practice, independent grading, SQL restrictions and existing history.

The user chose local accounts first. Registration and login must actually work;
progress must belong to the signed-in learner. This extends the original V1
single-user scope. Online hosting and email services are later work.

Browse courses → read course objectives and syllabus → sign up/log in → start or
resume a lesson → read instructions → run SQL → read the challenge → submit SQL
and its explanation → view feedback → resume from My Learning.

## 9.1 — Course platform design

- A course home with clear subject categories, search and course cards showing
  level, outcomes, available lessons, estimated study time and personal progress.
- A course detail page with objectives, prerequisites, chapter syllabus and
  Start/Continue actions. A My Learning page prioritizes enrolled courses and
  recent work rather than exposing only a raw session list.
- A lesson player with chapter navigation, readable instructions and schema,
  SQL editor/results, challenge immediately before its answer, and learning
  feedback. Preserve unsent drafts and ENG/VIE choices when navigating.
- A distinct visual hierarchy: meaningful course illustrations/icons, balanced
  color accents, typography, spacing and responsive navigation. Existing lesson
  and pipeline pages share the same navigation and visual system.
- Reviewable desktop/mobile screens before connecting the complete flow. No
  invented ratings, learner counts, instructors, certificates or video content.

## 9.2 — Subject pages, curriculum and routes

Subject, course, chapter and lesson are separate concepts. Difficulty and SQL
topic filters remain within a course; they are not the platform's top-level
subject taxonomy.

| Subject area | Initial state | Planned learning scope |
|---|---|---|
| SQL for Data QA | Usable now | Organize the existing 13 lessons into chapters; preserve IDs/history |
| ETL / ELT Testing | Planned | Pipeline stages, transformations, reconciliation, incremental and SCD testing |
| API / Data Contract Testing | Planned | Request/response contracts, ingestion, schema and data consistency |
| Microsoft Fabric | Planned | Fabric-specific pipelines and data testing |
| Azure Data Factory | Planned | ADF orchestration and pipeline validation |
| OneLake | Planned | Lake data layout and consistency |
| Azure Data Platform | Planned | Shared Azure concepts and integrations |
| Databricks | Planned | Lakehouse and transformation validation |
| Azure Synapse | Planned | Warehouse/analytics pipeline validation |

Each area has its own page. Planned courses show an honest availability label
and learning objectives; they do not offer broken Start buttons or claim runnable
labs. ETL/API course content and real cloud adapters require later scoped tasks.
Fabric, ADF, OneLake and Synapse share the Microsoft/Azure family, while retaining
their own recognizable course pages.

Use real routes for home, subject, course, lesson, My Learning, Pipeline & QA and
account pages. Direct URLs, reload, browser Back/Forward and clickable breadcrumbs
must work. Preserve old lesson IDs and resume links where applicable.

## 9.3 — Local Login / Signup and ownership

- Sign up with a local username/display name and password; login, logout,
  current-account view and password change. Account recovery is an explicit local
  operator procedure; this scope does not depend on SMTP, Google login or hosting.
- Use a vetted password-hashing implementation, opaque server-side sessions,
  HttpOnly cookies, CSRF/origin protection, expiry and revocation. Apply appropriate
  login throttling and avoid exposing credentials in browser storage or logs.
- Add ownership to learning sessions, drafts, progress and user-created pipeline/
  fault workspaces. Check ownership on the server for every read/mutation; UUIDs
  and hidden UI buttons are not authorization.
- Keep any shared teaching baseline read-only for learners. Separate operator
  initialization and recovery from ordinary learner actions. Preserve the existing
  database SQL-role/schema/time/output restrictions.
- Retain previous history through a transactional schema upgrade. Provide backup
  and an explicit way to associate legacy history with the chosen account; do not
  silently assign all history to whoever signs up first.
- Namespace browser drafts by account and clear account-specific visible state
  on logout. One learner must not inherit another learner's unsent answer.

## 9.4 — Verification and local delivery

- Real registration/login/logout/restart flow and two-account isolation checks:
  another account cannot read/submit/reveal/simulate another learner's session,
  access its history, or mutate its run/fault data by guessing an ID.
- Test password/session/CSRF behavior and the legacy upgrade with retained data.
- Browser tests for course search, subject/course routes, chapters, breadcrumbs,
  Back/Forward/reload, ENG/VIE, drafts, My Learning and mobile layout.
- Continue actual PostgreSQL grading of all 13 existing lessons, restricted SQL
  checks, pipeline/fault behavior and packaged Docker restart retention.
- Deliver one Task 9 PR, updated Windows D-drive startup/backup instructions and
  a source ZIP fallback. The user's machine-specific review remains a separate
  observed check from Linux CI.

Exit criterion: a learner can register locally, find the SQL course, complete a
real lesson and log back in after restart with the correct personal progress;
another learner cannot access that work. Planned areas have coherent pages and
clear availability, with no pretend cloud execution.

## Model and sequence

Recommendation: keep GPT-6.1 Sol with high reasoning effort for this task. This is
an engineering judgment based on the combined UI/routing/ownership/migration work.
The [official model page](https://developers.openai.com/api/docs/models/gpt-6.1-sol)
describes its coding capability and supports high reasoning effort.

Proposed next sequence after Task 9: runnable ETL/API curriculum, then separately
planned cloud adapters for Fabric/ADF/OneLake/Databricks/Synapse. This proposal
reorders the earlier optional Task 9 cloud adapter; it does not authorize cloud
implementation, payment, video hosting or AI tutoring.
