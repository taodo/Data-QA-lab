# Unified Platform Integration Contract — U1

Contract identifier: **UPIC-1.0 (proposed review draft)**. This is the authoritative integration blueprint for `taodo/Data-QA-lab`, `taodo/MiniBanking`, and `taodo/Automation-QA-Lab`. It defines future obligations; it does not claim integration endpoints, SSO, synchronization or an execution service exist. U1 changes Markdown only. Approval of this document is not approval to release Banking/public code execution.

Normative terms: MUST preserves a required boundary; PROPOSED needs implementation approval; UNRESOLVED blocks the affected future slice. Verified baseline/provenance/source links and actual live observations are in [Architecture](UNIFIED_PLATFORM_ARCHITECTURE.md#1-repository-and-deployment-provenance). Roadmap gates are in [Roadmap](UNIFIED_PLATFORM_ROADMAP.md); required tests are in [Test Strategy](UNIFIED_PLATFORM_TEST_STRATEGY.md).

## 1. Confirmed repositories and service identities

| Repository | Verified now | Future contract |
|---|---|---|
| [Data-QA-lab](https://github.com/taodo/Data-QA-lab) | React/TypeScript/Vite + FastAPI + PostgreSQL; develop `e4274a4e0624d7da085e34963c06676f6c19f74f` | Sole public platform shell/origin owner at `https://data-qa-lab.store`; approved integration adapters stay in existing backend initially. |
| [MiniBanking](https://github.com/taodo/MiniBanking) | Accepted develop `2d7bf660611cbfe853489b9014f0453acbfcf1c8`, FastAPI/SQLite, static Vietnamese learning UI | Private banking domain API; independent synthetic business state. Task 9 PR #18 remains draft/BLOCKED, not an integration dependency. |
| [Automation-QA-Lab](https://github.com/taodo/Automation-QA-Lab) | Main `b13353265707223b83b46855a55695655398775b`, `.gitattributes` only | Owns future frameworks/reusable examples/local-CI execution and evidence production. Not an existing web service. |

No Git branch merges between repositories. Consume reviewed pinned APIs/packages/artifacts/adapters; no third backend until separately approved execution requirements justify it.

## 2. Ownership and UI inheritance

| Record/component | Authority | Consumer / prohibition |
|---|---|---|
| Global header, track navigation, React routes, theme, ENG/VIE | Data QA platform | All tracks MUST reuse it, not mount separate applications/design systems. |
| Platform account/cookie/CSRF/session | Data QA PostgreSQL/auth | Bank/Automation cannot accept these as domain credentials. X-DQA-Account is only a stale-identity check. |
| Existing courses/36 lab contracts/query history/reveal/completion | Data QA | Preserve all IDs, SQL permissions, expected/grading truth and ownership. |
| Automation tutorial course/presentation | Data QA | Keep Task 21.1 manifest/player, ten modules/30 entries/one available lesson; no duplicate course or automatic source synchronization. |
| Future framework/code examples and runner configuration | Automation QA repository | Export reviewed, licensed, versioned examples/artifacts; platform authors/reviews presentation and ENG/VIE equivalence. Website never executes imported code. |
| Banking rules/API models/transfer ledger/idempotency/SQLite | MiniBanking | Adapter calls API; no direct PG consolidation, table queries as runtime API, or reimplementation of posting logic. |
| Bank mock role credentials/tokens | MiniBanking | Future adapter holds only server-side scoped tokens; no platform token forwarding. |
| Future practice-context ownership/lifecycle grants | Platform integration control plane + domain-owned isolated runtime | Exact owner/scope/retention design needs U5 approval; no such registry/provisioner exists today. |
| Existing Data QA progress/enrollment | Platform PostgreSQL | Derived from real account-scoped lab sessions; viewing content/query SUCCESS does not complete a lesson. |
| Existing Banking UI progress | MiniBanking localStorage self-marking | Device-local, untrusted and not platform user progress; do not migrate/credit automatically. |
| Automation tutorial progress | Not implemented | Future platform-owned feature after separate task; no implied completion. |
| Future Banking assessed evidence/completion/unified dashboard | Platform owns learner record; MiniBanking/Automation owns domain observations | Must retain provenance, assessment contract/version, execution outcome and completeness separately. A request/green report/import claim is insufficient. |

All track views MUST inherit [theme.css](../frontend/src/theme.css), [academy.css](../frontend/src/academy.css), [design MASTER](../design-system/data-qa-lab/MASTER.md) and shared React components. Use semantic page/surface/text/muted/brand/focus/status/code tokens in both themes; no domain-specific global theme, external font or icon dependency merely to differentiate a track. Track-specific authored decorative SVGs are allowed.

MUST retain Dark fallback/explicit `dqa-theme`, ENG fallback/explicit `dqa-language`, independent preference storage, native theme/language controls, document language, existing card/button/error/loading treatments, visible keyboard focus, 44px controls, readable responsive text, reduced motion and viewport-contained scrolling menus. Minimum acceptance widths 375/768/1280 in both languages/themes. Banking domain content currently VIE-only; author/review ENG before claiming bilingual integration. Do not iframe its `/learn/` page or import its CSS into the shell; its CSP forbids framing. No downgrade/redesign of existing Data QA pages.

## 3. Existing verified API boundaries

These endpoints **already exist** in platform [API source](../backend/app/api/__init__.py); there is no `/api/v1` namespace today.

| Endpoint family | Access/meaning |
|---|---|
| GET `/api/subjects`, `/api/courses`, `/api/courses/{course_id}` | Public localized catalog/course; executable_lab and tutorial metadata on develop. |
| GET `/api/lessons`, `/api/lessons/{lab_id}` | Public legacy executable content only, not hidden solution/scenario fields. |
| GET `/api/courses/{course_id}/tutorials/{lesson_id}` | Only `course_id=ai-test-automation` is supported. Public tutorial; available 200, planned 409, invalid/wrong-course 404; `language=ENG|VIE`, invalid language 422. |
| GET `/api/auth/me`, `/api/auth/config`, `/api/auth/demo` | Identity/public auth configuration/explicitly public demo listing. Never copy credential-bearing listing to architecture evidence or another service. |
| POST `/api/auth/signup`, `/api/auth/login`, `/api/auth/logout`, `/api/auth/password` | Existing intent/origin/CSRF/auth/rate/demo restrictions; public-shared password lock. |
| GET `/api/enrollments`, `/api/progress`; POST `/api/courses/{course_id}/enroll` | Private ownership; tutorial enrollment unavailable (409), executable progress unchanged. |
| GET/POST `/api/sessions`; GET `/api/sessions/{session_id}`, `/api/sessions/{session_id}/history/{kind}` | Private owner-scoped session/history; bounded paging. Tutorial IDs are not executable labs. |
| POST session `/query`, `/simulation`, `/submit`, `/hint`, `/reveal`, `/evidence-import`; GET `/evidence-export` | Existing bounded exercise semantics/reveal gate/read-only SQL/local mutation/evidence context. Do not broaden to banking SQL or code execution. |
| GET `/api/runs`, `/api/runs/{run_id}`, `/api/runs/{run_id}/quality`; POST `/api/runs`, `/api/runs/{run_id}/quality` | Owner scope; explicitly shared samples readable only; separate execution and DQ status. |
| GET/POST `/api/faults`; POST `/api/faults/{fault_id}/quality`, `/api/faults/{fault_id}/reset` | Existing controlled owner-scoped Data QA faults. Their existence does not authorize banking reset/fault endpoints. |
| GET `/api/health` | Platform DB readiness; no build SHA attestation. |

MiniBanking accepted [routers](https://github.com/taodo/MiniBanking/tree/2d7bf660611cbfe853489b9014f0453acbfcf1c8/backend/api) use **no `/api` prefix**:

| Method/path | Verified contract |
|---|---|
| GET `/health` | Startup/process readiness only. |
| POST `/auth/login` | Synthetic username/password → mock opaque access token/TTL; separately issued bank authentication. |
| GET `/accounts` | Bearer owner accounts; no pagination parameter. Seeded local practice has three accounts; future adapter must bound context size/response without claiming a general upstream list limit exists. |
| GET `/accounts/{account_id}/balance` | Owner-only; foreign/missing 404. |
| GET `/accounts/{account_id}/transactions?limit&offset` | Owner-only; limit 1–100/default20, offset 0–10000; ascending created_at + transfer_id; has_more. |
| POST `/transfers` | Bearer + exactly one bounded Idempotency-Key; strict from_account/to_account/positive integer amount. New201, replay200, auth401, unknown/inaccessible404, validation422, business/conflict409, contention503. |
| GET `/transfers/{transfer_id}` | Sender/recipient owner only; unrelated/missing404; no key/balance leak. |
| GET `/learn/` and static learning assets | Existing independent local UI; not a platform track route. |
| FastAPI default `/openapi.json`, `/docs`, `/redoc` | Source-default docs endpoints; not a public integration allowlist. Generated runtime OpenAPI was not fetched in U1. |

No Banking reset/seed/debug/fault SQL/shell/admin/logout/provisioning endpoint was found in the accepted app. Initialization, upgrades, fault/concurrency labs and SQL oracle are local/private CLI/test tooling, never public proxy targets. Automation has **no implemented HTTP endpoints**.

## 4. Proposed integration APIs and versioned artifacts

All rows below are **PROPOSED / NOT IMPLEMENTED**. Prefix `/api/integrations/v1/banking` is reserved for an explicit platform adapter, not a catch-all rewrite to MiniBanking. U2 implements none of these.

| Candidate platform method/path | Purpose / gate |
|---|---|
| GET `/api/integrations/v1/banking/capabilities` | Sanitized availability/content compatibility; no upstream addresses/tokens; off/unavailable must be explicit. |
| POST `/api/integrations/v1/banking/contexts` | Allocate a bounded authenticated synthetic context only after U5-approved ownership/provisioning/quota design; no reset of existing context. |
| GET `/api/integrations/v1/banking/contexts/{context_id}` | Owner/session-scope check before domain access; expiry/auth state metadata, no file paths or credentials. |
| GET context `/accounts`, `/accounts/{account_id}/balance`, `/accounts/{account_id}/transactions`; GET context `/transfers/{transfer_id}` | Fixed adapter operations with account/transfer authorization still enforced by domain; no user-supplied arbitrary upstream path/query/URL. |
| POST context `/transfers` | Platform CSRF + owner/scope + validated body; resolve separately scoped bank token internally; preserve domain amount/idempotency semantics, original key/body and UNKNOWN outcome. |

Context allocation is an unresolved control-plane requirement, **not** an existing MiniBanking endpoint. Domain and platform PRs must approve its lifecycle before adapter implementation/public writes. No generic HTTP proxy, arbitrary file/artifact-fetch URL, admin endpoint, bank SQL access or public `/execute` route. Upstream unavailable should yield a sanitized platform 503 or explicit capability-off state; preserve domain result/error distinction and never invent a banking rejection for a network failure.

Existing API policy: freeze current identifiers/semantics/URLs; additive optional metadata only. Existing language defaults stay compatible; frontend explicitly requests its saved language. Do not rename `/api/*`, silently drop referenced evidence, change `violation_count`, turn tutor status into lab completion or change bank 201/200 replay semantics. Breaking integration changes require a new major `/v2`, an explicit compatibility window, consumer tests, user approval and rollback. FastAPI application `version` is not sufficient wire-contract versioning.

**PROPOSED content/artifact envelope**, to be implemented after Automation bootstrap/domain approval:

```json
{
  "contract_version": "1.0",
  "producer_repository": "taodo/Automation-QA-Lab",
  "producer_commit": "<approved full Git SHA>",
  "framework_version": "<reviewed immutable release>",
  "content_version": "<reviewed content release>",
  "course_id": "ai-test-automation",
  "lesson_id": "m01-l01",
  "languages": ["ENG", "VIE"],
  "artifact_sha256": "<computed digest>",
  "evidence_kind": "LOCAL_OR_CI",
  "execution_status": "NOT_RUN",
  "assessment_status": "NOT_ASSESSED"
}
```

Placeholder envelope illustrates fields, not an actual published artifact. Producer must include schema/version, runtime/dependency lock/test command, expected assertions, actual timestamps/statuses when run, completeness/limitations and sanitized bounded results. Preserve separate content, framework, evidence schema and upstream API versions; full commits/digests pin identity but do not prove trust or correctness. Reviewed provenance/signing policy remains unresolved; arbitrary learner-imported metadata cannot claim trusted producer status.

First integration should be an explicit platform PR vendoring/referencing reviewed examples and localized content, not startup network synchronization or moving the existing manifest. Verify digest/schema/license/compatibility/size before acceptance. No extraction outside owned paths, executable hooks, raw HTML/scripts, tokens, passwords, idempotency keys or physical DB files. A nonzero exit caused by expected mutation is evidence of that scenario, not a universal framework failure; imported report PASS does not automatically grant completion. Third-party/provider dependencies require separate justification; no LLM API or paid-service requirement.

## 5. Route and track compatibility contract

PROPOSED stable track IDs: `data-qa`, `banking-qa`, `automation-qa`. They are not existing backend metadata. Route suffixes `data`, `banking`, `automation` map explicitly to them. Subjects/course IDs stay distinct; Banking course/challenge IDs must be domain-versioned, not forged into SQL `lab_*`. Existing Automation course `ai-test-automation` and lesson `m01-l01` remain platform presentation IDs.

| URL | Now (develop) | Target direct/refresh/history | Auth and legacy behavior |
|---|---|---|---|
| `/` | Data QA landing | U2 three-track homepage, SPA refresh and back/forward | Public; old deep links still work, Data CTA→`/learn/data`. |
| `/learn/data` | No implemented page; direct refresh404, client fallback loading | U2 exact Data landing; React + SPA allowlist | Public, reuse current Data QA landing and all nine course links. |
| `/learn/banking` | Not implemented | U2 exact informational landing | Public; capability/Planned labels, no simulator/session launch. |
| `/learn/automation` | Not implemented | U2 exact Automation landing | Public, link existing tutorial, no new runner/course copy. |
| `/learn/banking/simulator` | Not implemented | Future U6, only after isolation/security gates | Protected practice action; valid safeNext allowlist only when implemented. Off: explicit unavailable/NotFound, no redirect to raw bank UI. |
| `/learn/banking/challenges` | Not implemented | Future U3/U6 reviewed bilingual content/evidence UI | Public content; any persisted/private evidence protected separately. No viewing-completes semantics. |
| `/learn/automation/playground` | Not implemented | Future approved local/CI guidance first | Not a public code runner; unavailable until scoped. Auth policy depends on future persistence, not blanket SSO. |
| `/courses` | Public ten-course catalog | Preserve exact URL/reload/back/forward and `?q=` search | Public all-course catalog; nine executable stats plus tutorial distinction. Track filters can be additive, never hide saved course URLs. |
| `/subjects/{subject_id}` | Public ten subjects | Preserve matching/NotFound/reload/history | Subject ≠ track; Automation subject remains discoverable. |
| `/courses/{course_id}` | Public overview | Preserve IDs/routes/chapters or tutorial modules | No required new track prefix. |
| `/courses/{course_id}/lessons/{lab_id}` | AuthGate executable player | Preserve `?session=<UUID>` resume and `?new=1`, refresh/history | Preserve gate and existing safe return handling; no grading/history rewrite. |
| `/courses/ai-test-automation/tutorials/{lesson_id}` | Public tutorial player | Preserve exact route/reload/history; planned409→honest UI, invalid404 | Public; no enrollment/progress write. No auth redirect required. |
| `/my-learning`, `/history`, `/pipeline`, `/account` | Protected platform views | Preserve URL/reload/history/drafts | Existing login return validation; do not reinterpret old rows as new track events. |
| `/login`, `/signup` | Existing platform auth/Coming Soon in demo | Preserve safeNext and demo policy | Reject external/protocol-relative/encoded bypass returns; never accept arbitrary `/learn/*` prefix. |
| `/learn/{lab_id}` where `lab_id` matches `lab_*` | Legacy alias to SQL course, preserves query via replace | Keep alias ordering before generic NotFound and exact refresh allowlist | Existing behavior is specifically SQL alias, not a new universal track redirect. |
| Unknown `/learn/*`, missing API/assets | Loading client fallback / bounded server404 | Explicit NotFound; API/assets must retain real404 | No catch-all index rewrite or arbitrary redirect. |

Future protected paths must be added **exactly** to `safeNext` and tested for auth return, not accepted with an open prefix. For all implemented pages: deep GET refresh works, browser back/forward restores page/preferences, lost auth prompts re-login without discarding pending uncertain-operation evidence. Track creation changes presentation, not ownership of existing URLs.

## 6. Authentication, data isolation and threat analysis

Platform session and mock bank identity are different trust domains. Recommended future flow: validate platform principal/CSRF → authorize context (including shared-demo session scope) → select fixed upstream + context-owned bank role grant → use separately issued bank token → sanitize result. No platform token is sent to bank; no bank Bearer token/password reaches browser/localStorage/logs. Separate bank-role selection must be explicit to learners, not a claim that a platform account is a real bank customer.

| Threat | Required mitigation / approval gate |
|---|---|
| Confused deputy / token forwarding / forged X-DQA-Account | Never translate a claimed username/header into bank identity. Adapter derives platform owner from authenticated cookie and separately checks context grants. Bank verifier remains domain-owned. |
| Cross-learner bank state/IDOR | Owner check on every context/read/write/evidence lookup; unpredictable IDs are not authorization. Fresh SQLite/app scope per context is recommended. Shared A/B/C DB for all visitors is prohibited. |
| Shared public demo identities | A shared platform user is not one visitor. Either recorded-evidence-only mode or an additionally platform-session-bound ephemeral context; no other shared session can enumerate it. Named-account resume policy differs; approve separately. |
| CSRF / same-origin proxy bypass | Existing platform origin/intent/CSRF validation applies to all adapter writes; SameSite is not sufficient. Bank auth stays private; no broadened CORS/browser arbitrary upstream. |
| SSRF/path/header injection | Fixed configured upstream allowlist; validate IDs/bodies/paging; discard caller Authorization/Cookie/Forwarded headers. No redirect following to arbitrary upstreams or URLs. |
| Prototype/HTML/file import | Schema/size/depth/row bounds, text-only rendering, secret whitelist/redaction and immutable producer digests; do not execute/extract arbitrary content or accept learner-supplied truth. |
| Token expiry/restart/multi-worker routing | Bank tokens app-local; expire on restart. Sticky context ownership or explicit token renewal after authorization required. Do not share token caches with platform or promise HA without domain changes. |
| Timeout/UNKNOWN transfer | Preserve original key/body/context, pending operation and independent observations; never auto-new-key retry. Bank same-key/body replay/lookup plus state verification establishes outcome; network errors are not business rejections. |
| Integer/decimal mismatch | Bank VND integers up to signed64-bit; Data QA money NUMERIC/Decimal stays separate. Browser values beyond safe JS integer must be rejected or handled by reviewed lossless adapter contract before public release; do not silently round. |
| Rate/storage/CPU exhaustion | Bank login PBKDF2/context creation and SQLite writers need platform per-session/visitor/global budgets, finite requests, TTL/capacity, response limits and circuit breaking. Preserve existing demo caps; no unbounded file/process/context creation. |
| Unsafe API/CLI exposure | Deny reset/seed/upgrade/debug/fault/SQL/shell/metrics/raw docs/static file prefixes at public integration boundary. Local fault hooks remain runner-owned, not HTTP switches. |
| Public automation execution | Arbitrary Python/Playwright executes attacker code/network/browser. Local/CI first; later isolation, egress allowlists, no mounted secrets/host DB, CPU/memory/time/file quotas and cleanup threat review required. No public runner or third backend assumed. |

An ordinary synthetic shared role login alone does not solve tenancy. **UNRESOLVED gate D1:** approve context provisioning/lifecycle, shared-demo isolation, bank credential handling, routing/recovery and quotas before any public bank mutation. No existing API can securely allocate these contexts today. U1 defines alternatives; U2 stays informational, so secure integration is designed with a fail-closed boundary rather than invented SSO.

Progress MUST separate `execution_status`, `assessment_status`, `evidence_completeness`, `provenance`, curriculum/contract version and self-report. These names are proposed future fields, not existing PG columns or APIs. Keep existing executable completion rules unchanged. Anonymous reading, imported report PASS, UI checkbox and HTTP201 do not confer platform completion. No implicit localStorage account migration.

## 7. Configuration, releases and failures

Existing local/demo configuration is referenced in [Architecture deployment section](UNIFIED_PLATFORM_ARCHITECTURE.md#7-deployment-and-rollback). Retain separate learner PostgreSQL/demo PostgreSQL and SQLite, exact public host/trusted proxy/HTTPS/Secure-cookie/origin handling, operator-run Named Tunnel and all retained identities/budgets. Do not read or publish `.env`, tunnel tokens or account credentials. No preparation script against retained deployed data, reset/reseed/destructive migration, `docker compose down -v`, volume deletion or tunnel/DNS change.

Future local allocation candidates: platform existing ports subject to conflict checks; Banking private loopback candidate8002 with new owned synthetic state on D; Automation local/CI environments on D, no service port. Future public allocation: Banking only private network and platform adapter; no host-published banking or PG/SQLite endpoint, no raw `/learn/` mount. Any new settings/nets/images require reviewed implementation PR; this document creates none. Default integration capability off when configuration/upstream/version is missing.

Domain workflow: `feature/task-* → PR → Independent Review → User Approval → feature/develop`. Platform workflow: `Approved domain change → Integration contract review → Data QA feature branch → Integration PR → Independent Review → User Approval → feature/develop → Release gate → main → Deployment`. Each repository independently owns QA/release records; automation develop creation/bootstrap is a future approved domain task. Domain approval is not platform integration approval or deployment approval.

Cross-repository change notification / integration PR MUST include:

1. Producer repo, exact approved commit/base, release/package/API/content/evidence versions and domain review/approval reference; license and verified digests.
2. Contract/schema/endpoint changes, old/new sample payloads, error/replay/ownership behavior, consumer matrix and migration impact; no secrets/test DBs.
3. Domain actual QA evidence and limits, platform consumer contract tests, ENG/VIE/design review, prior URLs/36 lab + tutorial regression evidence and security review for auth/data/execution changes.
4. Explicit platform compatibility pin update; no floating main/latest or runtime fetch/merge. Integration PR cannot copy domain Git history/branches into platform.
5. Rollout capability-off defaults, capacity/retention/recovery decisions, data-preservation/backout plan, independently reviewed exact head and user approval.

Release gates: domain accepted release and unchanged approved SHA; adapter schema/version/negative/auth contract verification; full appropriate platform regression on exact final integration head; isolated bank fixture/API/SQL invariants; public host/proxy/CSRF tests; sanitized artifacts; user release approval. Documentation-only U1 requires references/routes/diff checks, no full local regression. Existing automatic CI may run, but no new workflow/deployment is introduced.

Failure/rollback contract: unavailable bank→sanitized unavailable state/503, disabled mutations, preserved pending operations/evidence and working Data QA/tutorial routes. Incompatible/missing Automation artifact→reject update, last approved static content stays. Failures are never blank pages, fabricated PASS or token leaks. Capability flags/version pins and their operator mechanism must be implemented/tested in a future PR before deployment; they do not exist by declaring them here. A release rollback restores compatible code/config only after approval, keeps all DBs/history, never silently resets practice state or deletes evidence. Context cleanup is permitted only for expressly disposable allocated objects with owner/lifetime records.
