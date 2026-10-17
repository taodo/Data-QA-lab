# U5-L local consumer: approval checkpoint

**Status: corrected offline contract checkpoint; live interoperability BLOCKED.**

Engineering objective: integrate the accepted private producer without changing
Data/Automation behavior or weakening session, financial, or recovery boundaries.
Learning objective: distinguish a producer artifact, an offline compatibility
check, an authenticated receipt, and independently observed financial evidence.
None implies a platform grade or Banking ON.

## Verified authority and source

- Platform base: `d48e9bf501c831502d90f5894e5d1b5531d0a2c5` on
  `feature/develop`; task branch `feature/u5-l-banking-private-consumer-bff`.
- Producer accepted merge: `970c5fa24092c08c4477b12ad40d45fc8e067b8b`,
  reviewed B4 head `71e8a7f0fae4dba6c0453c02fdb4793588f40b49`,
  B3 merge `d77ce49b6d4ba7303dd796d072f758c9f1086beb`.
- [Issue #51 implementation authorization](https://github.com/taodo/Data-QA-lab/issues/51#issuecomment-6232279132)
  permits LOCAL-ONLY work and explicitly says: **"If required joint signoff is
  still absent, stop at safe scaffolding and report BLOCKED rather than claim
  Banking ON."** It requires byte/error and
  operator PKI/secret custody/session/revocation decisions before live interop.
- [C1–C11](https://github.com/taodo/Data-QA-lab/issues/47#issuecomment-6195214592)
  approves the foundation design baseline, not final runtime interoperability.
- [B4 acceptance and merge](https://github.com/taodo/MiniBanking/issues/24#issuecomment-6232249252)
  is producer-only. The B4-only local verification waiver does not extend to U5-L.

The [platform-owner decision](https://github.com/taodo/Data-QA-lab/issues/51#issuecomment-6232857887)
approved J1–J6 with J4/J5 amendments. Independent security/operator signoff
remains pending. The [corrective specification](https://github.com/taodo/Data-QA-lab/issues/51#issuecomment-6233402825)
authorizes this offline correction only. Material J1/J4/J5 amendments below need
renewed explicit human acceptance before implementation; prior owner approval
must not be silently extended. AI-assisted review and SELF_REVIEW are not the
missing human security/operator approval or a local-only risk exception.
Historical U1/U5-P proposed routes are superseded only as stated by C1–C11 and
accepted producer contracts; they are not evidence of an implemented BFF.

## Delivered bounded scaffold

`tests/fixtures/banking_u5l_source_pins.json` records exact Git-blob SHA-256 hashes
and source paths for the accepted B3 and B4 V2 artifacts copied alongside it.
The existing B3 foundation fixture is retained unchanged. Offline tests check
canonical bytes/digest, signed64 precision counterexamples, the actual outer/inner
status matrix, and V2 evidence limitations. Hashes document source provenance;
they are not signed attestations or verification of a running producer.

No production module, schema, dependency, auth behavior, capability flag, BFF,
network configuration, Compose resource, or existing UI is changed by this slice.
It neither generates keys nor sends private traffic. Banking remains OFF. The
existing local release49 resources, `.env.release49`, public demo, retained
PostgreSQL data, and domain SQLite files are untouched.

## Local profile — owner baseline approved; corrective amendments await acceptance

The owner must accept the material corrective amendments, and an identifiable
independent human security/operator reviewer must sign off (or the owner must
explicitly approve a narrowly scoped local-only risk exception) on BOTH Issues
before live consumer traffic. J2/J3/J6 approved boundaries are preserved. No
runtime, dependency installation or private interop is authorized by this patch.

| ID | Proposed bounded local decision | Evidence and remaining approval |
|---|---|---|
| J1 — wire and errors | Preserve accepted B3 bytes and exact B4 V2 semantics. New transfer: `recovery=false`, dispatch once only after separate durable ACCEPT/SUBMIT. Consumer/signer/worker MUST NEVER emit `recovery=true`, `scope=recover`, or repeat transfer dispatch to resolve uncertainty. Reconciliation ONLY uses fixed `observe-operation` with original identity. Separate fixed reads with `key=null`; bind actor to server-owned context roster and authenticated platform session. No `/actor-token`. | Owner baseline approved; H2 corrective narrowing requires renewed acceptance. Source evidence and strict read/error profile below; all real wire tests NOT RUN. |
| J2 — local keys and transport | For the first bilateral test only, use runner-owned ephemeral P-256 signer keys and an independent ephemeral test CA with serverAuth/clientAuth certificates. Fixed server SAN `minibanking.internal`, client SAN `data-qa-lab-u5.internal`, chain + SAN + SHA-256 fingerprint verification both ways. Bind a dedicated producer to an OS-assigned loopback port; no redirects, proxies, browser URL/header forwarding or existing server reuse. Keys live only in a private owned temporary directory, have no source/artifact export, and are removed after owned processes close. | Platform owner approved this ephemeral test custody/topology; security/operator gate remains pending. Persistent operator keys, production PKI, rotation and release remain deferred; they cannot be inferred from a test pass. |
| J3 — signing dependency and claims | Reuse the accepted producer dependency families (`PyJWT>=2.9,<3.0`, `cryptography>=43,<47`) for ES256 only, subject to platform dependency approval and resolved-version evidence. Exact protected `alg/typ/kid`, pinned issuer/audience/subject/service, TTL30/skew5, fresh JTI, max4096 bytes; no external JOSE key URLs. Fixture issuer/identities are synthetic test values only. | Platform currently has neither dependency declared. No package is added in this branch. Owner approved these local dependency families; record compatible exact resolved versions when separately authorized to implement. |
| J4 — BFF and session boundary | Banking-only admission MUST reject server-derived `public_shared` principals even if enabled and authenticated. Require active authoritative session, its owned binding/context/actor, session CSRF, and configured exact Origin AND Host for mutations; deny missing/null/cross-origin and forged browser/proxy headers. Public/demo entry points remain OFF even with local headers/config. Non-browser tests use in-process ASGI with normal session/CSRF/Origin/Host, or an isolated test-only factory, never a runtime header/env bypass. Preserve shared auth and Data/Automation behavior. | Owner-amended baseline approved; explicit H3/Host correction awaits renewed acceptance. Future BFF acceptance examples are offline specifications, not executed BFF tests. |
| J5 — uncertainty, lifecycle and recovery | Fence new admissions first; for SUBMITTING/UNKNOWN attempt drain then bounded original-operation observe BEFORE revoke when safe/authorized. If expired/revoked/denied or drain/observation cannot finish, retain UNKNOWN/HELD and escalate; revocation must not wait indefinitely. No later 403 or missing observation settles money state. Worker uses narrow stored-binding service authorization, durable leases/fencing and pre-I/O attempts; sticky `ever_unknown`. Correlate ACK to one current outbox operation and independently verified producer fence; reject stale/late/duplicate ACK. See J5-01–J5-07 below. | Material correction requires renewed owner acceptance and separate security/operator gate. Sweep5s, connect2/read5/total8s; max3/5min and 10 lifetime apply ONLY to observation/reconciliation, NEVER money resubmission. Exhaustion retains UNKNOWN/HELD/outbox indefinitely until authorized disposition. No automatic eviction. |
| J6 — financial evidence | V2 SQL match is for declared disposable observations, not a signed domain receipt or consumer assessment. Source-owned independent read-only SQL must reconcile exact operation identities, one transfer/two sides/one reference and account deltas. U5 never opens domain SQLite or imports SQL evidence as progress. | Owner approved V2 interpretation; actual bilateral evidence remains required. Runtime strict response schema/sanitization, provenance and all seven crash windows must be exercised after authorization. |

## H1/H2/H3 verified against actual accepted source

Source inspection below is NOT a fresh producer test execution. MiniBanking links
pin accepted merge `970c5fa24092c08c4477b12ad40d45fc8e067b8b`; platform evidence
was inspected at pre-correction HEAD `bb5a4b69275ff8a58a424f3b39837eb1fe7644d3`.

| Finding | Confirmed bounded semantics / source and existing tests inspected |
|---|---|
| H1 | `observe` authorizes scope `observe` at [context_inventory.py:703](https://github.com/taodo/MiniBanking/blob/970c5fa24092c08c4477b12ad40d45fc8e067b8b/backend/context_inventory.py#L703); SignedGrantVerifier calls durable `consume` at [context_grants.py:300](https://github.com/taodo/MiniBanking/blob/970c5fa24092c08c4477b12ad40d45fc8e067b8b/backend/context_grants.py#L300), which rejects a revoked binding at lines137–139. Private revoke retires the binding at [private_transport.py:319](https://github.com/taodo/MiniBanking/blob/970c5fa24092c08c4477b12ad40d45fc8e067b8b/backend/private_transport.py#L319); ContextUnavailable maps to outer403 at lines372–373. Thus a fresh otherwise-valid observe grant after binding revocation is denied, not evidence of rollback. Existing `tests/test_private_transport.py:260–296` checks post-revoke status/dispatch denial, not a direct post-revoke observe; `:340–372` checks serialized admission/revoke fence, not writer cancellation. The observe consequence is established by the inspected call chain, not a newly executed TLS test. |
| H2 | [private_transport.py:336](https://github.com/taodo/MiniBanking/blob/970c5fa24092c08c4477b12ad40d45fc8e067b8b/backend/private_transport.py#L336) chooses `recover` for dispatch with recovery=true. [context_inventory.py:445](https://github.com/taodo/MiniBanking/blob/970c5fa24092c08c4477b12ad40d45fc8e067b8b/backend/context_inventory.py#L445) maps transfers.create to POST /transfers; line576 invokes runtime.request. `tests/test_b4_private_producer.py:154–206` explicitly recovers with nested201 when no earlier commit exists; `:372–394` recovers busy503 to new201. An identical request_id may return a stored receipt; a separately identified authorized recovery can reach the POST. This is an authenticated producer capability, not an unauthenticated exploit. Consumer reconciliation must prohibit it. |
| H3 | Platform [accounts.py:76–114](https://github.com/taodo/Data-QA-lab/blob/bb5a4b69275ff8a58a424f3b39837eb1fe7644d3/backend/app/accounts.py#L76) permits enabled shared-demo login/current_user and returns public_shared. Existing `tests/integration/test_public_demo.py:118–145` asserts successful shared login. Foundation `_session` at banking_foundation.py:93–106 also allows enabled shared accounts; it is NOT the future Banking-specific shared-demo denial. No Banking BFF exists yet, so this is a required admission correction, not evidence of a live public Banking exploit. |

### J1: immutable consumer request profiles

All signed Request fields and B3 canonical serialization remain unchanged. Digest
includes every Request field except digest: compact sorted `ensure_ascii=True`,
`allow_nan=False`, ASCII/UTF-8 SHA-256. Do not mutate frozen recovery/key/body to
construct reconciliation. Observation keeps the original Request; only a fresh
short-lived JTI/grant with scope `observe` is issued for its digest.

| Purpose | Fixed producer operation / payload | Key / scope / limits |
|---|---|---|
| New money acceptance | transfers.create; from_account, to_account, integer amount | Original frozen key; recovery=false, scope dispatch, at most one initial dispatch. No automatic or observation-triggered repeat. |
| Account list | accounts.list; empty payload | key=null, recovery=false, scope dispatch, independent read identity |
| Balance | accounts.balance; account_id | key=null, recovery=false, scope dispatch |
| History | accounts.history; account_id, limit, offset | key=null; strict integer limit1..100, offset0..10000; recovery=false, scope dispatch |
| Transfer lookup | transfers.lookup; transfer_id | key=null, recovery=false, scope dispatch |
| Reconcile original operation | POST fixed contexts/{ref}/observe-operation; original frozen Request | Original key/actor/binding/context/epoch/revision/request_id/operation_id/body/digest unchanged; scope observe, recovery=false; no dispatch/recover |

Read IDs are safe ASCII `[A-Za-z0-9._:-]{1,64}`; exact payload fields only. Actor
comes from the server-owned authorized context roster, scoped to the platform
session, never trusted free text or a replacement actor. Existing
`banking_foundation.canonical_request` remains transfer-acceptance-only: this
correction does not broaden it into a read or recovery dispatcher.

### J4: future BFF acceptance, not an implemented guard

Resolve public_shared from authoritative account/session storage, never a browser
claim. Deny shared-demo principals even on an otherwise valid local cookie session
and even when demo is enabled. A different session of the same ordinary owner
cannot seize a binding. Reject public/demo app entry points before admitting any
Banking action, regardless of loopback Host/Origin headers or local configuration;
a shared backing database must not weaken this check. Public proxies/Forwarded
headers and any test-only header/env flag confer no authority.

Browser mutations require configured exact Host (including port) AND Origin, not
values inferred from one another, plus normal session-bound CSRF. Missing/null
Origin is denied. Authenticated non-browser acceptance tests use ASGI and those
same controls, or an isolated test-only factory not selectable by runtime flags.
No exemption based on User-Agent, peer loopback, test header or forwarded Host.
Normal Data/Automation authentication remains unchanged. Actual BFF/PG/ASGI guard
and demo-enabled database tests remain NOT RUN until runtime is authorized.

### J5: future lifecycle, lease and ACK invariants

- **J5-01 — fence/order:** atomically fence admissions and retain immutable
  identities before auth-session removal. For SUBMITTING/UNKNOWN, persist a drain
  attempt, request bounded drain, then persist and attempt bounded original-only
  observation BEFORE revoke when still authorized. Security revocation is not
  delayed indefinitely. If unsafe/unavailable, persist UNKNOWN/HELD and escalation,
  then perform required revoke. Never pretend post-revoke observe can succeed.
- **J5-02 — observation budgets:** max3/5min, max10 lifetime applies only to
  observe/reconcile, never dispatch/transfer retry/new allocation. Persist attempts
  before I/O. Denials/timeouts consume bounded attempt/rate capacity but are NOT
  successful observations. WRITER_NOT_DRAINED, unknown operation, receipt or
  observation capacity, expiry/revoked403, exhaustion or missing evidence retain
  UNKNOWN/HELD and original references; no false NO_COMMIT or automatic eviction.
- **J5-03 — worker identity:** narrowly authorized service actor selected from a
  stored fenced binding/outbox, not a browser cookie, forged header, arbitrary
  context or resurrected user session. Permit only drain/observe/revoke for its
  immutable identity; never allocate/dispatch/recover. Real signer/transport still
  requires accepted local security configuration and independent signoff.
- **J5-04 — lease/fence:** short PG row lease with SKIP LOCKED, expiry, owner and
  monotonically increasing fencing generation; commit lease + attempt before I/O,
  release DB locks/transaction during I/O. Only current unexpired lease generation
  may persist response/ACK. Coalesce competing workers; no parallel cleanup or
  second money call. A crashed/expired lease may be reclaimed without discarding
  earlier attempts; stale worker completions cannot overwrite current records.
- **J5-05 — crash/uncertainty:** stale SUBMITTING after crash becomes UNKNOWN, not
  a redispatch task. Keep sticky ever_unknown audit even if later observations
  arrive; never erase provenance or replace the original result with a later
  rejection. Existing PG schema has no worker lease/fence/ever_unknown columns;
  these are future additive implementation requirements, not completed migration.
- **J5-06 — ACK correlation:** persist a single immutable outbox operation ID plus
  binding/context/epoch/revision, control-request identity, lease generation and
  pre-I/O attempt. Accept ACK only for that current pending request, matching
  original identity and independently verified producer revocation fence. Reject
  late/stale/duplicate ACK from advancing state or overwriting evidence. Duplicate
  completion must be harmless and never create a second completion/cleanup.
- **J5-07 — producer limit/retention:** accepted producer ACK body is only
  `{"revocation":"ACKNOWLEDGED"}`; it does NOT echo outbox identity or provide a
  signed financial receipt. Future consumer must correlate its authenticated mTLS
  response to the exact persisted signed control request and verify producer
  fencing semantics, not invent ACK fields. If required fence/correlation cannot
  be established, retain HELD/outbox and raise an explicit producer decision on
  Issue #24. ACK never settles financial uncertainty. Retain UNKNOWN/HELD/outbox
  indefinitely until authorized disposition, including after revoke or restore.

### Preserved J2/J3/J6 requirements

Future ephemeral key custody must verify restrictive owner-only Windows ACLs
before loading secrets and remove owned material only after owned processes close.
Verify the real TLS server hostname/SAN, trust chain and leaf fingerprint over
loopback, independently of the client identity pin; no proxy or redirect. Record
exact compatible resolved signer-library versions and exercise strict JWS/header,
clock/JTI negatives. Integer VND only; bilateral independent SQL remains
source-owned evidence, never a signed receipt, platform grade or absence proof.
These are future acceptance requirements, not executed runtime evidence here.

### Offline specification coverage versus live evidence

`tests/fixtures/banking_u5l_consumer_policy_v1.json` is an additive consumer-owned
policy and future acceptance matrix, NOT a changed producer fixture or operational
configuration. Preflight tests exercise that specification, the existing transfer
canonicalizer and a test-local illustrative BFF predicate. They do NOT run an
actual BFF/auth query, lease, worker, signer, socket, revocation or SQL reconciliation.
Source/test inspections above confirm bounded behavior; existing producer tests
were read, NOT re-executed. All live acceptance criteria remain NOT RUN.

### Pinned source error mapping for the later consumer

| Producer response | Consumer interpretation required by the proposal |
|---|---|
| outer200 / nested201 | New bank result observed; financial proof separate. |
| outer200 / nested200, or stored receipt with original nested201 | Replay/stored evidence; inspect `stored`, preserve original result and identity; no additional posting claim without SQL. |
| outer200 / nested409,404,422 | Domain rejection/visibility/validation observation; cannot erase earlier UNKNOWN. |
| outer200 / nested401,500,503 | Authentication/infrastructure uncertainty; retain original identity and hold. |
| outer202 or lost response after SUBMIT | UNKNOWN; timeout does not cancel a writer. |
| outer400,403,404,503 | Private envelope/authorization/route/unavailability error; keep UNKNOWN/HELD, never infer no historic commit. Unknown-operation/capacity/revoked denials map to generic outer403 private_request_denied, not new public reason codes. |
| observe outer200 / INCONCLUSIVE, WRITER_NOT_DRAINED | Writer may still commit; no settlement or successful conclusive observation. Observation/receipt exhaustion similarly preserves holds; no false absence proof. |
| outer401,422,429 | Not emitted by the accepted producer. Treat unexpected responses conservatively, not as newly approved wire behavior. |

Browser money remains canonical ASCII decimal strings, converted losslessly to
signed64 integers. A representable amount is still subject to the independent
domain business limit. Reject duplicate keys, floats, booleans, NaN, overflow,
malformed/oversize responses and unexpected fields; never expose raw producer
logs, grants, private keys, internal paths, cookies or domain credentials.

## Verification and continuation gate

Focused command (offline, no database/network):

```powershell
D:/Data-QA-Lab/.venv/Scripts/python.exe -m unittest tests.unit.test_banking_u5l_preflight tests.unit.test_banking_foundation -v
```

Actual results and exact final HEAD belong in Issue #51, not a document containing
its own future commit SHA. Final platform regression follows the existing
[verification strategy](UNIFIED_PLATFORM_TEST_STRATEGY.md#1-evidence-and-execution-policy):
exact-HEAD CI may cover full platform validation; do not duplicate it locally.
No skipped job, prior-head success, source-only SQL report, or offline fixture
constitutes live U5-L acceptance.

**Remaining implementation, all NOT RUN:** real signer/mTLS client, local-only
BFF and route authorization, durable I/O/response state integration, scheduled
expiry/outbox delivery and ACK, source/platform seven-window recovery, strict
browser response projections, actual private HTTP and independent source SQL.

After renewed owner acceptance of material J1/J4/J5 amendments and the separate
human security/operator approval (or explicit scoped owner risk exception) on BOTH
Issues, obtain runtime continuation authorization on this same branch. Run focused
tests first, then one required final regression on committed HEAD. Recheck both source/base pins and refresh affected evidence. Do not enable
public Banking, merge, deploy, or start U6. Until then the task is **BLOCKED**, not
READY_FOR_REVIEW or implementation-complete. Request independent review of this
checkpoint and the proposed decisions.
