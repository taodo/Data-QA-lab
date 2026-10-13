# Banking cross-repository implementation contract — U5-P

Status: **AMENDED PROPOSAL / NOT IMPLEMENTED**. Candidate identifier
`BIC-1.1-proposed`; D1–D7 are `USER_APPROVED_DIRECTION`, while every runtime
capability is `IMPLEMENTATION_NOT_AUTHORIZED` and the residual decisions below
are `CONTRACT_PENDING`. This document does not activate or publish a contract;
no endpoint, schema field, capability, migration or service below is implemented
by this document. Producer: MiniBanking private integration boundary. Consumer:
Data QA Lab Banking BFF. See [D1–D7 decisions](BANKING_ARCHITECTURE_DECISIONS_PROPOSED.md)
and [approval/implementation gates](BANKING_INTEGRATION_DECISION_CHECKLIST.md).
UPIC-1.0 remains authoritative until joint review explicitly accepts its deltas.

## 1. Existing verified contracts and ownership

Source pins: current platform integration base
`8b5e6336ff1123dbf2e447114b7a47d815cc8bef` (including U5-P merge
`fecd1671101c846fb6cd99d6c746925b9988b848`), MiniBanking B1
`7a77ec579d7ff0edf2299d3755155573fee1ec15`; merge provenance in Decisions.
This inventory was checked against accepted source, not runtime OpenAPI.

