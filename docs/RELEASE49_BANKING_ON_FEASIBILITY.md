# Issue #49 — Local Banking ON feasibility and dependency gates

REVIEW DATE: 2026-10-16. This is **source inspection and a proposed integration sequence**, not implementation, cryptographic attestation, a live local test, or permission to deploy. [Authoritative Issue #49](https://github.com/taodo/Data-QA-lab/issues/49); architecture [U5 C1–C11](https://github.com/taodo/Data-QA-lab/issues/47); [MiniBanking B4 #24](https://github.com/taodo/MiniBanking/issues/24).

## Exact source pins checked

| Repo | Source | Verified state |
| --- | --- | --- |
| Data QA Lab | feature/develop 372210246a4e1949b9ed0916f5fbb775d72a5807 | U5-F PR #48 merged; OFF registry and immutable PG ACCEPT/SUBMIT only |
| MiniBanking | feature/develop d77ce49b6d4ba7303dd796d072f758c9f1086beb | B3 private TLS/ES256 boundary accepted/merged, default OFF |
| MiniBanking | Draft PR #25 feature/task-b4-producer-ledger-verification 35189e0515d1eea6c1d4397ad24e803b63a9d5ce | Exact-HEAD CI #38754937736 PASS, but **unmerged and independent review pending** |
| Data QA Lab | tests/banking_fake_consumer.py | Structural negative tests only; no actual ES256 cryptographic signing/verification |

Source evidence: Data QA Lab backend/app/banking_foundation.py, docs/BANKING_U5_FOUNDATION_IMPLEMENTATION.md, tests/unit/test_banking_foundation.py, docker-compose.demo.yml; MiniBanking backend/private_transport.py, docs/B3_PRIVATE_TRUST_BOUNDARY.md, B4 Issue #24 comments, contracts/b3_grant_vectors_v1.json. Earlier U5-P proposed actor-token endpoint is obsolete: B3 uses its own synthetic actor broker.

## Capability matrix

| Capability / release gate | Status | Action/owner |
| --- | --- | --- |
| Platform authentication and opaque per-session PG binding | IMPLEMENTED / Banking OFF | U5-F; confirm isolation on actual BFF later |
| Durable intent, sorted ASCII-escaped SHA256 request digest, decimal-string money, UNKNOWN retention | IMPLEMENTED / no private I/O | U5-F; connect only through future reviewed consumer |
| Internal producer mTLS + explicit ES256 JWS grant verification / revocation | IMPLEMENTED in isolated B3 source, **not default started** | MiniBanking; production private key/cert and listener operations not provided |
| Independent domain SQL oracle for actual mTLS postings | CANDIDATE, CI PASS, **not accepted** | MiniBanking B4 PR #25 needs independent security/financial review and human merge |
| Platform ES256 JWS signer and pinned client-identity mTLS client | MISSING | New Data QA U5 live adapter task, with ephemeral dev CA/certs only locally |
| Signed allocation/status/dispatch/observe/drain/revoke plus revocation ACK | MISSING as integrated platform behavior | Data QA U5 live adapter; operator scheduling/expiration fencing essential |
| Same-origin fixed Banking BFF with CSRF/origin/host/actor/session/epoch checks and sanitized results | MISSING | Data QA U5-BFF task, never a generic proxy |
| Learner-facing Banking UI / simulator / ENG-VIE/mobile | MISSING | Data QA U6 task after accepted BFF |
| Joint producer+consumer signed positive/negative golden vectors, actual mTLS + post-commit lost response and independent SQL | NOT RUN | Two-repo pinned acceptance; must post results to both Issues |
| Local operator smoke and user-facing Banking E2E | NOT RUN | Future integration task on isolated test data |
| Deployment/private network hardening, backups/recovery and operational readiness | BLOCKED / B5 + U10 | Both repo owners, human approval, private-only producer |
| Public Banking ON at data-qa-lab.store | NOT AUTHORIZED | Must stay OFF until explicit new release approval |

B4 CI passing is **not** independent review or accepted branch state. B3 real trust implementation having tests does not mean a deployable U5 signer or direct platform communication already exists.

## Proposed minimum local Banking ON vertical slice — **not approved for coding by this Issue**

1. **MiniBanking source first:** close B4 Issue #24 review/remaining gates, accept exact producer contract and B4 test oracle on its own task branch. No producer runtime development in Data QA Lab.
2. **Data QA U5-L live transport/consumer issue:** implement a locally gated, default-OFF module for ES256 exact synthetic grants and pinned mTLS client identity; private loopback producer transport only, never public proxy. Preserve U5 immutable ACCEPT and SUBMIT transaction ordering, unique operation/bank key, actor/session-context and amount bounds, UNKNOWN hold, original-identity read-only observation. Require scheduled session expiry fence + domain revoke ACK and conservative outage behavior. Reject unsigned/invalid/wrong scope/actor/session/revision/expired/duplicate JTI grants without I/O. Implement actual cryptographic validation with ephemeral CA/keys and independent negative tests.
3. **Data QA U5-BFF issue:** same-origin fixed allowlisted endpoints for allocation/status/reads/operation ACCEPT/SUBMIT/reconcile; CSRF+origin on every mutation, no bank key/tokens/private context refs in browser; strict no-store/typed bounded JSON; explicit feature OFF/UNAVAILABLE/LOCAL_TEST readiness semantics. Host/public-demo restrictions remain intact; default OFF.
4. **Data QA U6 local UI issue:** minimal Banking trial experience for opted-in test users, synthetic actors/account reads, transfer confirm with lossless money string, explicit acceptance vs posting vs verification badges, UNKNOWN and recovery guidance. Mobile, keyboard, ENG/VIE and platform progress separation.
5. **Bilateral local E2E:** start isolated platform and MiniBanking private test-owned contexts/certificates, no Cloudflare or production bank SQLite. Verify exact pinned source HEADs and signed grant bytes, context allocation, scoped accounts, ACCEPT→SUBMIT→verified SQL observation, replay, changed body409, isolation across two users/sessions, logout/revoke/TTL, restart/recovery/UNKNOWN, timeout/503, mis-signed/invalid JWS, wrong TLS identity, SSRF/path/header injection, browser CSRF/host/origin, no fund/credential leaks. Never mark independent SQL oracle PASS merely from a producer HTTP 200/201/202.
6. **Release**: only after separate B5 producer ops and U10 platform release readiness, reviewed backups/retention/rotation and human approval. Even after a green local ON test, recommend first production upgrade with Banking OFF; public ON is a later explicit release gate.

## Decisions and acceptance boundaries

- Banking ON local requires a real private B3/B4 signed/mTLS path, not a global capability string or non-deployable fake consumer. Separate local dev flag defaults OFF and rejects missing/mismatched certs/contract/producer.
- U5's actor/operation identity is derived from server-side authenticated session; direct host URL, domain SQLite paths, private grant, bearer token, bank key, and signed JWS must not become browser inputs.
- Keep one-shot signed scopes and exact SHA256 canonicalization from B3: sorted compact JSON, ensure_ascii=True, strict signed64 in domain; browser positive ASCII decimal string, never JS Number for money. Reject floats, booleans, duplicates, exponent, non-ASCII digit, overflow, unapproved keys/certs.
- Reuse accepted source artifacts only; do not copy MiniBanking implementation into Data QA Lab. No live Bank ledger, SQL query/admin/reset/fault or public domain port. Revocation/outbox failures must preserve UNKNOWN and block fresh admission.
- Independent financial oracle must check actual sender/recipient deltas, transfer and both ledger sides, idempotency and ownership in a disposable test-owned SQLite DB; no manual corruption of retained user databases.
- All current gate statuses are based on repository metadata/source/previous exact-HEAD CI, not local execution during Issue #49. No runtime PASS claimed.

## Suggested follow-up task ownership (create only after user approval)

A. MiniBanking B4 #24 final independent review + accepted PR #25 (existing authoritative task; no duplicate).
B. Data QA Lab **U5-L / local ES256+mTLS client and life-cycle revocation** (new Issue, after A).
C. Data QA Lab **U5-BFF + U6 minimal local UI** (bounded one or two Issues after B, with independent auth/CSRF review).
D. Joint B4↔U5 exact-head signed integration and independent SQL proof (linked acceptance comments in both Issues).
E. MiniBanking B5 + Data QA U10 release readiness, then explicit human approval for public deployment/Banking ON.

**Current decision:** Gate A local Banking OFF reproducibility can be manually exercised now; local integrated Banking ON is BLOCKED on acceptance and missing U5/U6 runtime; production Banking public ON is NO-GO.
