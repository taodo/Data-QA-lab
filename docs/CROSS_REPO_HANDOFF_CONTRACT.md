# C2-A — Manual cross-repository review handoff and evidence contract

Status: documentation-only manual contract for independent review. No automated
validator, dispatch, domain write, new credential or protocol activation is added.
Engineering objective: make a human handoff traceable to a real domain receipt,
reviewer and immutable source. Learning objective: separate delivery, technical
review, feasibility and implementation/merge/deployment permission.

Authority: [Issue #44](https://github.com/taodo/Data-QA-lab/issues/44), following
[Option A decision](https://github.com/taodo/Data-QA-lab/issues/43#issuecomment-6138074009).
Keep [C1 v1 runbook](CROSS_REPO_COORDINATION.md), [UPIC](UNIFIED_PLATFORM_INTEGRATION_CONTRACT.md),
[Architecture](UNIFIED_PLATFORM_ARCHITECTURE.md), [Roadmap](UNIFIED_PLATFORM_ROADMAP.md)
and [Test Strategy](UNIFIED_PLATFORM_TEST_STRATEGY.md) authoritative within their scopes.
This document does not revise Banking D1–D7/F1–F3 or authorize C2-B.

## 1. Verified audit snapshot — 2026-10-13

| Repository / ref | Exact inspected SHA / identity | Source-grounded result |
| --- | --- | --- |
| Data-QA-lab / origin/feature/develop | `ac0bb35135c17a69213799e77aaac44a5bf8e541`; repository ID `1401920710` | Accepted C1; C2-A branch starts here. Integration source is not deployed-image proof. |
| Data-QA-lab / origin/main | `7af22c30ea81a0cbba42ff145c9beb3c7439f230`; same repository ID | Live C1-A workflow/handler/runbook inspected separately; do not promote main/develop into each other. |
| MiniBanking / feature/develop | `7a77ec579d7ff0edf2299d3755155573fee1ec15`; repository ID `1411382010` | B1 audit and FastAPI factory inspected: bank service owns existing SQLite/app-local auth, not a platform context broker. |
| Automation-QA-Lab / feature/develop | `9c00f59b0f6ddab83cbb6af9ea5735cefb09b8cd`; repository ID `1415072664` | A1 architecture/evidence source inspected: local/CI localhost HTTP + disposable SQLite and independent numeric assertions; no public runner/Playwright service. |

Pinned domain sources: [Banking B1 audit](https://github.com/taodo/MiniBanking/blob/7a77ec579d7ff0edf2299d3755155573fee1ec15/docs/INTEGRATION_READINESS_AUDIT.md),
[bank app factory](https://github.com/taodo/MiniBanking/blob/7a77ec579d7ff0edf2299d3755155573fee1ec15/backend/main.py),
[A1 architecture](https://github.com/taodo/Automation-QA-Lab/blob/9c00f59b0f6ddab83cbb6af9ea5735cefb09b8cd/docs/ARCHITECTURE.md),
[A1 evidence model](https://github.com/taodo/Automation-QA-Lab/blob/9c00f59b0f6ddab83cbb6af9ea5735cefb09b8cd/src/automation_qa/evidence.py).
Refs/files and repository IDs were read through authenticated GitHub access.
Anonymous domain requests returned 404; that is not proof a repository is absent.
No domain checkout, writes, runtime tests or permission changes were performed.
U1's earlier Task 9/unimplemented-Automation observations are historical: B1
records Task 9 acceptance; A1 exists now. Those U1 files are not rewritten here.

[C1 accepted report](https://github.com/taodo/Data-QA-lab/issues/39#issuecomment-6124358643)
and [C1-A smoke report](https://github.com/taodo/Data-QA-lab/issues/41#issuecomment-6137030840)
were read with current comments. Authentic ledgers observed:
[Banking](https://github.com/taodo/Data-QA-lab/issues/37#issuecomment-6135565204)
`c1-37-6135561480`, CLOSED revision 2 (request/cancel only), and
[Automation](https://github.com/taodo/Data-QA-lab/issues/38#issuecomment-6136717419)
`c1-38-6136715447`, CLOSED revision 4 (full smoke lifecycle).
These test cycles neither reviewed nor approved domain implementation. The smoke
report does not claim live concurrency, duplicate delivery or ambiguous-write
recovery verification. C2-A observes existing evidence; it sends no new commands.

## 2. Actors and ownership

| Actor | Owns / must do | Cannot infer or authorize |
| --- | --- | --- |
| Platform maintainer | Select authorized platform scope, pin source, record cross-links, verify returned evidence, issue explicit v1 transitions using verified platform write/admin permission | Cannot self-certify domain review or treat bank/automation green CI as platform integration approval |
| Domain owner | Decide which existing domain Issue/PR is authoritative, appoint reviewer and acknowledge scope/receipt | Cannot grant platform merge/deployment permission; domain receipt is not code approval |
| Domain human reviewer | Read exact source/requirements, post attributed verdict/test evidence on that domain artifact; state limits/conflicts | Not replaced by status bot or anonymous/AI prose; cannot approve outside delegated scope |
| GitHub Actions status bot | Validate platform opt-in command and update same-Issue v1 ledger | Does not contact domain, validate this envelope, review code or awaken another chat |
| Final human approver | Explicit scoped implementation/merge/release decision on reviewed exact head; platform admin closes v1 cycle when appropriate | CLOSED does not grant any other permission or close authoritative Issues |

No new credential is needed. Humans use their existing authorized GitHub access;
C2-A itself makes no domain writes. Future human domain comments still need owner
authorization for that specific artifact. Do not create a domain Issue without
separate permission. An existing Issue/PR URL alone is not permission to use it.
Reviewers must be appointed by the domain owner, with their real identity and
current role checked there. An external read-only reviewer needs a verifiable
owner delegation; claiming collaborator status is insufficient. Platform v1
write/admin checks remain independent, with effective admin required for close.
If either required identity/role/delegation cannot be verified, record UNKNOWN
and stop advancement; do not grant new permissions to make the process work.

## 3. Manual sequence and milestone mapping

These are human process milestones, NOT new implemented C1 states. LINKED and
RECEIVED remain notes; no invented `/coord link`, `/coord receive` or v2 command.

| Milestone | Required human action / proof | Actual v1 relationship |
| --- | --- | --- |
| REQUESTED | Authorized platform scope + new explicit request on #37 or #38; source command/ledger IDs retained | Request creates AWAITING_REVIEW; bot routing is not domain delivery |
| LINKED | Select existing owner-authorized domain Issue/PR; human cross-link both artifacts and the current correlation | No state transition; delivery remains unconfirmed until receipt |
| RECEIVED | Named domain human posts explicit receipt on domain artifact, confirms correlation, source SHA, scope and responsible reviewer | Still AWAITING_REVIEW; platform mirror of a link is not domain receipt |
| REVIEWED | Domain reviewer posts review there; platform maintainer independently checks attribution, exact SHA, requirements, test/CI and completeness | Explicit review command records review-posted, needs-changes or blocked; not prose alone |
| AWAITING_APPROVAL | Evidence/technical verdict known; platform feasibility separate; maintainer explicitly hands off appropriate reviewed cycle | REVIEW_POSTED → AWAITING_HUMAN_APPROVAL; no implementation permission implied |
| CLOSED | Authorized admin acknowledges completed handoff or cancels known-safe active cycle; preserve outcome and limitations | Closes coordination cycle only, never the authoritative Issue or another approval gate |

End-to-end: inspect current ledger/holds and requirements → request → select
authorized target → cross-link → receipt → domain review → platform independent
verification → explicit v1 outcome → scoped human decision separately → close.
For needs-changes, revise the authorized source, obtain fresh receipt/review for
the new full SHA and explicitly resume within budget. No review of old SHA is
silently reused. A legitimate blocked review can be recorded as BLOCKED with its
actual evidence; it cannot be treated as complete review-posted or approval.

## 4. Proposed documentation envelope: qa-handoff/1.0

This is a human-authored evidence proposal, not a JSON schema/API/validator
implemented by C2-A, not `qa-coordination/v2`, and not extra trusted bot fields.
Store a sanitized record in a platform human comment with links to domain source;
the domain's original receipt/review remains authoritative. A digest or JSON
format alone does not authenticate authorship. Never paste it into a bot ledger.

Required keys must be present; null/empty fields explicitly mean UNKNOWN or
not yet available. DRAFT/BLOCKED records may retain those gaps. VERIFIED means
the named human actually completed the checklist below; it is not an automated
attestation. Missing essential receipt/reviewer/SHA/evidence prevents VERIFIED.

| Field | Required meaning / validation rule |
| --- | --- |
| `schema_version`, `example_only` | Literal `qa-handoff/1.0`; boolean example flag. Synthetic records never become real evidence without replacement/reverification |
| `handoff_id`, `record_status`, `process_milestone` | Human ID `<v1-correlation>-h<attempt>`; DRAFT/VERIFIED/BLOCKED; only the six human milestones above. Attempt is manual, not bot revision |
| `origin` | Exact platform repo + numeric ID, Issue 37/38, immutable request comment ID/URL, v1 correlation, ledger URL and observed expected revision |
| `target` | Exact allowlisted domain repo + numeric ID; owner-authorized Issue/PR URL, authority/delegation reference. Never an arbitrary upstream URL |
| `reviewed_commit_sha` | Full lowercase 40-hex domain commit, not branch/tag/short SHA; null before a review is pinned. Record separate platform SHA if integration is also reviewed |
| `actors` | Requester, receiver, reviewer and verifier: login, numeric ID if independently available, role/delegation evidence and verification method/time. Missing IDs require explicit limitation and independent identity confirmation, not invented IDs |
| `receipt_url`, `review_url` | Original immutable domain comment/review links confirming same correlation, scope and SHA; null if missing. Update timestamps/body snapshots detect edits, not just comment IDs |
| `review_status` | NOT_REVIEWED/COMPLETE/INCOMPLETE/BLOCKED for review evidence; COMPLETE can include a negative technical verdict and is not approval |
| `verdict` | Technical: NOT_REVIEWED/APPROVE/APPROVE_WITH_NOTES/NEEDS_CHANGES/BLOCKED; platform feasibility: NOT_ASSESSED/FEASIBLE/CONDITIONAL/BLOCKED. Human approval separate |
| `evidence` | Requirement IDs + result per requirement; pinned diff/source URL; test entries with exact command, observed result, tested SHA, source result URL and limitations; CI entries with run/job URL, head SHA, event/attempt, conclusion, checked time. A NOT_RUN entry is not PASS |
| `timestamps` | Requested/received/reviewed/verified UTC RFC3339 with Z, or null when unknown; record comments' created/updated times and source observation time. Check plausible order, no invented execution times |
| `verification` | Method MANUAL_UI/API_READ/SOURCE_READ or NOT_CHECKED, human verifier, checked links/identity/SHA/requirements and remaining gaps. Name actual API endpoints only if used; UI inspection is not an API permission check |
| `human_decision` | Separate implementation, merge and deployment records, each NOT_GRANTED/GRANTED/DENIED + scoped human actor, exact repo/head, decision link/time/conditions. null actor/link for NOT_GRANTED; GRANTED requires explicit verified authorization |
| `redaction` | Checked human/time or NOT_CHECKED; removed categories, approved visibility and unresolved leak flag. Do not copy raw credentials/PII/DB evidence |
| `limitations` | Explicit missing evidence, source drift, freshness, artifact expiry and unverified capabilities; no silent defaults |

Optional: sanitized body/artifact SHA-256 computed by the verifier, artifact
expiry, platform reviewed SHA, superseded-record URL, license/contract version
and restricted operator evidence pointer. Hashes do not replace source access,
independent expectations or authorization. Unknown major versions stop acceptance;
additive minor changes require an explicitly reviewed manual mapping. No runtime
version negotiation or storage/progress migration is introduced.

### Synthetic Banking draft — not a delivered or accepted handoff

Real repository IDs/source pins below are audited context; correlation, record
IDs and target tokens are illustrative. Replace tokens with owner-authorized
canonical references and obtain actual receipt/review before using this record.
No fabricated domain Issue number, actor identity, test PASS or approval is given.

```json
{
  "schema_version": "qa-handoff/1.0", "example_only": true,
  "handoff_id": "c1-37-900000001-h1", "record_status": "BLOCKED", "process_milestone": "LINKED",
  "origin": {"repository": "taodo/Data-QA-lab", "repository_id": 1401920710, "issue": 37, "request_comment_id": 900000001, "request_url": "<PLATFORM_REQUEST_URL>", "correlation": "c1-37-900000001", "ledger_url": "<PLATFORM_LEDGER_URL>", "expected_revision": 1},
  "target": {"repository": "taodo/MiniBanking", "repository_id": 1411382010, "authority_url": "<AUTHORIZED_DOMAIN_ISSUE_OR_PR_URL>", "authorization_url": "<DOMAIN_OWNER_AUTHORIZATION_URL>"},
  "reviewed_commit_sha": null,
  "actors": {"requester": null, "receiver": null, "reviewer": null, "verifier": null},
  "receipt_url": null, "review_url": null, "review_status": "NOT_REVIEWED",
  "verdict": {"technical": "NOT_REVIEWED", "platform_feasibility": "NOT_ASSESSED"},
  "evidence": {"requirements": ["Banking F1", "Banking F2", "Banking F3"], "diff_url": null, "tests": [], "ci": []},
  "timestamps": {"requested_at": null, "received_at": null, "reviewed_at": null, "verified_at": null},
  "verification": {"method": "NOT_CHECKED", "checks": [], "gaps": ["Missing domain receipt, reviewer attribution and reviewed SHA"]},
  "human_decision": {"implementation": {"status": "NOT_GRANTED", "actor": null, "decision_url": null}, "merge": {"status": "NOT_GRANTED", "actor": null, "decision_url": null}, "deployment": {"status": "NOT_GRANTED", "actor": null, "decision_url": null}},
  "redaction": {"status": "NOT_CHECKED", "removed_categories": [], "visibility": "<OWNER_APPROVED_VISIBILITY>", "unresolved_leak": false},
  "limitations": ["Synthetic template only; no domain write or permission check performed"]
}
```

### Synthetic Automation draft — no review inferred from A1 source/CI

```json
{
  "schema_version": "qa-handoff/1.0", "example_only": true,
  "handoff_id": "c1-38-900000002-h1", "record_status": "DRAFT", "process_milestone": "REQUESTED",
  "origin": {"repository": "taodo/Data-QA-lab", "repository_id": 1401920710, "issue": 38, "request_comment_id": 900000002, "request_url": "<PLATFORM_REQUEST_URL>", "correlation": "c1-38-900000002", "ledger_url": "<PLATFORM_LEDGER_URL>", "expected_revision": 1},
  "target": {"repository": "taodo/Automation-QA-Lab", "repository_id": 1415072664, "authority_url": "<AUTHORIZED_DOMAIN_ISSUE_OR_PR_URL>", "authorization_url": "<DOMAIN_OWNER_AUTHORIZATION_URL>"},
  "reviewed_commit_sha": null,
  "actors": {"requester": null, "receiver": null, "reviewer": null, "verifier": null},
  "receipt_url": null, "review_url": null, "review_status": "NOT_REVIEWED",
  "verdict": {"technical": "NOT_REVIEWED", "platform_feasibility": "NOT_ASSESSED"},
  "evidence": {"requirements": ["A1 independent oracle", "A1 expected-defect detection", "No public runner"], "diff_url": null, "tests": [], "ci": []},
  "timestamps": {"requested_at": null, "received_at": null, "reviewed_at": null, "verified_at": null},
  "verification": {"method": "NOT_CHECKED", "checks": [], "gaps": ["No received/reviewed evidence yet"]},
  "human_decision": {"implementation": {"status": "NOT_GRANTED", "actor": null, "decision_url": null}, "merge": {"status": "NOT_GRANTED", "actor": null, "decision_url": null}, "deployment": {"status": "NOT_GRANTED", "actor": null, "decision_url": null}},
  "redaction": {"status": "NOT_CHECKED", "removed_categories": [], "visibility": "<OWNER_APPROVED_VISIBILITY>", "unresolved_leak": false},
  "limitations": ["Synthetic template only; current A1 source is not a review receipt"]
}
```

## 5. Human verification checklist and failure decisions

Check before recording a successful review/handoff and again before approval:

| Check | Required independent observation / stop rule |
| --- | --- |
| Canonical links | Exact HTTPS github.com owner/repo; platform ID 1401920710, bank ID 1411382010, automation ID 1415072664; correct Issue/PR/comment belongs to that repo and scope. Reject lookalike hosts/owners, URL credentials, unexpected query/redirect targets or arbitrary artifact fetches |
| Authority and receipt | Domain owner authorized artifact/reviewer; domain human receipt matches correlation/source SHA/requirements; missing receipt = UNCONFIRMED, stop success/handoff |
| Actor | View original account/comment/review attribution; obtain numeric ID and current role/delegation through authorized UI/API where available. Log method and time; pasted login/author_association, bot/AI prose and screenshot are insufficient |
| Immutable source / freshness | Resolve full commit and diff, match review subject and tested SHA. Observe current head/expected revision immediately before transition/approval; moved branch = STALE, re-review. No universal freshness period substitutes for checking scope/source changes |
| Test and CI truth | Open original logs/job/run and exact SHA/event/attempt; record actual command/assertion/results and limitations. A PR merge ref, different SHA, badge, green title, untrusted uploaded JSON or expected-defect nonzero exit without correct assertion evidence is not proof |
| Requirements / completeness | Each requested requirement maps to independent evidence or explicit gap; no status-only truth. Banking admission/commit/UNKNOWN and Automation HTTP-success/assessment/completeness remain distinct |
| Integrity and replay | Read original created/updated timestamps and body; record sanitized snapshot/digest if needed. Edited/deleted source, stale revision, competing handoff, conflicting verdict or changed evidence = HOLD; preserve prior records, obtain explicit superseding record |
| Access / redaction | Open references with authorized access; unreachable/expired artifact = INCOMPLETE, no inferred PASS. Do not widen repository visibility, copy secrets or export raw logs/DBs to fix access. Suspected leak = STOP and owner security escalation |
| Human gates | Review and platform feasibility do not imply implementation, merge or deployment. Check explicit scoped actor/head/decision reference separately; no permission = NOT_GRANTED |

Manual duplicate identity is `(origin repo, request comment ID, target authority,
reviewed SHA, handoff attempt)`. Compare existing records first; two operators
designate one owner and reconcile notes instead of posting another request.
Record a superseding link when source changes; never silently overwrite evidence.
This is a human discipline, not transactional exactly-once enforcement.

On failed CI, stale head, unauthorized/unverified reviewer, inaccessible repo,
incomplete evidence, missing receipt, conflicting edits or unknown delivery:
record BLOCKED with UNKNOWN details, owner and corrective evidence required; stop successful
review/handoff/approval. A verified negative technical review may use v1
needs-changes/blocked, with explicit limitations. Do not poll/retry indefinitely.
Read-only fallback is a sanitized platform note saying delivery is unconfirmed;
it is not a substitute domain receipt. Escalate to both owners and the human
approver. If API access is unavailable, use authorized UI and record MANUAL_UI;
if that still cannot prove identity/source, leave NOT_CHECKED and stop.

C1 run-history/uncertain-write holds take precedence: no rerun, new cycle,
deleted ledger/run history, manual CLI mutation or expiry-based bypass. Follow
the existing runbook's owner-reviewed recovery. Admin cancellation is only for
a known-safe active cycle, not proof that an ambiguous write had no effect.

## 6. Human decision matrix

| Decision | Authority / evidence | Does NOT grant |
| --- | --- | --- |
| Domain technical APPROVE / WITH NOTES / NEEDS CHANGES / BLOCKED | Appointed domain reviewer on exact source, requirement evidence and limits | Platform feasibility or permission to implement/merge/deploy |
| Platform FEASIBLE / CONDITIONAL / BLOCKED | Platform maintainer checks consumer contracts, ownership, security and outstanding conditions | Domain technical approval or capability activation |
| Implementation GRANTED | Explicit user/owner approval of named task/scope/base; separate authoritative Issue where needed | Merge or production permission |
| Merge GRANTED | Explicit authorized human approval of exact repository/PR/head after independent review and required checks | Merge of another repo, next task or deployment |
| Deployment GRANTED | Separate operator/user release approval of reviewed versions/topology/data-preservation plan | Broader token grants, unreviewed domain release or public code execution |
| Coordination CLOSED | Admin v1 acknowledgment/cancellation | Any of the above, authoritative Issue closure, learner completion or new task |

Conditions must be explicit and satisfied; APPROVE_WITH_NOTES is not unconditional
readiness. Never treat the same person posting a routing command as proof of
independent technical review. Disclose conflicts and obtain another reviewer.

## 7. Copyable human templates — NOT executable or sent by C2-A

Replace angle-bracket tokens after verification. Do not paste fenced/quoted
commands expecting execution, and do not post a template with unresolved tokens.
Human domain comments below are future owner-authorized actions, not C2-A writes.

```text
Manual domain handoff (no /coord command here)
Platform authority: <PLATFORM_ISSUE_AND_REQUEST_COMMENT_URL>
Correlation / expected platform revision: <CORRELATION> / <REVISION>
Domain authority and owner permission: <AUTHORIZED_DOMAIN_URL> / <OWNER_REFERENCE>
Review exact commit: <FULL_DOMAIN_SHA>
Requested requirements / exclusions: <BOUNDED_SCOPE>
Receipt needed from: <APPOINTED_DOMAIN_HUMAN>; delivery remains UNCONFIRMED.
This requests review only, not implementation, merge or deployment.
```

```text
Domain human receipt
Received correlation <CORRELATION> from <PLATFORM_SOURCE_URL>.
Authorized scope/source <REQUIREMENTS> / <FULL_SHA>; authority <DOMAIN_URL>.
Responsible reviewer <LOGIN_AND_VERIFIED_ID_OR_EXPLICIT_LIMITATION>.
Owner delegation <REFERENCE>; mismatches/blockers <NONE_OR_DETAILS>.
No technical verdict or implementation/merge/deployment approval yet.
```

```text
Domain review evidence
Correlation <CORRELATION>; receipt <URL>; reviewed full SHA <SHA>; diff <URL>.
Reviewer identity/role/delegation <VERIFIED_REFERENCE_AND_METHOD_TIME>.
Requirements → actual assertion/test result → source logs/CI SHA <MATRIX>.
Technical verdict <APPROVE|APPROVE_WITH_NOTES|NEEDS_CHANGES|BLOCKED>.
Observed execution/assessment/completeness and NOT_RUN limitations <DETAILS>.
Original created/updated time, redaction, unresolved risks <DETAILS>.
This is a technical review, not platform integration or release authorization.
```

Exact current v1 grammar (case/order fixed; correlation/revision tokens are
placeholders). Commands must be the FIRST unindented line of a NEW unedited
human comment. One command only, optional evidence notes after a blank line:

```text
/coord request target=banking type=review
/coord request target=automation type=review
/coord review id=<CORRELATION> revision=<REVISION> outcome=review-posted
/coord review id=<CORRELATION> revision=<REVISION> outcome=needs-changes
/coord review id=<CORRELATION> revision=<REVISION> outcome=blocked
/coord resume id=<CORRELATION> revision=<REVISION>
/coord handoff id=<CORRELATION> revision=<REVISION>
/coord close id=<CORRELATION> revision=<REVISION> decision=acknowledged
/coord close id=<CORRELATION> revision=<REVISION> decision=cancelled
```

### Complete illustrative Banking sequence — no real handoff performed

1. Maintainer reads #37's [F1–F3 review](https://github.com/taodo/Data-QA-lab/issues/37#issuecomment-6123495278)
   and obtains authorized review scope. A new permitted banking request produces
   a NEW correlation; never reuse the CLOSED smoke correlation/revision above.
2. Domain owner selects an existing authorized bank artifact or separately
   authorizes creating one. Human links it both ways; reviewer receipt names
   exact bank SHA and F1/F2/F3. No receipt: stop at BLOCKED draft, as in the sample.
3. Reviewer checks security split, ACCEPT/SUBMIT/crash-window proof and every
   quota/retention owner; source-only review explicitly lists runtime NOT_RUN.
   If money evidence is required, use independent per-transfer/account/ledger
   invariants on authorized disposable state, not total-only/HTTP SUCCESS proof.
4. Maintainer verifies original review/identity/SHA/requirements, records actual
   technical outcome with explicit v1 review command. Needs-changes requires
   fresh evidence after authorized amendment/resume, never automatic B2 work.
5. A complete positive technical review permits explicit handoff for separate
   platform feasibility and user decision. Admin acknowledges that coordination
   exchange (or cancels known-safe blocked cycle); #37 remains authoritative.
   B2/U5 implementation, domain merge and deployment remain separate gates.

### Complete illustrative Automation sequence — no real handoff performed

1. Maintainer reads #38's [feasibility review](https://github.com/taodo/Data-QA-lab/issues/38#issuecomment-6123504304),
   obtains bounded scope and requests automation review with a fresh correlation.
   Current A1 does not authorize website content sync, trusted ingestion or runner.
2. Human chooses owner-authorized existing Automation Issue/PR, cross-links;
   domain human receipts exact A1/change SHA, framework/content/evidence scope
   and exclusions. Unknown receipt/identity remains draft, as in the sample.
3. Reviewer supplies actual normal-suite evidence and, where relevant, the
   controlled wrong_total assertion: independent expected 500 versus observed
   response 450, while SQLite remains 500. Intentional pytest failure alone
   cannot prove defect detection; distinguish HTTP execution from assessment.
   Future changes must be reviewed/tested on their actual SHA, not this old pin.
4. Maintainer verifies logs/CI/source/attribution, preserves NOT_RUN/incomplete
   fields and records explicit actual outcome. Positive review/handoff is only
   for its reviewed scope; no platform-verified learner progress follows.
5. Human separately decides any content integration scope/head, then admin
   closes the coordination exchange. Domain framework and platform tutorial UI
   retain separate ownership/PRs; no public execution, C2-B or auto-next-task.

## 8. Cost, retention, compatibility and staged adoption

Manual overhead: one authorized request, two cross-links, explicit domain receipt,
domain review and independent platform verification per handoff. Human attention
is the main cost; use bounded requirement matrices and existing artifacts rather
than copying long logs. No AI/service fee, new hosted worker, token or dependency.
C1 retains its finite Actions/API use: at most one active cycle per Issue, eight
accepted events, three review rounds and ten lifetime cycles; do not delete closed
cycles to reclaim capacity. Its 24-hour command/history window is not an evidence
retention policy or permission to bypass unresolved delivery.

Retain canonical Issue/PR/receipt/review/decision references and source pins under
each owner's existing GitHub retention/access policy. Record artifact expiry;
before a gate recheck access or obtain owner-approved sanitized durable evidence.
C2-A sets no automatic deletion/export or new retention duration. Keep only
minimal sanitized extracts, no DBs, tokens, passwords, customer/learner PII,
environment dumps or raw reports. Public platform comments must not reveal
private repository material without owner approval; restricted evidence may be
accessed by authorized reviewers but inaccessible proof stays INCOMPLETE.
No visibility widening, secret redistribution or destructive evidence cleanup.

Adoption: independently review this doc → explicit human merge approval on its
exact head → separately authorize a small manual pilot using existing artifacts
and fresh approved coordination cycle → record limitations → evaluate overhead.
No live pilot is run by C2-A. Falling back means stopping new handoffs and keeping
v1/evidence unchanged; no workflow disablement, database or deployment is needed.

Future Option B needs its own Issue, user approval, threat model, allowlisted
sender/receiver contracts, scoped GitHub App installation, custody/rotation and
revocation, authenticated receipt/evidence return, dual-repo permission review,
durable idempotency/partial-write/concurrency limits, cost/retention policy,
negative tests, release/rollback gates and explicit human authority. No PAT/App,
dispatch or AI orchestration is implicitly approved by adopting this manual doc.