| EXISTING MiniBanking method/path | Verified request/result | Source |
|---|---|---|
| GET `/health` | 200 `status=ok`; process/startup only, no ongoing DB/version attestation | [main.py](https://github.com/taodo/MiniBanking/blob/7a77ec579d7ff0edf2299d3755155573fee1ec15/backend/main.py) |
| POST `/auth/login` | strict username1–64/password1–256, no extras; 200 token/bearer/expires_in; invalid401 | [auth router](https://github.com/taodo/MiniBanking/blob/7a77ec579d7ff0edf2299d3755155573fee1ec15/backend/api/auth.py), [schemas](https://github.com/taodo/MiniBanking/blob/7a77ec579d7ff0edf2299d3755155573fee1ec15/backend/schemas/__init__.py) |
| GET `/accounts` | bearer-owner accounts; integer VND balances; no current row/paging cap | [accounts router](https://github.com/taodo/MiniBanking/blob/7a77ec579d7ff0edf2299d3755155573fee1ec15/backend/api/accounts.py) |
| GET `/accounts/{account_id}/balance` | owner only; foreign/missing404 | accounts router |
| GET `/accounts/{account_id}/transactions` | limit1–100/default20, offset0–10000/default0; ascending created_at+transfer_id, direction and has_more | accounts router, [service](https://github.com/taodo/MiniBanking/blob/7a77ec579d7ff0edf2299d3755155573fee1ec15/backend/services/transfers.py) |
| POST `/transfers` | strict from/to1–64, amount integer1..2^63−1; exactly one ASCII key `[A-Za-z0-9._:-]{1,128}`; new201/replay200 | [transfers router](https://github.com/taodo/MiniBanking/blob/7a77ec579d7ff0edf2299d3755155573fee1ec15/backend/api/transfers.py), [schemas](https://github.com/taodo/MiniBanking/blob/7a77ec579d7ff0edf2299d3755155573fee1ec15/backend/schemas/transfers.py) |
| GET `/transfers/{transfer_id}` | sender/recipient owner; unrelated/missing404; seven-field Transfer result, aware UTC time | transfers router/service |

Existing errors: `error.code/message` or sanitized validation `detail` loc/msg/type;
401,404,422,409 business/conflict,503 database_busy,500 database_error. Source
same-account422; funds/limit/overflow/conflicting body409. No rejected FAILED row
is stored; only committed SUCCESS. Offset history is not a consistent snapshot
during inserts. Existing `/learn/` assets and FastAPI docs/OpenAPI exist, but are
**not** integration targets. No allocation/status/revoke/readiness/intent API exists.

| Authority | Owns | Must not own |
|---|---|---|
| MiniBanking B2–B5 | Domain rules, actors/credentials, SQLite/apps/tokens, private manager/inventory/receipts, financial observation/oracle, lifecycle | Platform accounts/cookies/CSRF, React shell, platform progress or PG administration |
| Data QA U5 | Platform session binding/registry/grants, durable allocation intents and operation identities, quotas, compatible producer pins | Posting/ledger rules, bank credentials creation, direct bank SQL/CLI execution |
| Data QA U6 | Fixed BFF mapping, same-origin simulator UI, typed errors/string money, ENG/VIE/theme/a11y/browser QA | Generic HTTP proxy, second banking shell, live privileged controls |
| U3/U7/U9 + domain content owner | Reviewed versioned challenges/rubrics, evidence trust and platform learning records | HTTP/localStorage→automatic completion or changed existing lab truth |

The domain inventory is a PROPOSED transactional private lifecycle catalog,
separate from financial context files; platform registry is future additive PG
storage. Neither exists in the current schemas. Their approval/migrations belong
to independent B2 and U5 tasks, with preservation/rollback review first.

## 2. PROPOSED browser/BFF endpoint inventory

Candidate public prefix **P = `/api/integrations/v1/banking`**. Every row is
PROPOSED; public browser calls only P, never MiniBanking. Authenticated reads
also enforce session/context/actor ownership. All mutations use current platform
writer/CSRF/origin controls and approved JSON intent policy, never disable them.

| PROPOSED method/path | Exact purpose / behavior |
|---|---|
| GET P`/capabilities` | Sanitized OFF/UNAVAILABLE/AVAILABLE and accepted contract/content capabilities; public discovery may see no owner data. Health alone cannot set AVAILABLE. |
| POST P`/contexts` | `{allocation_intent_id:UUID}` only; atomically reserve binding budget/map before private provisioning. New ready201, same intent200, pending202, changed scope409. No caller fixture/path/URL/epoch. |
| GET P`/contexts` | Current authorized binding's contexts only; no shared-username cross-session list. |
| GET P`/contexts/{context_id}` | Sanitized status/expiry/authorized actor choices/pending counts and opaque storage scope tag. No domain reference/path/epoch credential. |
| GET context `/accounts`, `/accounts/{account_id}/balance`, `/accounts/{account_id}/transactions` | Fixed domain reads with required granted actor_id selector; bounded path. Only history limit/offset is forwarded to domain, never actor_id. Owner/actor checks first. |
| GET context `/transfers/{transfer_id}` | Required granted actor_id selector; fixed lookup and preserved domain participant rule. |
| POST context `/operations` | Accept/freeze transfer intent, persist, **no upstream transfer**; 201 acceptance or200 same intent; mismatch409. |
| GET P`/operations/by-intent/{client_intent_id}` | Recover lost acceptance response in current binding; lookup precedes generic operation-ID routing. Foreign/missing404. |
| GET P`/operations/{operation_id}` | Owned durable status/result/observations; HTTP200 does not mean committed or assessed. |
| POST P`/operations/{operation_id}/submit` | Empty JSON only; reauthorize, atomically record dispatch attempt; use frozen bank key/body/actor/context. In-flight202, matching new201/replay200, typed errors below. |
| POST P`/operations/{operation_id}/reconcile` | Empty JSON, authorized bounded read-only domain observation plus platform record update. Does not create/retry a transfer. |

All path IDs are schema-validated and safely encoded as one segment; UUID
selectors are lower canonical UUIDs. Domain account IDs remain case-sensitive,
bounded1–64; initial integration allowlist restricts to safe ASCII IDs issued in
the authorized context, never paths/slashes/query delimiters. Unknown queries,
duplicate JSON keys, extra body fields and browser bank headers are rejected.
Read queries allow only required `actor_id`, plus `limit`/`offset` on history;
missing actor422, unknown/ungranted actor404. No implicit fallback role. The BFF
uses the selector solely to resolve an authorized private token/grant.
Responses are no-store, schema-whitelisted and bounded; references are never
silently truncated. No public DELETE/reset/seed/fault/debug/SQL/execute/proxy route.

This **proposes replacing** UPIC's direct context POST `/transfers` candidate with
two-phase operation acceptance/submit. Do not implement both as independent
writers or create an untracked legacy shortcut. No existing Banking BFF client
is broken because neither proposal exists today; joint amendment still required.

## 3. PROPOSED private producer surface and fixed path mapping

Private prefix **Q = `/internal/integrations/v1/banking`**, no internet port.
Authenticated control-plane service identity is distinct from learner cookies.
Only grant scopes explicitly permitted to that service can call these endpoints.

| PROPOSED method/path | Domain responsibility |
|---|---|
| GET Q`/capabilities` | Authenticated API/schema/producer release/limits and readiness metadata, independent of legacy `/health`. |
| POST Q`/contexts` | Idempotent `allocation_request_id` + signed allocation grant; domain creates its own path/reference/epoch and authentic approved fixture. No caller runtime handles or arbitrary balances. Lost-response retry returns same allocation. |
| GET Q`/contexts/{context_ref}` | Validate grant; report lifecycle/auth revision/incarnation/readiness/holds, private ref stays server-side. |
| POST context `/actor-token` | Scoped actor-login broker; credentials stay domain-side, internally use existing POST `/auth/login` and real password verification. Token/TTL only to BFF memory. Not a general token exchange. |
| POST context `/dispatch` | Fixed validated operation enum, per-request grant and separate bank Bearer token; durable admission receipt then internal route below. No caller method/path/base URL. |
| POST context `/observe-operation` | Read-only frozen-key/body/actor/epoch observation after grant checks; domain-owned observer, never BFF SQL. Evidence must distinguish matching commit/proven no commit/inconclusive. |
| POST context `/drain` | Restricted lifecycle service scope, stop new financial dispatch; bounded actual drain/retain/hold. Not public reset/delete. |

Internal-only domain cleanup follows lifecycle policy; no remote arbitrary-file
deletion endpoint. Authorization-revision revocation and named rebind, if approved,
use a separately reviewed lifecycle control message/ack, not a browser field.

| PROPOSED dispatch enum | EXISTING fixed context-app call |
|---|---|
| `accounts.list` | GET `/accounts` |
| `accounts.balance` | GET `/accounts/{validated account_id}/balance` |
| `accounts.history` | GET `/accounts/{validated account_id}/transactions`, only approved limit/offset |
| `transfers.create` | POST `/transfers`, exactly one original Idempotency-Key and strict integer body |
| `transfers.lookup` | GET `/transfers/{validated transfer_id}` |

BFF builds only approved service/grant/actor headers; no caller Cookie,
Authorization, Host, Forwarded, X-DQA-Account or raw Idempotency-Key is copied.
Fixed reviewed private address, no redirects, no arbitrary HTTP verb/URL/path.
Domain standalone API semantics stay unchanged; service routing is a new B2/B3
boundary, not existing multi-worker or context selection behavior.

### PROPOSED grant, context and operation fields

All fields below are future contract fields, **not current APIs/PG columns**.

| Envelope | Required fields / constraints |
|---|---|
| Signed request grant, private only | `iss`, `aud`, fixed `typ`, `kid`, `iat`, `nbf`, `exp`, `jti`, `service_id`, pseudonymous `binding_ref`, `context_ref`, `context_epoch`, `authorization_revision`, `actor_id`, `scope`, `request_id`, `request_digest`; allocation grant instead binds allocation_request_id and approved fixture ID, no pre-existing runtime handle |
| Domain context record | manager-owned reference/path manifest/data epoch/runtime incarnation, authenticated allocation identity, binding/grants, lifecycle state, actual in-flight receipts, hold/ref ledger, fixture/schema/release pins, timestamps/budgets/tombstone |
| Platform context record | public context_id + private reference/epoch, platform user/session binding, allowed actors/auth revision, accepted producer/schema/content pins, state/expiry, allocation-intent mapping, unresolved operations/reference holds |
| Browser acceptance body | `client_intent_id:UUID`, granted `actor_id`, `transfer:{from_account,to_account,amount:canonical string}`; context from exact URL; no bank key/token/epoch/handle/owner claim |
| Platform operation record | operation_id, unique(binding_ref,client_intent_id), frozen context/ref/epoch/actor/bank key/typed body/digest/version pins, acceptance time, attempt receipts, immutable confirmed result, outcome/execution/assessment/completeness and audit references |
| Sanitized browser operation | operation_id, client_intent_id, public context_id/actor_id, frozen string-money request, phase/outcome, result/observations, UTC times and completeness; no raw key/token/path/grant/private receipt internals |

**PROPOSED grant defaults:** TTL30s, clock skew tolerance5s, maximum4096 bytes.
mTLS verifies pinned service SAN/issuer and server identity; JWS algorithm is
configured ES256 only, no `none`, algorithm confusion or header URL key fetching.
Validate signature/issuer/audience/type/time/size, service scope, current context
epoch/auth revision/actor and semantic request digest **before routing**. Domain
must know the accepted binding/revision from allocation/control state, not accept
any signed arbitrary handle. Each dispatch attempt gets a fresh request ID/grant;
duplicate request ID+digest returns the same durable receipt, mismatch409.
Logout/rebind revocation prevents future admission; an admitted transaction may
still commit. Unacknowledged revocation fences further access, not DB deletion.

Request digest covers validated operation/context/epoch/actor/request ID/operation
ID/key and semantic payload, using a jointly specified sorted compact UTF-8 JSON
encoding of the typed envelope. No float or duplicate-key coercion. Matching test
vectors across repos are required before implementation. Keys/certificates are
operator-configured and rotated with an approved overlap/revocation policy;
the grant cannot select an arbitrary verifier/key URL. Library/PKI choices remain
joint security gates, not homemade crypto or installed dependencies in U5-P.

### B2 grant-verification interface versus B3 production trust

B2 defines an interface shaped around validated operation, context reference,
epoch, actor, authorization revision, request ID and semantic digest. Its default
implementation denies all requests. Unit/integration tests may inject a fixed,
deterministic authorizer whose fixtures are test-configured only, cannot be
selected through deployable environment/configuration, and never accept arbitrary
caller claims. B2 private-route handlers remain unbound or return capability-OFF
outside the test harness. Negative tests cover absent, malformed, foreign, stale,
replayed and scope-mismatched grants before context routing.

A B2 admission receipt proves only that the domain dispatcher durably accepted a
specific request identity for processing. It is not proof that the context app ran,
that SQLite began, or that a transfer committed. B2 may merge after independent
review while live integration remains OFF; its acceptance evidence must show the
deny-all production default and the non-deployable test-authorizer boundary.

B3 supplies the production verifier and private transport: mutually authenticated
TLS plus strict ES256 JWS verification with pinned trust configuration. It owns
certificate/key provisioning and custody, issuer/audience/typ/algorithm allowlists,
maximum token size/time/skew, request-ID replay control, authorization-revision
revocation, overlap rotation, emergency capability-off behavior and operator test
vectors. Network location alone does not authenticate a caller. Shared HMAC is not
approved because a verifying peer could mint grants. No live traffic is allowed
until B3 producer, U5 signer/registry and U6 consumer gates are independently
accepted for exact revisions.

## 4. Durable operation lifecycle and HTTP semantics

1. Browser creates and stores client_intent_id+draft before POST acceptance,
   under server-issued opaque binding scope tag. The tag is not a credential;
   server auth is always authoritative. Logout/account change removes that
   browser draft namespace, never deletes server operations. Storage failure
   blocks submission and explains recovery limits, rather than using memory only.
2. U5 validates/fixes context/epoch/actor/body and generates one private bank key;
   persists the binding+intent mapping transactionally, then returns acceptance.
   Retry after lost response retrieves that mapping, not a new bank key. Changed
   actor/context/body for the same intent returns INTENT_CONFLICT without mutation.
3. Explicit submit rechecks session/state/budgets/pins, persists SUBMITTING and
   attempt identity before sending. Domain records admission/active receipt before
   app posting; SQLite idempotency remains the financial deduplicator. Duplicate
   browser submits coalesce or return current state; no independent second call.
4. Validate full seven-field result (ID/from/to/amount/VND/SUCCESS/UTC timestamp)
   against original request and prior confirmed result. Confirmed result is
   immutable; record subsequent observation separately. Stored response200 is
   labeled STORED_RESULT, not invented upstream replay evidence.
5. If any attempt may have reached upstream without a trustworthy matching result,
   mark UNKNOWN and block new transfers in that context until reconciled. Preserve
   original context/epoch/actor/key/body. A rejected probe or later401/409 cannot
   settle the original. Probes are separately recorded and never accepted as retry.
6. ACTIVE contexts may explicitly retry the same operation under bounded policy
   after reauth; never automatic new-key/actor/context. Expired/draining contexts
   allow only observe/lookup, since ordinary POST transfers may post if key absent.
   Read-only NO_COMMIT_PROVEN requires actual writer drain, intact epoch/checkpoint/
   receipts and consistent independent state. Otherwise INCONCLUSIVE/hold.
7. Ordinary restart preserves file+epoch and renews actor token; restored/replaced
   file changes epoch and blocks old submissions. Keep old records/holds for joint
   reconciliation; never relabel an old UNKNOWN operation with the restored epoch.

### Crash-window and receipt matrix

`ACCEPT` is the platform's durable frozen intent. `SUBMITTING` is the platform's
durable attempt record written before dispatch. `ADMITTED` is the domain's durable
dispatcher receipt. None alone proves a bank commit. Every recovery retains the
original context/epoch/actor/key/body and earlier UNKNOWN observations.

| Window | Durable evidence at the boundary | Possible financial effect | Only safe recovery | Primary owner / required test |
|---|---|---|---|---|
| 1. Before durable platform ACCEPT | No server intent; optional browser draft is an untrusted recovery aid | None, because dispatch is forbidden before ACCEPT | Re-submit the same client intent for acceptance; create no bank call/key until one mapping commits | U5; crash before/during registry transaction proves zero dispatch and one mapping |
| 2. After ACCEPT, before submit | Frozen platform intent/key/context/epoch/actor/body; no SUBMITTING or domain receipt | None | Return NOT_SUBMITTED; allow explicit submit only while context is ACTIVE and authorization still matches | U5; restart/lost acceptance response/double-click coalescing |
| 3. After platform SUBMITTING persist, before domain receipt | ACCEPT + attempt/request ID + SUBMITTING; domain may have no receipt, but transport delivery is uncertain | None or an about-to-be-admitted call; platform cannot prove which from absence alone | Mark UNKNOWN until domain receipt/inventory and transport evidence reconcile; duplicate submit joins the same attempt, never creates a key/actor/context | U5/U6 with B2 fixture; loss immediately before/after send |
| 4. After domain admission, before SQLite write/commit | ACCEPT + SUBMITTING + durable ADMITTED receipt with request digest; possibly active-writer marker | No effect yet, or write may be in flight; admission is not commit | Observe the same receipt and writer lifecycle. Do not infer NO_COMMIT_PROVEN from a missing transfer while a writer may run. In ACTIVE state only, a later explicit same-operation POST is permitted after actual drain and policy authorization; never automatic | B2; crash at admission/app handoff/BEGIN and in-flight observer tests |
| 5. After SQLite commit, before domain response | Domain idempotency row + transfer + two ledger sides + account deltas; receipt may still be active/response-pending | Financial effect committed exactly once | Read-only lookup plus independent SQL/oracle confirms MATCHING_COMMIT; same-key replay is allowed only by explicit ACTIVE recovery policy, not needed to establish commit | B2/B4; response-loss checkpoint and exact independent reconciliation |
| 6. After domain response, before BFF confirmation | Domain result/receipt may be durable; platform remains SUBMITTING/UNKNOWN without a confirmed response record | Committed for matching201/200, or no effect for a conclusive precommit rejection; BFF has not durably classified it | Fetch durable receipt/status and independent observation; store confirmation idempotently. Later401/409/500 cannot overwrite earlier UNKNOWN | U5/U6+B2/B4; response received then platform crash, conflicting later observation |
| 7. Expiry, drain, restart or restore at any earlier window | Existing platform intents/attempts and domain receipts/inventory; normal restart retains epoch, restore/replacement changes it | In-flight or committed effect may exist; an old snapshot may omit a commit/idempotency row | Stop new writes, actually drain, use read-only reconciliation. Expired/draining/retained contexts never POST. Restore fences the old epoch and holds it for operator disposition; INCONCLUSIVE remains UNKNOWN | B2/B5 + U5 operations; writer drain, restart, older-restore and full-capacity hold tests |

`NO_COMMIT_PROVEN` requires all relevant writers drained, the original domain
inventory/receipt chain intact, an unchanged data epoch, and independent account,
transfer, idempotency and ledger evidence consistent with no effect. One missing
row, an unavailable registry, a lost receipt, a changed epoch or a restored older
snapshot is `INCONCLUSIVE`. Domain admission and an HTTP response are observations,
not substitutes for the independent financial oracle.

Duplicate submit requests coalesce on the stored platform attempt/request ID and
domain digest. They do not create an additional domain call while one is active.
After an earlier UNKNOWN, every later error is appended as a separate observation;
it cannot downgrade uncertainty or replace frozen identity. A replay POST may be
initiated only for the original operation in ACTIVE state, after reauthorization
and bounded-policy admission. Expired, DRAINING, RETAINED and RECOVERY_HOLD states
support read-only observation only.

| PROPOSED BFF status / typed observation | Required operation effect |
|---|---|
|201 phase ACCEPTANCE | Intent durably accepted, NOT_SUBMITTED; no claim money moved |
|202 phase ALLOCATION_PENDING or SUBMITTING | Existing tracked work; poll owned status, no duplicate allocation/dispatch |
|201 phase SUBMISSION, UPSTREAM_NEW | Verified domain201, outcome COMMITTED_NEW; execution observed, assessment NOT_ASSESSED |
|200 UPSTREAM_REPLAY / STORED_RESULT / status read | Verified replay or labeled stored result; status read may still be UNKNOWN; HTTP200 alone proves neither completion nor QA PASS |
|409 known domain business/conflict,422 validated rejection,404 owned-resource failure | First conclusive attempt can be REJECTED; existing UNKNOWN remains UNKNOWN with separate attempt observation. No raw field/input leaks. |
|401 platform AUTH_REQUIRED;403 CSRF_DENIED | No new dispatch; re-login does not grant another session's context or erase UNKNOWN |
|429 SESSION_BUDGET;503 CAPACITY/UNAVAILABLE | If rejected before any dispatch: NOT_SUBMITTED. If earlier submission uncertain: preserve UNKNOWN. Retry-After is scheduling, not permission for a new key. |
|503 BANK_ACTOR_UNAVAILABLE after domain401 | BFF does not logout platform or switch actor; bounded fresh login for same granted actor, original UNKNOWN retained |
|503 upstream database_busy | Preserve domain code/source; no blanket no-commit inference across attempts; original key/body retained |
|502 UPSTREAM_CONTRACT_ERROR / domain500;504 transport deadline/loss | Once dispatch may have happened, UNKNOWN; malformed success can hide a committed transfer. Response validation failure cannot roll it back. |
|200 read-only reconciliation | MATCHING_COMMIT confirms original, NO_COMMIT_PROVEN settles without resubmit, INCONCLUSIVE stays UNKNOWN; separate assessment/completeness |
|409 CONTEXT_EPOCH_CHANGED / closed state | No dispatch on changed/restored context; retain pending records and operator hold |

PROPOSED error envelope: `{error:{code,source,operation_id?,outcome?,retryable,
message_key}, contract_version}`. Codes and localized messages are whitelisted;
source distinguishes PLATFORM/DOMAIN/TRANSPORT/CONTRACT. `retryable` never means
automatic submission; domain401 cannot become platform401. No SQL/stack/input/key
echo. Upstream invalid status/body and inconsistent 201/200 are contract incidents.
Unknown operation ID remains owner-private even in an error response.

Deletion needs zero admitted writers, no UNKNOWN/pending receipt or referenced
retention obligation, domain ownership/path checks, closed handles and fenced
tombstone. Platform hold acknowledgement must precede domain cleanup. If either
registry is unavailable, retain state and reject new allocation at capacity;
never choose deletion to restore availability. Resolution is not immediate deletion.

## 5. Canonical decimal-string mapping and examples

PROPOSED BFF request schema: amount is an ASCII string with1–19 digits, no leading
zero, range1..9223372036854775807. Balance/output money permits `0` too. Browser
keeps strings; optional comparisons use exact BigInt, never JSON BigInt serialization
or Number arithmetic. Server parses exactly to int; bool/number input is invalid.
MiniBanking receives its existing integer fields and retains business limit/funds/
overflow409. Decode upstream JSON with exact integer parsing, reject bool/float,
negative/out-of-range amounts/balances, unexpected fields/type/currency/timestamps,
then map **all** nested amounts/balances to strings before browser serialization.
Preserve UTC precision; normalize timezone to Z without dropping microseconds.
Domain JSON is never handed to JavaScript first and repaired after rounding.

Illustrative PROPOSED acceptance body (not a live request/fixture disclosure):

```json
{
  "client_intent_id": "00000000-0000-4000-8000-000000000001",
  "actor_id": "actor-1",
  "transfer": {"from_account": "A", "to_account": "B", "amount": "1000"}
}
```

| Contract test vector | Required result |
|---|---|
| `"1"`, `"1000"` | Valid schema, exact int1/1000 domain request; business outcome still domain-owned |
| `"9007199254740991"`, `"9007199254740992"`, `"9007199254740993"` | Distinct exact values through consumer/producer tests; raising fixture transfer limit is disposable-test-only; no rounded equality |
| `"9223372036854775807"` | Valid wire range; domain business rejection may occur; never wrap |
| `"9223372036854775808"`, 20-digit strings |422 range error before dispatch |
| `"0"`, `"-1"`, `"+1"`, `"01"`, `"1.0"`, `"1e3"`, whitespace, Unicode digits, number1000, true/null |422 request validation, no upstream call |
| output integer0/max-int and nested history amounts above2^53−1 | Exact canonical strings; bool/float/negative/overflow response→contract error |
| recipient balance=max-int−999, amount1000 | Domain409 balance_overflow, unchanged independent SQL state |
| configured limit exceeded / funds insufficient | Preserve distinct domain409, not wire422 or fabricated no-commit proof after UNKNOWN |

No change to Data QA SQL/Decimal/NUMERIC contracts. Existing bank standalone
integer endpoints are not converted to strings; conversion is only the new BFF.

## 6. Compatibility, failure and rollout matrix

| Case | PROPOSED acceptance / fallback |
|---|---|
| Current B1 baseline | Domain business contracts reusable, integration capability OFF: no manager/private grants/version attestation implemented |
| Accepted B2/B3 release + matching contract/schema/fixture digest | Enable only after B4/U5/U6 consumer negatives and explicit pilot approval; /health alone insufficient |
| Additive minor version | Strictly recognized optional metadata; reviewed producer/consumer tests and explicit pin update; no silent unknown financial fields |
| Breaking scope/money/error/lifecycle change | New major namespace/schema, approved compatibility window and migration/rollback review in both repos |
| Missing/wrong producer pin, schema, key, readiness or context | Fail closed; no new banking writes, keep existing Data QA/tutorial/navigation and recorded content |
| Bank outage / auth restart / limit exhaustion | Sanitized unavailable; preserve owned pending state, original identity and evidence; no new context substitution |
| Platform registry outage / pending durability failure | Do not dispatch; a possibly dispatched prior operation remains UNKNOWN; no localStorage-only fallback |
| Domain storage/restore/cleanup uncertainty | RECOVERY_HOLD; admission off until independent reconciliation, no reseed/repair/reset |
| Feature off / code rollback | Block new mutations; provide compatible authorized status/recovery path or operator-only recovery hold. Never expose browser retry through an incompatible adapter. |

Release manifest pins exact approved platform/domain SHAs, BIC/schema versions,
fixture/content/rubric/evidence versions/digests and measured limits. No floating
main/latest, startup synchronization or cross-repo Git merge. Domain notification
includes compatibility matrix/test vectors/limits and independent review. Integration
PR separately updates the pin and verifies unchanged 36 labs/tutorial/auth/history.
Application FastAPI version0.1.0 is not a wire/release attestation.

Local PROPOSED pilot: fixed loopback private endpoint (candidate8002 after conflict
check), new disposable owned context root on D, explicit local mTLS keys outside
Git and same grant validation. Public PROPOSED topology: existing platform edge/
HTTPS/origin protections, private bank network only, no host-published SQLite/PG/
bank docs/static/admin or direct browser bank calls. No such configuration is
created by U5-P. No retained account, Docker volume or Cloudflare change.

Logs use event/request/operation IDs, coarse authorized binding references,
state transitions, safe code/source/version/timing/size; never credentials,
grant, token, raw bank key/body or physical path. Financial evidence is a separately
authorized sanitized record; avoid embedding account bodies in access/error logs.
Logging/collection failure cannot invent PASS or silently drop referenced evidence.

## 7. Proposed UPIC-1.0 deltas — explicit amendment, runtime approval still required

| Delta | Proposed change; existing blueprint remains unchanged |
|---|---|
| P1 baseline | Replace historical Task9 BLOCKED/bank2d7bf66 pin in a future approved contract revision with accepted tested compatible release; current audit pin7a77ec5 includes B1 docs, not B2 runtime |
| P2 D1–D3 | Specify Option A, session binding, domain manager/dispatcher, mTLS/signed request grants/private actor login, epoch vs incarnation and revocation protocol |
| P3 D4 | Approve numeric pilot budgets/TTL/hold rules, browser intent persistence and durable allocation/operation lookups |
| P4 writer routes | Replace candidate direct POST context/transfers with acceptance + submit; add typed operation/status/reconcile and private lifecycle schemas |
| P5 D5 | Formalize attempt/outcome/assessment separation, actual-drain read-only recovery, matched backup epochs and no automatic UNKNOWN cleanup |
| P6 D6 | Select canonical amount/balance strings at BFF boundary, retain domain integers and Data QA Decimal semantics |
| P7 D7 | Gate bilingual content/rubric/trusted provenance/progress separately, preserve IDs, imports and references; no localStorage credit |

The user-approved D1–D7 direction authorizes these deltas for contract and Issue
drafting; it does not update UPIC-1.0 in place or approve implementation. New
APIs/schema/migrations/runtime configuration need separately authorized
implementation tasks. Rejected generic proxy/SSO/database consolidation
and public unsafe controls remain rejected.

| Decision | Amendment state | Remaining contract / authorization gate |
|---|---|---|
| D1 Option A and split B2/B3 trust | USER_APPROVED_DIRECTION | CONTRACT_PENDING for libraries, PKI/certificate/signing-key custody, termination, rotation/revocation and vectors; IMPLEMENTATION_NOT_AUTHORIZED |
| D2 session-bound shared demo | USER_APPROVED_DIRECTION | Named-account rebind/resume disabled for MVP; any later rebind is a new approval |
| D3 unique synthetic secrets/tokens | USER_APPROVED_DIRECTION | CONTRACT_PENDING for credential custody, rotation, operator access and revocation acknowledgement |
| D4 pilot limits | USER_APPROVED_DIRECTION | Values remain configurable proposals; owner tests and B5 measurements required before pilot/public release |
| D5 ACCEPT/SUBMIT/UNKNOWN | USER_APPROVED_DIRECTION | CONTRACT_PENDING for operator reconciliation authority, NO_COMMIT_PROVEN disposition and restore checkpoints |
| D6 decimal strings/domain integers | USER_APPROVED_DIRECTION | Exact producer/consumer vectors and schema revision approval required before implementation |
| D7 deferred assessment | USER_APPROVED_DIRECTION | No progress/grading implementation; privacy, rubric, provenance and retention require later U3/U7/U9 approval |

## 8. Testable per-repository acceptance

MiniBanking B2/B3: two owned contexts with same A/B/C and keys, separate tokens;
foreign grant/actor/session/reference/epoch/URL/path fails before routing; private
service/JWS/mTLS negative vectors; fresh init/partial init/cleanup race/Windows
handle closure; quotas/exhaustion and token restart; compatibility/readiness/error
and secret-redaction contracts. B4: actual private HTTP plus independent read-only
[SQL oracle](https://github.com/taodo/MiniBanking/blob/7a77ec579d7ff0edf2299d3755155573fee1ec15/scripts/verify_sql.py),
one transfer/two matching sides/one reference, exact account deltas, FK/conservation/
reconciliation; false-success/missing-side/replay/conflict/rollback/UNKNOWN/restore
detectors. B5: measured capacity and actual restart/drain/backup/restore/network
outage rehearsal on disposable state, no public launch.

Data QA U5: durable intent acceptance before dispatch; lost response/refresh/double
click maps once; same shared username/two sessions cannot read/list/retry/status/
evidence; ownership/CSRF/header spoofing; pending storage crash and orphan holds;
named rebind disabled unless approved. U6: fixed operation adapter, strict string
money test vectors, malformed/oversize upstream and SSRF/redirect negatives, HTTP
status/source/outcome fidelity, browser recovery and no-secret exposure; ENG/VIE,
Dark/Light,375/768/1280 and existing SQL/non-SQL/history/tutorial regressions.

Joint gates require exact approved heads, pinned producer/consumer fixtures and
independent negative evidence; green producer alone does not approve consumer.
No bank runtime, SQL, build or full suite was executed by this documentation task.
