# U5-L local consumer: approval checkpoint

**Status: BLOCKED before live interoperability. Offline preflight only.**

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

No subsequent joint signoff was present in the Issue #51 comments at inspection.
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

## Decisions proposed for joint review — NOT APPROVED OR IMPLEMENTED

The human platform/domain owner and security/operator reviewer must affirm the
following local profile on Issue #51 and record the corresponding decision on
MiniBanking Issue #24. An agent-authored proposal is not their signoff.

| ID | Proposed bounded local decision | Evidence and remaining approval |
|---|---|---|
| J1 — wire and errors | Adopt the exact accepted B3 `BIC-1.1-candidate` wire under the C1–C11 design alias `BIC-1.1-producer-baseline`. Pin the B4 V2 outer/inner status matrix, not the foundation fake matrix. No `/actor-token`. Canonical full Request except digest uses compact sorted `ensure_ascii=True`, `allow_nan=False` ASCII/UTF-8 and SHA-256. | Source artifacts pinned in this branch; approve consumer use and signed positive/negative vectors before real sockets. |
| J2 — local keys and transport | For the first bilateral test only, use runner-owned ephemeral P-256 signer keys and an independent ephemeral test CA with serverAuth/clientAuth certificates. Fixed server SAN `minibanking.internal`, client SAN `data-qa-lab-u5.internal`, chain + SAN + SHA-256 fingerprint verification both ways. Bind a dedicated producer to an OS-assigned loopback port; no redirects, proxies, browser URL/header forwarding or existing server reuse. Keys live only in a private owned temporary directory, have no source/artifact export, and are removed after owned processes close. | Authorize this ephemeral test custody/topology. Persistent operator keys, production PKI, rotation and release remain deferred; they cannot be inferred from a test pass. |
| J3 — signing dependency and claims | Reuse the accepted producer dependency families (`PyJWT>=2.9,<3.0`, `cryptography>=43,<47`) for ES256 only, subject to platform dependency approval and resolved-version evidence. Exact protected `alg/typ/kid`, pinned issuer/audience/subject/service, TTL30/skew5, fresh JTI, max4096 bytes; no external JOSE key URLs. Fixture issuer/identities are synthetic test values only. | Platform currently has neither dependency declared. No package is added in this branch. Approve the library choice for the local slice; record exact resolved versions when implemented. |
| J4 — BFF and session boundary | A separate explicit local app configuration defaults OFF and must fail closed unless trust, signer and producer pins validate. Keep public/demo entry point OFF regardless of local configuration. Fixed same-origin BFF only; authoritative cookie session plus opaque token-hash-derived binding, CSRF and exact configured loopback Origin on every mutation; reject missing/null/cross-site Origin, browser grant/URL/actor credentials and cross-session ownership. Preserve all Data/Automation routes. No U6 UI. | Existing origin middleware allows some missing-Origin requests; do not silently change shared auth. Approve stricter Banking-only handling and the local/public app separation before implementing routes. |
| J5 — uncertainty, lifecycle and recovery | Commit ACCEPT and SUBMIT separately before I/O. Never replace the frozen identity or automatically retry a transfer. Keep previous UNKNOWN through later 401/403/409/503, malformed replies, expiry and restoration. Reads/observations cannot declare NO_COMMIT from absence. Logout/password/session fencing and revocation outbox precede auth-session removal; a bounded local maintenance worker sweeps expiry and retries outbox with original context identity. Fail admission closed while revocation freshness is unavailable; ACK only for the matching binding/context/epoch/revision. | Approve a 5-second local sweep, connect2/read5/total8-second I/O budgets, maximum 3 recovery attempts per intent/5min and 10 lifetime, preserving existing admission quotas. No eviction or automatic deletion of UNKNOWN/HELD/outbox. Persistent operational retention/rotation/restore approval remains separate. |
| J6 — financial evidence | V2 SQL match is for declared disposable observations, not a signed domain receipt or consumer assessment. Source-owned independent read-only SQL must reconcile exact operation identities, one transfer/two sides/one reference and account deltas. U5 never opens domain SQLite or imports SQL evidence as progress. | Approve V2 consumer interpretation and bilateral evidence procedure. Runtime strict response schema/sanitization, provenance and all seven crash windows must be exercised after authorization. |

### Pinned source error mapping for the later consumer

| Producer response | Consumer interpretation required by the proposal |
|---|---|
| outer200 / nested201 | New bank result observed; financial proof separate. |
| outer200 / nested200, or stored receipt with original nested201 | Replay/stored evidence; inspect `stored`, preserve original result and identity; no additional posting claim without SQL. |
| outer200 / nested409,404,422 | Domain rejection/visibility/validation observation; cannot erase earlier UNKNOWN. |
| outer200 / nested401,500,503 | Authentication/infrastructure uncertainty; retain original identity and hold. |
| outer202 or lost response after SUBMIT | UNKNOWN; timeout does not cancel a writer. |
| outer400,403,404,503 | Private envelope/authorization/route/unavailability error; never infer no historic commit. |
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

After recorded J1–J6 approval, implement those requirements on the same task
branch, run focused tests first, then one required final regression on committed
HEAD. Recheck both source/base pins and refresh affected evidence. Do not enable
public Banking, merge, deploy, or start U6. Until then the task is **BLOCKED**, not
READY_FOR_REVIEW or implementation-complete. Request independent review of this
checkpoint and the proposed decisions.
