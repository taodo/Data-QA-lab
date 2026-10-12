# Unified Platform Test Strategy — U1

This is a proposed verification strategy, not a claim U1 ran product suites or implemented integrations. Confirmed repositories: platform [Data-QA-lab](https://github.com/taodo/Data-QA-lab), Banking [MiniBanking](https://github.com/taodo/MiniBanking), future local/CI frameworks [Automation-QA-Lab](https://github.com/taodo/Automation-QA-Lab). Follow [Integration Contract](UNIFIED_PLATFORM_INTEGRATION_CONTRACT.md), [Architecture provenance](UNIFIED_PLATFORM_ARCHITECTURE.md#1-repository-and-deployment-provenance), and [U2–U10 gates](UNIFIED_PLATFORM_ROADMAP.md).

## 1. Evidence and execution policy

U1: inspect actual pinned source/Git/API observations, validate Markdown links/routes/counts and `git diff --check`; no application build/full regression/DB initialization/reset is required for four new docs. A report or workflow definition is not proof of an executed check. Report exact head/base, read-only domain revisions, commands and EXECUTED / NOT RUN / BLOCKED distinctions.

Future implementation: focused changed behavior/negative tests first; build when executable frontend changes; final relevant regression on exact committed head. Green CI on that exact head may satisfy platform full validation; do not duplicate it locally. After fixes run affected checks first, then final CI; do not weaken assertions or retry unchanged failures without diagnosis. Domain-specific gates remain independent: MiniBanking Task 9's incomplete local HIGH evidence is not replaced by this policy or hosted CI. Independent review/user approval is not a test outcome.

Execution states (future unified evidence model): NOT_RUN/RUNNING/SUCCESS/ERROR/UNKNOWN distinct from assessment NOT_ASSESSED/PASS/FAIL and completeness COMPLETE/INCOMPLETE. Existing platform/API names remain unchanged; mapping is explicit at consumer boundary. A tutorial view, API request, UI checkbox, imported PASS string or green framework run cannot alone prove requirement coverage/learning completion. Controlled defects must fail their intended invariant/assertion, not merely any command.

## 2. Regression matrix — preserve every executable lab and tutorial

| Existing course ID | Labs | Mandatory retained behavior | Existing primary checks |
|---|---:|---|---|
| `sql-data-qa` | 13 | Key reconciliation, duplicate-group/excess-row semantics, Decimal aggregates, grain/JOIN, version order, UTC/replay/freshness/SCD boundaries; restricted read-only runtime; hint/reveal/completion/history | [learning contracts](../tests/unit/test_learning_contracts.py), [lab integration](../tests/integration/test_learning_labs.py), [browser](../tests/e2e/test_browser.py) |
| `etl-testing` | 5 | Source/Target mapping/transformation/rejects, isolated batches/replay/recovery, SUCCESS ≠ correctness | [Task 10 unit](../tests/unit/test_task10.py), [Task 10 integration](../tests/integration/test_task10.py), [ETL guidance](../tests/integration/test_etl_guidance.py), existing ETL browser execution/reveal |
| `api-testing` | 4 | Actual local HTTP contracts, pagination, bounded retries and persisted ingestion/idempotency; JSON submission rather than assumed SQL shape | Task 10 unit/integration, existing API browser/editor/evidence/reveal/history |
| `fabric-testing` | 3 | Layer/run/schema/publication evidence and provenance; immutable independent grading expectations | [cloud unit](../tests/unit/test_cloud.py), [cloud integration](../tests/integration/test_cloud.py), cloud browser tests |
| `adf-testing` | 3 | Copy/replay/recovery, watermark context, local mutation invalidation, full portable referenced evidence | Cloud unit/integration; browser export/import/replay/reset round trip |
| `onelake-testing` | 2 | Partition/manifest and reference freshness; UTC boundaries and incomplete evidence | Cloud tests/guidance/browser, no live-provider claim |
| `azure-testing` | 2 | Manifest/routes/access observations; permission evidence distinct from data defect/incomplete observations | [Task 12 unit](../tests/unit/test_task12.py), [Task 12 integration](../tests/integration/test_task12.py), foundations browser |
| `databricks-testing` | 2 | Accepted/rejected/quarantine reconciliation and version-aware updates/replay/deletion | Task 12 unit/integration/browser; independent truth, not Spark/Delta runtime emulation |
| `synapse-testing` | 2 | Fact/dimension key/mapping reconciliation, reporting grain/fanout/exact totals | Task 12 unit/integration/browser |
| **Executable total** | **36** | All IDs/requirements/fixtures/scoring/security/session history stay compatible | Enumerate actual catalog/profiles, not only one smoke lesson. At least one SQL and one non-SQL real learning loop on an integration change. |
| `ai-test-automation` | **30 metadata / 1 available** | Ten ordered modules/unique IDs, ENG/VIE, `m01-l01` full sections/copy/local practice; 29 planned no content/launch/completion; no session/AI/grading/persistence | [tutorial unit](../tests/unit/test_tutorials.py), [tutorial API](../tests/integration/test_tutorial_api.py), [public tutorial browser](../tests/e2e/test_tutorial_browser.py) |

Existing platform catalog size on develop: **10 courses = nine executable + one tutorial**, not 66 executable labs or 30 available automation lessons. Counts remain meaningful by `learning_kind`. New track cards must not erase the Automation subject/course or relabel it as cloud evidence.

## 3. Shared shell and route acceptance

Verify all three tracks against [UI contract](UNIFIED_PLATFORM_INTEGRATION_CONTRACT.md#2-ownership-and-ui-inheritance), on 375/768/1280, ENG/VIE, Dark/Light, mouse and keyboard. Existing [browser tests](../tests/e2e/test_browser.py) include Task 20/20.1 theme, focus, menu containment/link hits, Escape/outside/focus restoration/mutual exclusion and course introduction/reveal behavior; extend instead of adding a framework.

U2 targeted checks: homepage three cards, Data landing nine executable links, Banking honest Planned, Automation existing tutorial link; all existing catalog/course/player routes preserved; language/theme preferences and document language survive refresh/navigation; no horizontal overflow, clipped labels/overlapping menu or smaller essential text; focus contrast/visible ring and SVG disclosure states retained. Verify menu scrolling includes every subject after new track navigation.

Route matrix test dimensions for each implemented route in [contract](UNIFIED_PLATFORM_INTEGRATION_CONTRACT.md#5-route-and-track-compatibility-contract):

| Dimension | Required check |
|---|---|
| Direct GET / reload | SPA index only for exact valid routes; API/static missing paths stay404; new `/learn/*` matches do not show endless loading. |
| History | Internal Link push/replace, browser back/forward, preserved lesson session query/`new=1`, native tutorial section anchors. |
| Public discovery | No private user/session/query/submission payload in catalog/tutorial/track responses; no POST side effect from reading. |
| Auth return | Guest gates protected lab/private features, safe same-origin known next returns after login; reject external/protocol-relative/encoded bypass/unknown prefixes. Preserve demo signup Coming Soon. |
| Legacy | `/learn/lab_*` SQL alias preserves query/replace; all old `/courses/*`, `/subjects/*`, My Learning/history/pipeline remain usable. |
| Failure | Bank/artifact offline does not break header/Data QA/tutorials; honest unavailable/planned/error, no invented progress. |

Run meaningful contrast/manual screenshot checks; a viewport test is not physical-device/screen-reader/Safari/Firefox certification. Report those explicitly untested unless actually run.

## 4. Banking domain and adapter verification

Accepted MiniBanking independent tests/API/OpenAPI models are pinned to `2d7bf66`. Its domain [CI](https://github.com/taodo/MiniBanking/blob/2d7bf660611cbfe853489b9014f0453acbfcf1c8/.github/workflows/regression.yml) runs Linux pytest, actual localhost HTTP smoke and Newman whole collection + independent SQLite oracle; Windows readiness/SQL portability. In-process ASGI is not actual TCP. Do not treat Task 9 draft evidence as accepted release or change its harness/gates.

Before U6 public writes, use fresh *runner-owned* SQLite contexts and independent read-only SQL connections to observe committed rows; never point fixtures/CLI/init/Newman at learner, deployed demo or retained banking files. Assert:

- Strict VND integers/overflow/limit/funds, owned debit, participant lookup and bounded stable history; equal global totals are insufficient.
- New transfer201 then same-key/body replay200 preserve one transfer, two correct ledger sides and one scoped reference; different body409 has no posting, rejected/500 precommit paths preserve all rows.
- Per-account opening + credits − debits, exact from/to deltas, paired ledger accounts/amount/currency, total conservation, uniqueness/FKs and durable reopen behavior.
- Old bank token fails after app restart; separately authorized re-login recovers known same-context/key/body operation. Response timeout remains UNKNOWN until reconciled; no blind new key.
- Context A/B ownership/visitor isolation, same bank mock role but different files/app/token stores, no cross-read/mutation/evidence retrieval; shared platform usernames must not grant other browser sessions' contexts.
- Platform cookie/CSRF/account-change controls stay authoritative at BFF, foreign/expired bank token cannot authenticate platform, spoofed context/header rejected. No browser Authorization/Cookie forwarded upstream; upstream body/error/headers redacted.
- Fixed upstream/path/method/ID/paging allowlist, SSRF/redirect/header-injection tests, denied docs/admin/seed/reset/debug/CLI/SQL/file endpoints, no public SQLite access. Limits, contention, queue/context/TTL cleanup and unavailable-service behavior.
- JavaScript integer-safe boundary and an approved lossless representation beyond 2^53−1; no rounded bank money. Existing Data QA Decimal JSON stays unchanged.

Eight accepted content IDs: `auth-ownership`, `exact-deltas`, `replay-new`, `conflict-preservation`, `lookup-history`, `missing-side`, `rollback-retry`, `loss-durable`. Test ENG/VIE parity after authored translation, prediction/hints/separate answer/rubric and local self-mark provenance. Existing bank evidence importer supports Task 5/6 snapshots with 1MiB/depth/node/row limits and secret-field rejection; Task 9 format needs a separately reviewed version/mapping, not automatic acceptance.

Future assessment must use independent expectations and observable financial state, not reexecute the transfer service as its oracle. Free-text rubric is self-check unless an explicit deterministic assessor is implemented; no LLM semantic-grading claim.

## 5. Independent Automation QA verification

Automation currently has no implemented framework/service. Future separate bootstrap/release tests (see [bootstrap roadmap](UNIFIED_PLATFORM_ROADMAP.md#recommended-separate-automation-bootstrap-task-not-u1-implementation)) must validate config/target allowlists/timeouts/retries, fixture isolation, reusable API assertions, safe read-only DB oracle, Playwright selectors/assertions/cleanup and bounded CI. Demonstrate incorrect output/fanout/replay/weak assertions cause the expected failure, rather than self-comparison or status-only assertions.

Producer/consumer contract tests: schema and major/minor compatibility, approved producer commit/framework/content release, stable course/lesson IDs, bilingual completeness, archive/digest/license, runtime/command/status/completeness and expected-defect distinction. Reject malformed/unknown/oversized/unapproved/raw secret/HTML/executable hook/path traversal/remote URL artifacts; never update grading truth or claim authenticated provenance from a learner-supplied SHA. Consume reviewed pinned versions in platform PRs, not startup synchronization.

Local/CI execution stays in Automation domain. Public runner APIs/credentials/mounts are absent; tests must confirm unavailable actions instead of simulating fake executions. If a future sandbox is proposed: adversarial code isolation/egress/secrets/CPU-memory-time-file limits/cleanup/abuse/cross-tenant testing and independent security approval are prerequisites for any third execution service.

## 6. CI and cross-repository release gates

| Gate | Producer responsibility | Platform consumer responsibility |
|---|---|---|
| Domain PR | Independent domain QA, exact SHA/base, actual evidence/limits, review + user approval→develop | Do not auto-import a green but unapproved domain branch. |
| Integration PR | Notify API/content/package/evidence compatibility changes, old/new examples and approved pin/license/digest | Validate UPIC version matrix, typed consumer fixtures/negative cases, UI parity, route/security/data isolation and all relevant legacy regressions. |
| Release | Record domain accepted API/framework/content revisions and rollback compatibility | Platform final-head CI/review/user approval→develop; separate release gate→main→deployment, retained-data preservation plan, capability-off default. |
| Failure | Preserve sanitized diagnostics/unknown operations; no false PASS | Reject incompatible artifact, disable Banking writes, keep Data QA/tutorials/navigation working; no reset/delete/reseed. |

Existing platform [workflow](../.github/workflows/test.yml) already runs frontend build, unit, PostgreSQL integration and browser suites plus container smoke/restart and isolated demo HTTPS/Named Tunnel/public-account checks. [demo_verify.py](../scripts/demo_verify.py), [demo security](../tests/unit/test_demo_security.py), [demo integration](../tests/integration/test_demo.py), [public accounts](../tests/integration/test_public_demo.py), [demo browser](../tests/e2e/test_demo_browser.py) enforce exact hosts/proxies/origin/CSRF/password restrictions/history. Extend only relevant checks in an approved implementation PR; no new CI framework in U1.

Public release rehearsal uses separate disposable deployment data and no externally opened tunnel automatically. Retained PostgreSQL volumes, 15 operator-reported demo accounts and banking files are protected. Never `down -v`, provision/Prepare against retained data, reset/reseed or manipulate tunnel tokens. Actual deployment/image SHA and retained-account count require a later authorized private operator check; never publish credentials.

## 7. Rollback/failure verification and U1 evidence

Rehearse on isolated state: Banking off/down/timeout/version mismatch, token expiry/restart, pending transfer preserved across platform re-auth, last-good Automation artifact on missing/invalid release, feature-off direct routes, code rollback with compatible schemas and retained progress. Assert no fake completion, silent truncation, new-key retry or lost Data QA drafts/history. Context cleanup deletes only explicitly disposable owned state; pending/retained evidence follows approved policy.

U1 EXECUTED: fetched platform refs/branch/ancestor verification; read accepted MiniBanking Git objects, Task 9 PR/Issue and Automation initial commit/refs; parsed actual platform catalog/manifest; anonymous HTTPS GET deployment observations; lightweight Markdown/reference/route/API/count and documentation-only diff validation. Commands/results and PR/head/remote verification are recorded in handoff. No full local regression, frontend build, domain execution, SQLite/PG queries, tunnel changes, deployment, physical-device or runtime OpenAPI generation performed. Historical Task 21.1 green CI is prior evidence, not a U1 rerun.

Acceptance for U1: four linked, internally consistent documents; every invented integration capability clearly PROPOSED/UNRESOLVED; all relative source references exist; pinned domain source paths resolve; no code/config/data changes; Git diff whitespace clean and source worktrees preserved. READY_FOR_REVIEW describes architecture readiness only; later domain security/specification gates remain explicit.
