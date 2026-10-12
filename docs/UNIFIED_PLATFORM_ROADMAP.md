# Unified Platform Roadmap — U1 through U10

U1 status: documentation-only blueprint for independent review. U2–U10 are **proposed tasks, not implementation authorization**. Three confirmed repositories: [Data-QA-lab](https://github.com/taodo/Data-QA-lab) (platform/UI/identity), [MiniBanking](https://github.com/taodo/MiniBanking) (bank domain/API/SQLite), [Automation-QA-Lab](https://github.com/taodo/Automation-QA-Lab) (future local/CI framework/examples). Follow the [authoritative contract](UNIFIED_PLATFORM_INTEGRATION_CONTRACT.md) and [current-state audit](UNIFIED_PLATFORM_ARCHITECTURE.md).

## Baseline and sequencing

Platform accepted base `e4274a4` includes Task 20/20.1 and merged Task 21.1 PR #33. Keep nine executable courses/36 labs and `ai-test-automation` (10 modules/30 entries/one available introductory tutorial). MiniBanking accepted base `2d7bf66` contains eight Vietnamese challenges/local learning UI and transfer APIs; Task 9 `27187cb`/PR #18 is still draft/BLOCKED and cannot be imported as accepted work. Automation main `b133532` has only `.gitattributes`, no framework/service/develop branch. Public domain observation still shows pre-21.1 catalog; development merge is not deployment.

Recommended dependency order: U2 informational navigation can proceed after U1 approval without a bank/automation service. U3 content contract and U4 independent Automation bootstrap can be planned next. U5 must close public bank isolation/security decisions **before** U6 simulator writes. U7 depends on U3/U6 for assessed bank practice, with read-only recorded evidence possible first. U8 depends on domain-approved U4 releases; U9 depends on explicit identity/progress/evidence contracts. U10 is a release/security gate, not automatic deployment or a promised public runner.

## Proposed implementation slices and acceptance

| Task | Owner / dependency | Bounded scope | Acceptance / stop gate |
|---|---|---|---|
| **U2 — Shared three-track navigation** | Platform; U1 approval | Homepage three cards, exact `/learn/data`, `/learn/banking`, `/learn/automation`; reuse existing Data landing and tutorial overview/player; Banking/Automation future actions honestly Planned. | Shared header/tokens/theme/ENG-VIE/accessibility at 375/768/1280; React and SPA routes plus bounded legacy fallback; refresh/back/forward; public discovery; all saved course/lab/tutorial links/auth returns preserved. No new backend/domain calls/progress/schema/dependencies/deployment. |
| **U3 — Domain learning-content contract** | Platform + separately approved bank content changes | Pin accepted eight Banking challenge IDs/version; author ENG/VIE representation; explicit local/recorded/live provenance, evidence rubric; validate track membership without renaming courses. | Domain approval/content license/digest/schema; no MiniBanking iframe/CSS copy or duplicate Task 21.1; missing content unavailable; read-only evidence bounds/secrets rejection; no forged progress/assessment or Task 9 dependency. |
| **U4 — Automation bootstrap and versioned examples** | Separate Automation domain task, then separate platform integration PR | Bootstrap local/CI pytest/API/UI structure and release contract; platform consumes approved examples via reviewed version pins/content PR, not runtime synchronization. | Future develop/task workflow established with approval; deterministic local/CI tests and independent assertions, sanitized versioned evidence, dependency/lock policy; no web service/code runner/LLM keys. Preserve original platform tutorial IDs/renderer. Detailed bootstrap below. |
| **U5 — Banking context/isolation security foundation** | Bank domain + platform integration reviews; D1 decision closure | Decide and implement isolated synthetic context lifecycle, owner/session grants, private role/token handling, quota/TTL/cleanup, routing/restart and unknown-operation recovery in isolated test environments. | Per-context SQLite/app isolation or separately approved tenant-aware alternative, never shared default A/B/C DB across visitors; shared-demo visitor isolation; no raw public control endpoints, SSRF, credential/token forwarding or bank SQL passthrough. Stop public integration if ownership/provisioning/retention unresolved. No retained data initialization/reset. |
| **U6 — Secured Banking simulator adapter/UI** | Platform with accepted U5 domain release | Narrow fixed BFF operations for accounts/balances/transfers/lookup/history, React views inheriting platform shell; synthetic role selection explicit; preserve key/body for retries. | Auth/CSRF/IDOR/host/proxy/header allowlist tests; integer/overflow/lossless JS contract; real domain API + independent SQLite outcome evidence; 201/200/409/503/UNKNOWN fidelity; bank outage leaves other tracks usable. Public rollout still requires U10/operator approval. |
| **U7 — Banking challenges and assessment evidence** | Platform + bank content; U3/U6 | Eight approved challenge mappings, recorded-evidence import, prediction/hints/answers, explicit assessment/self-check; only then approved platform-owned progress persistence if scoped. | HTTP success insufficient: per-transfer ledger pairing, per-account deltas/reconciliation, no side effects on rejection, durable idempotency/replay; imported PASS untrusted; ownership and bounded evidence/provenance/version; no semantic free-text grading claim. Task 9 concurrency optional only after its own release gate closes. |
| **U8 — Automation frameworks and learning integration** | Automation domain releases + separate platform PRs; U4 | Local/CI API/database/Playwright implementations and independently verified examples; reviewed tutorial content increments on website. | Each available lesson actually authored ENG/VIE, planned statuses accurate; no future execution claim; pinned framework/content compatibility and real failure-detection tests; secret-safe reports; existing 36 labs untouched. Exact Task 21.2–21.5 specs required before assigning implementation scope. |
| **U9 — Unified progress and evidence experience** | Platform; approved U7/U8 semantics | Track-aware dashboard over existing executable progress plus separately specified tutorial/Banking self-report/assessment states; contextual links, resume and provenance. | No rewrite/loss of existing enrollment/session IDs/history. Account/privacy and public-shared disclosures; self-report ≠ validated completion, execution ≠ QA correctness; versioned assessment and incomplete/unavailable states. Any additive schema migration has a reviewed preservation/rollback plan. No domain DB consolidation. |
| **U10 — Integration hardening and release decision** | Platform + domain owners; previous accepted compatible revisions | Contract compatibility suite, limits/abuse/outage/restart/rollback rehearsal on disposable state, operational release manifest and user-approved release gate. Public sandbox feasibility may be a separate research subtask only. | Approved exact heads; full relevant regression, protected unsafe endpoints/private storage, capacities/context cleanup and data preservation, reversible capabilities; explicit develop→main→deploy approval. No public code execution or third backend until separate threat-model/cost/isolation approval. Fail closed if any gate unresolved. |

Each task should be independently reviewable and split when domain and platform responsibilities diverge. Do not use a domain approval as blanket platform permission. No U2–U10 work begins in U1.

## Existing Task 21/22 mapping — facts versus planning allocation

No authoritative Task 21.2–21.5 or Task 22 implementation specifications were found in the audited platform source/docs or Task 22 issue search. The rows below explicitly map their **planning/integration slots**, not invented approved requirements. Obtain the exact specs and revise this mapping in an approved planning PR before implementing them.

| Existing identifier | Verified status | Unified slot / proposed responsibility |
|---|---|---|
| **Task 21.1** | Merged PR #33; implemented platform tutorial foundation | U1 audited accepted dependency; reused unchanged by U2/U3/U8. Website presentation/manifest remain platform-owned even after independent Automation bootstrap. |
| **Task 21.2** | Future, scope unverified | Specification gate at U3/U4: distinguish course content/quiz/progress requirements from Automation repository bootstrap. Bootstrap is a separate domain task; do not treat this number alone as authorization. |
| **Task 21.3** | Future, scope unverified | U4/U8 consumer/framework integration window; if approved spec covers API/database practice, framework code goes to Automation repo and tutorial UI/content integration to platform. Otherwise remap. |
| **Task 21.4** | Future, scope unverified | U8/U9 integration window; if approved spec covers Playwright/CI/evidence, domain implementation and platform presentation/progress gates remain separate. Otherwise remap. |
| **Task 21.5** | Future, scope unverified | U8/U9 capstone/content/evidence review window **conditional on actual spec**; no assumed completion model or public execution. |
| **Task 22** | Future, scope unverified | U10 specification/security/release decision gate. Do not assert Task 22 means sandbox, Banking or SSO; review its actual scope first. A sandbox proposal would require a separate execution threat model and may be rejected/deferred. |

The independent Automation repository amendment changes *framework ownership*, not existing course URLs, lesson IDs or learner-facing presentation. There is no migration of Task 21.1 to a new site/service.

## Recommended separate Automation bootstrap task (not U1 implementation)

Recommend one domain task `feature/task-1-automation-foundation` after explicit approval to establish `feature/develop` from its initial main. Suggested initial structure:

```text
pyproject.toml
src/automation_qa/         # config, API client and reusable assertion helpers
tests/unit/               # deterministic config/assertion/client behavior
tests/api/                # fixed synthetic/local targets, no real banks
tests/db/                 # read-only oracle checks over disposable fixtures
tests/ui/                 # Playwright locators and bounded journeys
examples/                 # reviewed standalone learner snippets
contracts/                # versioned content/evidence schemas
docs/                     # local setup, safety, evidence interpretation
.github/workflows/        # local-equivalent bounded CI, no deploy/secrets
```

Dependency plan (future approval required): Python 3.12 candidate to align existing CI, `pyproject.toml` with approved bounded dependency ranges and a reproducible lock/constraints mechanism; do not install a second manager/framework without benefit. pytest + HTTP client for API tests, Playwright only when UI cases exist; browser install/cache/output on D locally. DB driver only when a concrete read-only/disposable DB scenario needs it. No AI provider SDK, paid API or cloud credential dependency. Support commands through the venv Python, independent expected values, negative/boundary cases and controlled mutations that demonstrate failures.

Configuration uses named approved local/CI targets and validated env variables, no learner arbitrary URL/SQL/shell upload. Separate API clients/fixtures from assertions; use bounded timeouts/retries, frozen operation key/body for Banking UNKNOWN/replay, explicit fixture isolation and cleanup. Treat platform auth, bank mock auth and CI credentials as different. Default to no network outside selected synthetic targets; never copy public demo credentials into source, screenshots or reports.

Initial GitHub Actions: minimal read permissions, locked installation, unit/API tests on disposable state, UI only when needed, finite job/runtime limits and sanitized evidence uploads; no deployments/auto-merge/provider calls. Separate normal regression from expected-defect demonstrations, preserve actual exit codes and independent SQL checks. Report framework version, exact commit, target/domain version, content/evidence contract, command/runtime, actual execution/assessment/completeness and limits. Uploaded reports are evidence, not an authenticated website learner completion grant.

Domain delivery: feature/task PR→independent review→user approval→develop→explicit domain release. Platform import delivery then uses its own integration-contract review/feature PR/regression/release approval. U1 performs none of this bootstrap or synchronization.

## Public readiness, failure handling and alternatives

- **D1 isolated Banking context decision** blocks U5/U6/public writes, not U2 informational cards. Recommended app+SQLite per context has capacity/expiry/token-routing costs; an explicit tenant-aware domain redesign is an alternative, not accepted work. Recorded-evidence-only Banking is the safe fallback until approval.
- Task 9 formal gate remains BLOCKED; never merge or amend its timeout/harness to unblock platform planning. Concurrency teaching integration must pin a later accepted domain revision and distinguish ASGI overlap from real TCP/multi-process behavior.
- Named personal account progress, shared-demo session scope and self-report/assessment semantics require separate approvals before U9. Existing retained 15 accounts are operator-reported and not censused in U1; preserve all.
- Public domain currently differs from develop. Release manifests must pin platform, bank API/content and Automation artifact versions; inspect actual deployment image provenance during a future authorized gate.
- Bank unavailable: capability off, sanitized error, preserve pending operation/independent observations; do not create a new key or mark completion. Automation unavailable/incompatible: keep last approved content/M01.L01, reject import, no runtime fetch/runner. Disable new integration slices without rolling back/delete/reset of any database.
- Local/CI Automation may remain the final execution model if public sandbox isolation/abuse/cost cannot be justified. Do not add a service merely because a third repository exists.

## U1 verification and handoff boundary

Executed: Git identity/status/ref/ancestor checks, accepted-source audit, manifest/catalog counts, read-only remote refs/initial commit/Task 9 PR and status lookup, anonymous public GET observations. Four-document path/Markdown/route/inventory/count and documentation-only diff checks are recorded in the U1 PR handoff. Runtime suites, bank startup/OpenAPI generation/SQLite queries, production account/tunnel/image inspection and deployment were not run. Existing automatic PR CI is informational for this documentation-only diff; no full local suite is required.

U1 ends at **READY_FOR_REVIEW** for the blueprint. U5/U6 and unspecified Task 21/22 implementation gates remain unresolved. Do not merge, deploy, modify a domain repository or start U2 without independent review and explicit user approval.
