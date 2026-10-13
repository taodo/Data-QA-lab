# Banking integration decision checklist — U5-P

Status: **AMENDED PROPOSAL / NOT IMPLEMENTED**. D1–D7 have
`USER_APPROVED_DIRECTION`; residual contract items remain `CONTRACT_PENDING`; all
runtime work remains `IMPLEMENTATION_NOT_AUTHORIZED`. A checked direction is not
an implementation, pilot, release or deployment approval. References:
[Decisions](BANKING_ARCHITECTURE_DECISIONS_PROPOSED.md),
[BIC candidate contract](BANKING_CROSS_REPO_IMPLEMENTATION_CONTRACT.md),
[authoritative UPIC-1.0](UNIFIED_PLATFORM_INTEGRATION_CONTRACT.md).
Only these three existing U5-P documents are amended; B2/U5 runtime work needs a new
explicit user instruction and independent review in each owning repository.

## 1. Joint decision status and residual approvals

Record decision, reviewer, approval date, exact contract revision and remaining
scope restrictions in both projects before coding. Merge approval for a domain
implementation is not platform integration/release approval.

| ID | State | Approved direction | Residual owner / dependency / closure evidence |
|---|---|---|---|
| D1 | USER_APPROVED_DIRECTION / CONTRACT_PENDING | Option A, app/engine/auth/SQLite per context; bounded domain manager + platform registry; B2 isolation interface separated from B3 production mTLS+ES256 trust | Joint architecture/security/operations; approve library, PKI/certificate/signing-key custody, TLS termination, issuer/audience/typ/alg profile, rotation/revocation/replay and cross-repo vectors. No implementation authorization. |
| D2 | USER_APPROVED_DIRECTION | Shared demo bound to individual authenticated session; anonymous recorded/read-only; named resume/rebind disabled for MVP | Platform product/security + domain grant owner; two-sessions/one-username negatives and orphan-hold access. Any future rebind is a new contract decision. |
| D3 | USER_APPROVED_DIRECTION / CONTRACT_PENDING | Domain-owned unique synthetic secrets/private login broker; server-memory token cache by context+epoch+actor+incarnation+authorization revision | Domain auth + platform adapter; credential custody/rotation, operator access, expiry/revocation acknowledgement and redacted negative evidence. |
| D4 | USER_APPROVED_DIRECTION / CONTRACT_PENDING | Configurable pilot budgets/TTL/retention and durable allocation+intent protocol; caps cannot evict UNKNOWN/referenced state | Owners/phases are assigned in Decisions; operations approves actual values only after enforcement tests, while B5 measures capacity before public release. |
| D5 | USER_APPROVED_DIRECTION / CONTRACT_PENDING | Durable ACCEPT then explicit SUBMIT, frozen identity, conservative UNKNOWN, read-only recovery after expiry/drain | Domain recovery + platform registry + operator; approve NO_COMMIT_PROVEN authority, receipt/oracle evidence, restore checkpoints and retained-state disposition after crash matrix tests. |
| D6 | USER_APPROVED_DIRECTION / CONTRACT_PENDING | Canonical decimal-string BFF money with exact signed64-bit domain integers; preserve Data QA SQL Decimal | Joint API/UI; approve schema revision and positive/negative/2^53/max-int/overflow producer-consumer vectors before implementation. |
| D7 | USER_APPROVED_DIRECTION / CONTRACT_PENDING | Defer assessed learning progress/grading; retain eight challenge IDs and honest LIVE/RECORDED/IMPORTED provenance | Curriculum/privacy owners; later U3/U7/U9 approval for rubric, provenance, evidence access/retention and assessment. HTTP2xx/localStorage never imply PASS. |

Security decisions needing **joint approval**, not implementation guesswork:

- [ ] Private TLS peer identity, grant algorithm/keys/expiry/replay/revocation and
  authorization-revision acknowledgement; trusted-service compromise response.
- [ ] Shared-demo session isolation, named rebind/cross-session policy and
  narrowly authorized recovery after logout/expiry; no bank/platform identity equivalence.
- [ ] Immutable intent acceptance/submission and orphan/UNKNOWN recovery, including
  who can prove no commit, hold/close a context or approve retained-file disposition.
- [ ] Context storage root/ownership/fences/Windows handle closure, backup checkpoints,
  restore epoch fencing and capacity exhaustion without deleting unknown evidence.
