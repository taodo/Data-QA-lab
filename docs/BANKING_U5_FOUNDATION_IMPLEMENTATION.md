# U5-F — Banking platform registry and durable intent foundation

Authoritative task: [Data QA Lab Issue #47](https://github.com/taodo/Data-QA-lab/issues/47), C1–C11 binding architecture. Branch `feature/u5-banking-platform-foundation` from `feature/develop` `a8a4fecf31167b88ff8834a7c390fe8c7c0700bf`. MiniBanking B3 accepted producer baseline `d77ce49b6d4ba7303dd796d072f758c9f1086beb`. B4 Draft #25 is **not** accepted/merged.

## Engineering / learning objectives

U5-F demonstrates that a platform can atomically persist authenticated session-scoped context allocations and immutable money-transfer intent ACCEPT then SUBMIT, **without granting the public website banking execution rights**. Distinguish persistence/authorization/uncertain execution from independent financial truth. The registry and ACCEPT receipt do not prove a bank transfer occurred. No Banking operation is graded, and all live/private Bank execution is disabled.

## Migration and deployment boundary

The repository uses one additive, idempotent `backend/app/persistence/schema.sql` and `initialize_database()` in its bootstrap, **not Alembic**. U5 appends PostgreSQL `metadata.banking_bindings`, `banking_contexts`, `banking_operations`, `banking_attempts`, `banking_observations` and `banking_revocation_outbox` with uniqueness/FK/checks, preserving existing account, lab and course tables. Migration via the normal bootstrap must be applied on an isolated test database and verified for repeatability before acceptance. Never reset or drop the user/demo/production PG DB.

Banking `binding_ref` uses a fresh opaque pseudonym per authenticated `account_sessions.token_hash`, and its owner is separately recorded. The token_hash is intentionally **a snapshot, not a cascading FK**: normal logout deletes the session record, but bank UNKNOWN/outbox and legal retention holds cannot be erased by session deletion. Real banking still requires a valid, live, authorized session on **every** state-changing API. Different sessions for the same username receive different bindings/context identities.

A single live context per binding is enforced by a unique partial index. Registered context allocation intents, operations and submitted attempts have dedicated database uniqueness. Candidate context lifetime/retention caps are conservative and do not erase held, uncertain or previously accepted operations. The foundation stores the immutable frozen request under PG JSONB plus exact digest, no bank account credential or domain SQLite path. No cross-repo data mutation.

**Rollback:** the foundation is disabled by default. Do not drop banking metadata tables if any ACCEPT/SUBMIT, UNKNOWN, HELD or revocation outbox entries exist. The rollback strategy is to keep the additive schema inert, with backups and explicit retention/disposition reviewed separately; destructive down-migration is not authorized.

## Security and durability

`backend/app/banking_foundation.py` has `CAPABILITY="OFF"` and no network or signing imports. The module only exposes trusted backend functions taking a PG transaction connection and server-derived principal. `_session` revalidates `account_sessions` expiry, account active state and public-demo disabled status under row lock, checking the principal's user ID and token hash. Raw cookie/password/CSRF are not forwarded into Banking grants. There are **no public Banking routes** in FastAPI or browser UI in this slice, so authentication/CSRF and BFF endpoint integration remain separately reviewed U5/U6 work.

`reserve_context` atomically locks the session and provides idempotent allocation; `attach_private_context` is an internal operator/test-only acknowledgement, **not a live producer call**. `accept_intent` validates string money and immutable context/actor/request identity, persists an ACCEPTED row and SHA256 hash, then returns. `submit_intent` runs in another explicit transaction, persists a single attempt and moves state to SUBMITTING **without network side effects**. Duplicate submit returns existing phase and does not issue another attempt. A failed/lost later transport response would require `mark_uncertain`; a later 401/409 cannot be used to erase an existing UNKNOWN. Only separately authorized original-identity read-only observation and independent proof can settle financial outcome, not this module.

Logout, password change and reset call `fence_session` in the same PG transaction that deletes the account session(s). This changes SUBMITTING to UNKNOWN and appends a **PENDING** revocation outbox entry while preserving durable operations. `fence_orphaned_bindings` supports maintenance for expired/orphaned sessions; there is **no live scheduler or revocation transport** in U5-F, so this is not a claim of real-time domain revocation acknowledgement. All live grants/traffic must remain OFF until such an operational path is reviewed, scheduled and proved against B3.

## Producer contract baseline (fixture only)

`tests/fixtures/banking_b3_producer_v1.json` is pinned exactly to accepted B3 `contracts/b3_grant_vectors_v1.json`. Frozen typed B2 Request serialization uses `json.dumps(sort_keys=True,separators=(',', ':'),ensure_ascii=True,allow_nan=False)`; SHA-256 over the UTF-8 encoded bytes. The producer request includes context handle, epoch, actor, binding/revision, operation ID, request ID, bank key, typed payload and recovery flag. The platform boundary accepts only ASCII decimal strings 1..2^63−1, rejects bool/float/leading zeros/exponent/unicode digits/overflow and passes lossless integers into that producer request. Future production signing uses ES256 pinned keys and direct mTLS; no signer/private keys, transport adapter or dynamic key download is in this slice. Proposed `/actor-token` is omitted: MiniBanking keeps synthetic actor credentials/token in its own B2 broker.

These unit golden checks are **not** U5↔MiniBanking live consumer acceptance. B4 cross-repo test will require real test-signed JWS + valid/invalid mTLS peers and recovery/read-only SQL verification after a separately approved adapter/signer slice.

## Validation and delivery

- Focused: `python -m unittest tests.unit.test_banking_foundation -v` and `DATA_QA_TEST_DATABASE_URL=<isolated disposable PG> python -m unittest tests.integration.test_banking_foundation -v`.
- Final existing platform workflow: GitHub `.github/workflows/test.yml` runs frontend build, Python unit/integration/E2E with isolated PostgreSQL, plus packaged container smoke. Record exact final branch HEAD and result, do not treat queued jobs as PASS.
- Check existing login/signup/logout, Data labs and demo behavior in CI. No changes to routes, Data track catalogue, course UI, localization, theme, domain bank ledger, proxies, public tunnels or release settings.
- After tests complete, post a complete FINAL REPORT on Issue #47, verify remote HEAD, independent review of security/schema/CI, and stop without merging. B3's human independent-review waiver applies **only** to B3, not to U5.