- [ ] Lossless amount/balance schemas, upstream status/source validation, request limits,
  SSRF/header/redirect denial and secret-safe logs/artifacts.
- [ ] Separate runtime/privacy/evidence/rubric/progress gates and proposed UPIC deltas
  P1–P7; no silent approval of a public release or new APIs.

## 2. Proposed defaults and assumptions

Authoritative numeric table: [D4 in Decisions](BANKING_ARCHITECTURE_DECISIONS_PROPOSED.md#d4--conservative-bounds-and-durable-intent).
Every following value is **PROPOSED DEFAULT / NOT MEASURED PRODUCTION CAPACITY**:

| Group | Initial proposed limit |
|---|---|
| Context count / creation | 1 active/session,3/user,20/global;100 total including holds; creation1/session/5min,2/user/10min,6/global/min |
| Provision / request concurrency | 2 provisioning workers,queue4/wait2s/deadline30s;4 requests/context,16/global,1 financial dispatch/context; request queue2/context,32/global/wait200ms |
| Rates / attempts |30 requests/session/min;6 transfer submits/session/min;3 attempts/intent/5min and10 lifetime; no automatic transfer retry |
| Lifetimes / drain |30min idle,4h absolute,15s drain deadline followed by hold if not actually drained |
| Storage / evidence |16MiB/context DB+sidecars;2GiB domain total;2MiB sanitized evidence/context;100 intents+500 observations/context; platform registry10000 operations/64MiB, smaller existing demo caps prevail |
| Retention |>=7 days after context closure/operation settlement;30 days sanitized evidence/audit;UNKNOWN no automatic deletion, alert after24h; no deletion while references/holds require retention |
| HTTP / auth |16KiB requests,256KiB responses,100 account rows; connect2s/read5s/total8s, SQLite wait1000ms; actor tokens300s/capacity8/context,2 login attempts/actor/min; grants30s/skew5s/4096 bytes |

Assumptions to validate: trusted domain/platform code; synthetic data only; local
SQLite filesystem; one dispatcher owner; secret storage and TLS keys outside Git;
fixed private address; bounded initial actors/accounts; authentic seed only into
new manager-owned state. Existing standalone bank auth/transfer defaults and
history limits remain facts, not capacity measurements or changed settings here.
PBKDF2 costs, SQL contention, file/engine memory, disk reservations, response size
and retention pressure must be measured by B5. Exceeding budgets returns explicit
429/503/error/INCOMPLETE; never eviction, rounding or silent evidence truncation.

The complete per-value owner/phase/exhaustion/gate classification is normative in
[the D4 enforcement matrix](BANKING_ARCHITECTURE_DECISIONS_PROPOSED.md#d4-enforcement-ownership-and-phase-matrix).
Its ownership groups are:

| Enforcement group | Values owned | Earliest implementation phase | Full-capacity rule |
|---|---|---|---|
| Platform registry/BFF | Per-session/user context and creation budgets; request/submit/attempt rates;10000-operation/64MiB registry; platform intent/evidence portions | U5 | Fail before dispatch; retain references and UNKNOWN;429 for caller budgets,503 for unavailable durable capacity |
| MiniBanking dispatcher/inventory |20 active/100 inventory; provisioning/request/queue/write concurrency; context TTL/drain;16MiB/context+2GiB total; actor token scope | B2 essential, with B3 transport/auth bounds | Stop allocation/admission, alert and hold. Never delete/evict retained or UNKNOWN state to recover capacity |
| Joint producer/consumer boundary | HTTP sizes/account rows/history forwarding/timeouts; grant TTL/skew/size; operation/observation/evidence references | B3 + U5/U6 | Reject or contract-error without truncation; possible prior admission remains UNKNOWN |
| Operations/release |>=7d resolved retention,30d evidence/audit,24h UNKNOWN alert; final numeric tuning | Policy before pilot, B5 measurement before public release | Non-destructive reconciliation and dual-owner disposition only; retained Data QA and non-manager bank data are excluded from cleanup |

## 3. Dependencies and exact future implementation boundaries

All scopes below are **PROPOSED future Codex tasks requiring separate approval**.
Each starts from its own latest accepted develop, preserves work/data, uses its
own feature branch/PR, runs focused tests then required final exact-head checks,
and stops for independent review/user approval. No cross-repository Git merges.

| Future task / repository | Dependencies | Allowed implementation / mandatory deliverable | Explicit exclusions |
|---|---|---|---|
| B2 — MiniBanking context isolation | Reviewed amendment + separate authoritative B2 Issue + explicit user approval; B1 accepted | Domain-owned durable inventory, fresh SQLite/app/auth scopes, bounded allocation/dispatch/lifecycle/drain/restart/owned cleanup, durable admission receipts and a fail-closed grant-verifier interface. Deterministic authorizer is test-only/non-deployable; capability OFF; producer isolation/recovery/negative tests | Production mTLS/JWS verifier, live platform/domain traffic, platform PG/identity/UI/progress, tenant schema redesign/pool optimization, retained DB init/reset, public controls/deploy |
| B3 — MiniBanking private API hardening | Accepted B2 interface; U5 signer/contract agreement; approved security profile and D6 vectors | Production private transport identity, mTLS termination, strict ES256 JWS verifier, certificate/key custody/rotation/revocation/replay, capability/version/readiness and request/resource/error/log bounds | Public bank port/docs/static proxy, shared HMAC/network-only trust, SSO, new banking features, unapproved infrastructure/deployment changes |
| B4 — MiniBanking producer verification | Accepted B2/B3 + approved BIC vectors | Real private HTTP producer tests, independent read-only ledger/SQL oracle, context/UNKNOWN/string-money boundaries, sanitized pinned evidence; retain required existing Task9/HIGH gates | Using posting service as expected truth, public SQL/fault APIs, progress grading, retained DB queries |
| B5 — MiniBanking operational readiness | B2–B4 accepted; compatible U5/U6 pilot; decisions closed for release slice | Disposable-state measured capacity/drain/restart/backup/restore/outage/private-network rehearsal; exact-pin release/rollback runbook and local/public verdicts | Public tunnel/deploy, retained-data rehearsal, automatic main merge or test-gate waiver |
| U5 — Data QA registry/security foundation | Reviewed amendment + separate authoritative U5 Issue/user approval; fixed B2/B3 fixtures allowed before producer acceptance | Platform user/session binding/grants, durable allocation intents/operation records, quotas/CSRF/authorization, pending crash/recovery holds, producer compatibility checks; separately reviewed additive preservation-safe migration only if needed; real dispatch OFF until accepted B2/B3 | Banking posting/SQL/seed, simulator redesign, tutorial/Data QA grading changes, shared SSO/progress/D7 features/deploy |
| U6 — Data QA BFF and simulator | Accepted U5+B2/B3; B4 producer evidence and joint vectors | Fixed adapter, string money/status mappings, actual consumer contract tests, secure existing-shell UI with ENG/VIE/theme/375–1280/a11y/recovery browser E2E | Generic proxy/direct bank browser calls, credentials or arbitrary URLs, domain business logic, public unsafe controls/automatic rollout |
| U3/U7 — content and assessment | D7 + approved domain content/provenance; live parts require U6 | Eight stable challenge mappings, reviewed bilingual content/rubrics/independent expected evidence, honest recorded/imported/live status | Import PASS as truth, localStorage credit, AI/free-text semantic grading or automatic completion |
| U9 — progress | Explicit D7 assessment/privacy approval, accepted U7 semantics | Additive platform-owned progress/evidence experience with separate self-report/execution/assessment/completeness and legacy preservation | Bank user/database migration, reading/API2xx completion, existing course/history rewrite |

Ordering avoids a circular dependency: agree the contract first; U5 registry code
may use pinned producer fixtures with capability OFF in parallel with B2/B3, but
must not claim live verification until an accepted compatible producer exists.
B2/B4 producer tests can use the non-deployable deterministic authorizer before
production trust exists; U6 adds actual BFF
consumer tests. Both must pass before a live pilot. B5 rehearses the accepted
pilot; platform U10/user-approved release gate remains separate. No runtime work
or domain notification is sent by U5-P.

## 4. Producer and consumer verification gates

| Gate | MiniBanking must demonstrate | Data QA must demonstrate |
|---|---|---|
| Ownership/private trust | mTLS/grant epoch/actor/scope negatives; same IDs/keys in two files never cross; path/junction/lease/cleanup safety | Different sessions sharing demo username cannot list/read/write/history/status/retry/evidence; spoofed headers/grants/cookies fail; auth/CSRF retained |
| Durable acceptance | Allocation/request receipts survive crash/restart; fresh same-actor login; missing file/schema quarantined | Intent saved before posting; lost acceptance/BFF response/refresh/double click maps once; same intent changed context/actor/body409; no key replacement |
| Financial independence |1 transfer/2 correct ledger sides/1 reference; exact account deltas, opening+net, FK/conservation; no partial rejection effects | Validate seven-field result/pins and source/outcome, no HTTP2xx assessment claim; typed malformed/oversize/upstream error mapping |
| UNKNOWN / restoration | Full response-loss/401/500/503/in-flight drain; read-only expiry observer; old snapshot/epoch fences retry; controlled defect detectors | Preserve earlier UNKNOWN despite later rejection/probe; no automatic retry/new context; offline registry fail closed; operator recovery stays separate |
| Precision/limits | Strict integer domain boundaries/overflow and producer response validation; rate/token/queue/storage exhaustion | Canonical strings across nested results at2^53 and max-int; reject numeric/bool/scientific/leading-zero input before dispatch; no truncation/SSRF/redirect |
| Evidence/release | Sanitized actual HTTP+SQL provenance/versioned fixture evidence; normal and controlled-defect results separate; independent domain HIGH review | ENG/VIE/theme/a11y/browser recovery, existing36 executable labs + tutorial/legacy/auth/history regressions; approved producer pins and independent integration review |

Test plans must include explicit commit/base/version, commands, execution status,
results and NOT RUN limitations. Windows handles/actual private TCP/container
rehearsal are distinct from ASGI source/test inspection. Green CI or domain review
does not substitute for consumer failures, security approval or release approval.

## 5. Go/no-go gates

### B2 readiness verdict

- `READY_FOR_ISSUE_DRAFT = YES`: the amended documents define B2's isolated
  runtime, deny-all grant-verifier interface, non-deployable test authorizer,
  durable admission receipts, essential resource bounds and crash-window tests.
- `READY_FOR_IMPLEMENTATION = NO`: implementation requires this amendment to be
  independently reviewed/merged, then a separate authoritative MiniBanking B2
  Issue with exact scope, acceptance tests and explicit user approval.
- `LIVE_INTEGRATION = OFF`: a merged B2 cannot carry real platform traffic. B3
  production trust and accepted U5/U6 producer-consumer gates are prerequisites.

This verdict permits drafting the B2 Issue only. It does not create that Issue,
notify/modify MiniBanking, authorize code, or approve a local/public pilot.

### Local pilot — CONDITIONAL, not authorized by U5-P

- [ ] D1–D6 jointly signed; D7 deferred/no-progress boundary explicitly approved.
- [ ] Accepted compatible B2/B3/B4 and U5/U6 exact heads, producer/consumer negative
  tests, fresh disposable owned context root and independent SQL evidence.
- [ ] Explicit operator-approved loopback port/root/private transport/key custody;
  no retained bank/demo files, no initialization of existing learner data.
- [ ] Lost response, session expiry, UNKNOWN drain/restart and feature-off recovery
  verified; numeric admission bounds configured with honest capacity limits.
- [ ] Documented rollback/read-only recovery, no new-key/context substitute and
  no public exposure. Approval names/time and pilot scope recorded.

Any missing item means **NO-GO** for live integration; reviewed recorded content
can remain available under its own scope. Existing domain standalone practice is
not proof an integrated pilot has passed.

### Public live demo — BLOCKED until a separate release decision

- [ ] All local gates plus B5 measured mixed-session capacity/storage/TTL/drain/
  backup/restore/outage evidence and independent security review.
- [ ] Actual private-only bank service, no public docs/SQL/reset/seed/fault/admin/
  SQLite endpoint; platform HTTPS/proxy/CSRF/demo policies preserved.
- [ ] Cross-visitor isolation and orphan/rebind rules validated under retained
  shared-demo identities; no account provisioning/reset on retained data.
- [ ] Exact compatible release pins, capability-off default, operator key/revocation/
  alert/retention/runbooks and safe read-only recovery during rollback.
- [ ] ENG/VIE/shared Task20/20.1 UI, accessible mobile and unchanged courses/history;
  D7 provenance/assessment gates closed for any claimed learning completion.
- [ ] Separate platform U10/release review, explicit user approval for main and
  deployment. Develop merge, architecture approval and domain CI are insufficient.

Never `docker compose down -v`, reset/reseed, expose raw services or modify tunnel
credentials to satisfy a gate. No release commands or public access are run here.

## 6. U5-P documentation verification checkpoint

Confirmed amendment base: platform `origin/feature/develop` at
`8b5e6336ff1123dbf2e447114b7a47d815cc8bef`, containing U5-P PR #36 merge
`fecd1671101c846fb6cd99d6c746925b9988b848`, C1 and U2. Domain accepted
baseline remains `7a77ec579d7ff0edf2299d3755155573fee1ec15`. Final amendment HEAD,
remote and PR are reported in handoff rather than embedding a self-referential SHA.
Git diff must modify exactly:

1. `docs/BANKING_ARCHITECTURE_DECISIONS_PROPOSED.md`
2. `docs/BANKING_CROSS_REPO_IMPLEMENTATION_CONTRACT.md`
3. `docs/BANKING_INTEGRATION_DECISION_CHECKLIST.md`

EXECUTED audit: clean Git/remote/base checks and platform fetch; read Issue #37,
all current comments, accepted U5-P/U1 documents, PR #36 metadata, and MiniBanking
B1 documents/source at the exact remote branch SHA through authenticated read-only
GitHub access. Current `main.py`, Settings, AuthService and TransferService confirm
one DB/app/token store and no context manager/grant verifier/domain receipt/BFF.
No MiniBanking write/fetch/branch operation occurred. Production/main/deployed
state is not inferred.

Validation commands (PowerShell from `D:\Data-QA-Lab`, no runtime/database action):

```powershell
git status --short --branch
git fetch origin
git rev-parse origin/feature/develop
git diff --check origin/feature/develop
git diff --name-status origin/feature/develop
rg -n "USER_APPROVED_DIRECTION|CONTRACT_PENDING|IMPLEMENTATION_NOT_AUTHORIZED|READY_FOR_ISSUE_DRAFT|READY_FOR_IMPLEMENTATION" docs -g "BANKING_*.md"
```

The ignored, temporary amendment checker verified Markdown fence/table structure,
local links/anchors, D1–D7/status/readiness terms, exact baseline pins, preserved
numeric proposals and three-document-only scope. It was removed after execution;
the command is provenance, not a committed runtime tool. No runtime assertion is
derived from static checks. After commit also check committed diff whitespace,
remote SHA and clean tree.

Observed lightweight check: **PASS** — 3 documents,23 tables,15 local links,
2 local anchors,13 required amendment terms,24 preserved limit tokens and exactly
the three authorized changed files; zero errors. `git diff --check` passes.

Manual eight-reference consistency review:

| Reference | Retained requirement / explicit proposal delta |
|---|---|
| U1 Architecture | Two services/independent databases, platform shell ownership, no public unsafe bank surface; newer bank merge provenance supersedes historical Task9 status only |
| UPIC-1.0 | Authoritative proposed boundary/namespace/auth/evidence/compatibility kept; P1–P7 deltas enumerated instead of editing approval status |
| U1 Roadmap | Separate domain tasks/U5 registry/U6 adapter/U7–U9 progress/U10 release; no automatic rollout or Automation framework work |
| U1 Test Strategy | Independent SQL truth,36 labs/tutorial/legacy/auth regressions, shared UI/ENG-VIE/theme and exact-head independent producer/consumer gates |
| B1 Readiness Audit | Existing seven application APIs/types/errors and eight challenges source-checked; integration manager/BFF remain missing, public BLOCKED |
| B1 Isolation Design | Option A/files+apps+auth with grants, session-demo binding, epochs/fences/owned cleanup; numeric/private identity choices now explicit proposals |
| B1 Companion Contract | Fixed mappings/domain integers/private credentials, UNKNOWN preservation; two-phase writer and string-money schemas are proposed joint deltas |
| B1 Roadmap | B2 lifecycle, B3 hardening, B4 independent producer proof, B5 operations; platform work remains separately authorized |

NOT RUN: pytest/Newman/full-suite/build/browser, bank server/runtime OpenAPI,
SQLite/PostgreSQL reads/writes/init/reset, capacity/restore rehearsal, public-domain
requests, deployment/main/tunnel operations. Existing automatic CI may run on the
documentation PR; it is not a requirement to duplicate full runtime suites locally.
No code, schemas, settings, dependencies, secrets, domain repositories, retained
accounts/history or production infrastructure are modified. Stop for independent
architecture review; do not merge or begin B2/U5/U6.
