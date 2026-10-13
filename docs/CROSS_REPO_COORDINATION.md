# C1 — GitHub coordination protocol and operator runbook

## Purpose and verified baseline

Engineering objective: record bounded, explicit human review handoffs without
granting an agent domain-repository write access or deployment authority.
Learning objective: distinguish routing/status evidence from an actual independent
review and from permission to implement, merge or release.

Authority: [Issue #39](https://github.com/taodo/Data-QA-lab/issues/39).
Base: `feature/develop` at `fecd1671101c846fb6cd99d6c746925b9988b848`.
Task branch: `feature/c1-cross-repo-coordination`.
The complete Issue and current comments were read before implementation, including
Banking #37's F1–F3 amendment review and Automation #38's bootstrap review.
Existing comments are never retroactively interpreted as commands. U2 PR #35,
domain tasks, production and retained learner/demo data are outside this change.

| Platform Issue | Target label | Review domain (read-only reference) |
| --- | --- | --- |
| [#37](https://github.com/taodo/Data-QA-lab/issues/37) | `banking` | `taodo/MiniBanking` |
| [#38](https://github.com/taodo/Data-QA-lab/issues/38) | `automation` | `taodo/Automation-QA-Lab` |

Only these open, unlocked platform Issues accept opt-in commands. The handler
never calls either domain repository, creates domain tasks, dispatches events,
calls AI APIs, wakes/messages a separate ChatGPT session, or merges/deploys.
A human reads the authoritative Issue and evidence, performs the review using
their chosen tools, then explicitly records the outcome here.

## Activation and workflow permissions

The default branch is currently `main`. GitHub's `issue_comment` trigger requires
the workflow to exist on the default branch; a develop PR alone does not activate
comment handling. See the [official trigger documentation](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#issue_comment).
C1 prepared the workflow for review; C1-A prepares the isolated main-targeted
release described below. A separately approved merge is required for activation.
No default-branch change or live command test is performed during preparation.

The workflow is JSON-formatted YAML (the [YAML 1.2 JSON-compatible subset](https://yaml.org/spec/1.2.2/)).
This allows structural security assertions with Python's standard library.

| Job | Trigger and permissions | Work |
| --- | --- | --- |
| `validate` | Path-filtered push to main/develop/C1-A branch; `contents:read` | The focused mocked unit tests only; no token passed to the test command |
| `coordinate` | Created opt-in human comment on #37/#38; `contents:read`, `actions:read`, `issues:write` | Read fresh metadata, authorize, validate, then one POST or PATCH |

Checkout is pinned to an official `actions/checkout` v4 commit, with persisted
credentials disabled. The handler checks out the event's trusted default-branch
SHA, never a PR or comment-selected ref. No comment interpolation enters shell
commands. See [GitHub Actions security guidance](https://docs.github.com/en/actions/reference/security/secure-use).
`actions:read` is used only for durable delivery/run-history guards. There are no
PATs, external secrets, labels, AI credentials or `contents:write` permissions.

The existing [test workflow](../.github/workflows/test.yml) is unchanged: its
normal push/PR CI can still run, but comment events do not invoke its heavy suites.
GitHub's `GITHUB_TOKEN` event suppression also prevents ordinary bot comment
recursion; the handler independently rejects bots. See [trigger restrictions](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/trigger-a-workflow).

## Actors and exact command grammar

Every command must be a NEW, unedited human comment. Its first line must match
one of the following exactly, without indentation, quotes, fences, schemes,
extra fields or reordered arguments. Commands are case-sensitive. Optional
human notes may follow a blank line; they are never executed or copied into the
bot ledger. Include links to the actual review/evidence in these notes.

```text
/coord request target=banking type=review
/coord request target=automation type=review
/coord review id=c1-37-123456 revision=1 outcome=review-posted
/coord review id=c1-37-123456 revision=1 outcome=needs-changes
/coord review id=c1-37-123456 revision=1 outcome=blocked
/coord resume id=c1-37-123456 revision=2
/coord handoff id=c1-37-123456 revision=2
/coord close id=c1-37-123456 revision=3 decision=acknowledged
/coord close id=c1-37-123456 revision=2 decision=cancelled
```

The numbers above are illustrative. Copy the current correlation and revision
from the bot acknowledgment. For Automation use its actual `c1-38-<commentID>`.
Do not send multiple commands in one comment. Unknown commands, mismatched
targets, commands on other Issues or PRs, edits, bot authors and stale revisions
produce no write. Ordinary prose and quoted examples are not commands.

The handler calls GitHub's [collaborator permission endpoint](https://docs.github.com/en/rest/collaborators/collaborators#get-repository-permissions-for-a-user)
and matches the returned numeric user ID and login against the fresh comment.
Effective platform permission `write` or `admin` is required. GitHub reports
maintain as write and triage as read; read/triage users cannot transition state.
Closure additionally requires effective `admin` permission. Username allowlists
and `author_association` confer no authority.

This verifies platform permission, not domain membership or authorship of the
review prose. A read-only external reviewer can post evidence; an authorized
platform maintainer must explicitly record it. Admin acknowledgment closes the
coordination cycle only, not the Issue, domain task or implementation gate.

## Lifecycle and acknowledgment

| Current state | Explicit human command | Result / next responsible actor |
| --- | --- | --- |
| No active request | `request` | REQUESTED → AWAITING_REVIEW / domain human reviewer |
| AWAITING_REVIEW | `review ... outcome=review-posted` | REVIEW_POSTED / platform human maintainer |
| AWAITING_REVIEW | `review ... outcome=needs-changes` | NEEDS_CHANGES / responsible author or maintainer |
| AWAITING_REVIEW | `review ... outcome=blocked` | BLOCKED / human resolving blocker |
| NEEDS_CHANGES or BLOCKED | `resume` within review budget | AWAITING_REVIEW / human reviewer |
| REVIEW_POSTED | `handoff` | AWAITING_HUMAN_APPROVAL / owner/admin |
| AWAITING_HUMAN_APPROVAL | Admin `close ... decision=acknowledged` | CLOSED / no next automated action |
| Any active state | Admin `close ... decision=cancelled` | CLOSED / no next automated action |

The first accepted request creates exactly one structured bot acknowledgment on
the same Issue. Later accepted transitions PATCH that comment, retaining its
event history. REQUESTED is recorded as the initial transition, atomically with
AWAITING_REVIEW; there is no extra bot request/follow-up comment. CLOSED is terminal.
A new cycle requires another explicit request and remaining lifetime capacity.

The acknowledgment contains source Issue, target repository, protocol
`qa-coordination/v1`, correlation `c1-<issue>-<requestCommentID>`, revision, state,
next responsible human role and source comment links. Its marked JSON ledger
records command/comment IDs, actor IDs/logins, verified permission, original UTC
timestamp, first command line and SHA-256 of the original body. It contains no
review-body copy or secrets. Only the verified `github-actions[bot]` numeric ID
41898282 and a canonical, reconstructable ledger are trusted. Human-forged
markers are ignored; malformed bot ledgers, duplicates and conflicting active
cycles fail closed. Privileged administrators and other write-capable workflows
remain within the repository trust boundary; this is not a cryptographic signature.

## Idempotency, concurrency and finite bounds

- Per-Issue job concurrency uses `cancel-in-progress:false`, `queue:max`.
  GitHub currently permits 100 pending jobs; queue order is by waiting time and
  does not guarantee dispatch order. See [concurrency semantics](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax#concurrency).
  Expected revisions and command chronology prevent stale transitions.
- One active request per Issue, eight accepted events/revisions per cycle,
  three review rounds, ten cycles per Issue. Budget exhaustion causes no write.
- Comments: at most five pages of 100; run history: ten pages of 100 within
  the preceding 24 hours. Full-page boundary exhaustion fails closed rather
  than silently discarding history. Commands older than 24 hours are rejected.
- Maximum command body 8,000 UTF-8 bytes, event file 1 MiB, API response 2 MiB;
  HTTP timeout 10 seconds per request and job timeout three minutes.
- Each mutation has one attempt, no HTTP retries or redirected requests.
  Rate limits/network errors stop processing with a sanitized static reason.
- Accepted comment IDs in the ledger suppress repeat delivery. An unacknowledged
  rerun attempt or previous run with the same comment identity cannot write.
  The current run must appear in GitHub's own workflow metadata before writing.
- Recent failed/cancelled/timed-out/action-required runs for the same Issue,
  without a ledger receipt, conservatively hold subsequent mutations. Runs on
  the other Issue do not block this Issue. Fresh source/Issue/ledger rechecks
  catch edits, closure and conflicting changes before the single write.

GitHub comment POST has no transactional idempotency key. This protocol chooses
at-most-once supported workflow delivery over guaranteed delivery after an
ambiguous response: a lost response can mean a missing acknowledgment or an
operator hold. It does not claim distributed exactly-once delivery. Manual
parallel CLI invocation, privileged ledger/run deletion and arbitrary other
writers are outside the supported execution boundary. Source edits/deletions
freeze an active cycle except an explicit admin cancellation.

## Human operation and recovery

1. After separately approved default-branch activation, read #37 or #38 and its
   latest review; post the corresponding exact request with relevant evidence.
2. Read the acknowledgment. A human independently reviews; an authorized
   maintainer posts its outcome with the current revision. If changes/blockers
   are resolved, explicitly resume, then obtain another review within the budget.
3. For REVIEW_POSTED, explicitly hand off to the owner/admin. The admin records
   acknowledgment or cancellation. Neither action approves implementation or
   closes the authoritative Issue. Domain workflows retain their own review gates.
4. For NO_WRITE, inspect the static reason and current ledger before sending any
   new command. Never edit an old command to make it execute.
5. For FAIL_CLOSED / WRITE_UNCERTAIN or an unresolved-run hold, STOP automated
   transitions. Inspect the run and Issue comments using read-only tools and
   reconcile whether a receipt exists. Do not rerun, delete ledgers/run history,
   evade a hold with a new command, or assume that waiting 24 hours proves safety.
   No repair/reset command is implemented; an owner-reviewed recovery decision
   is required. Conservative holds can include failures before any mutation.
6. On a malformed trusted ledger or exhausted lifetime/scan capacity, stop and
   request a separately reviewed protocol/operational change. Do not truncate
   referenced evidence or silently start another coordination Issue.

## Verification and remaining limitations

Changed implementation: [handler](../scripts/github_coordination.py),
[workflow](../.github/workflows/coordination.yml),
[tests](../tests/unit/test_github_coordination.py), and this runbook.

```powershell
Set-Location D:\Data-QA-Lab
$env:PYTHONUTF8 = '1'
.\.venv\Scripts\python.exe -m unittest tests.unit.test_github_coordination -v
git diff --check
```

Observed local result: 30 tests passed, including both targets, authorization and
ID spoofing, command grammar, full lifecycle, finite budgets, redelivery/ambiguous
writes, ledger authenticity, run visibility, concurrency rechecks, malformed/API
failures, and workflow security contracts. Whitespace and relative documentation
references were checked. Existing CI content is verified unchanged from the base.
Push validation runs the same focused suite; exact commit/run evidence belongs in
the PR and Issue #39 FINAL REPORT.

Not run: live opt-in comment lifecycle, live simultaneous event delivery, production
activation, domain workflows, browser/frontend build, database/full local suites.
These are not required to execute mocked C1 tests; live GitHub behavior must still
be verified after approved activation. No real #37/#38 commands or bot ledger
mutations were sent during implementation. Existing normal CI may run independently
on the task push/PR. No domain scope, existing CI, application or deployment files
were changed. Stop at independent review; do not merge or deploy.

## C1-A — isolated release preparation (Issue #41)

Authority: [Issue #41](https://github.com/taodo/Data-QA-lab/issues/41), authorizing
preparation and review only. Engineering objective: bring the accepted routing
protocol to the default-branch release boundary without releasing platform work.
Learning objective: distinguish a validated release PR from activation, and
coordinate a reversible smoke check without implying a domain review/approval.

| Provenance | Exact commit |
| --- | --- |
| Remote main base when branched | `ad3f88bd430de9b4ff8d33307435dc39eb2949f7` |
| Accepted C1 implementation | `3067892b945c8ea6f6f05270653a2fb97767d783` |
| C1 PR #40 accepted merge / fetched develop | `ac0bb35135c17a69213799e77aaac44a5bf8e541` |
| Isolated release branch / PR target | `feature/c1a-coordination-activation` / `main` |

All four C1 files were unchanged between the reviewed implementation, accepted
merge and fetched develop. They were ported individually onto remote main;
no develop merge/cherry-pick or unrelated platform changes were included. Main
has only the existing test workflow, which validates disposable CI state and
does not deploy the website. External deployment hooks were not independently
verified; the operator must confirm those remain inert before an approved merge.
Task 20.1, 21.1, U1/U5-P documents and concurrent U2 are not promoted by this PR.

Intentional deviations from C1, all within these four files:

- Workflow: replace the obsolete `feature/c1-cross-repo-coordination` push filter
  with the exact C1-A branch so the release head gets its own focused CI. Retain
  existing `main`/`feature/develop` path filters for validation of this protocol
  only. Nothing changes in comment routing, permissions, checkout or concurrency.
- Tests: add one regression asserting the exact three branches/four paths,
  fixed focused command, and comment-only mutation job. The original 30 remain.
- Runbook: clarify release-stage wording and add this provenance, approval,
  smoke and rollback procedure. Protocol, grammar and limits remain v1.
- Handler: byte-identical to accepted C1. It has only stdlib imports and needs no
  tutorial/app/develop files, installed packages, migration or new dependencies.

The release branch runs the earlier PowerShell test command: 31 tests pass, with
workflow parse/security assertions. Reference/fence checks and `git diff --check`
also pass. Source/release SHA-256 values, exact release HEAD and final-head hosted
CI evidence are recorded in the Issue #41 FINAL REPORT and main-targeted PR.
The original C1 verification above is historical, not live activation evidence.

### Approval gate and read-only checks

1. Independently review the isolated main PR, these four paths, source hashes and
   green focused CI on its exact head. Recheck main and release HEAD immediately
   before any later merge; a changed head requires review again.
2. Obtain separate explicit human approval to merge/activate this reviewed head.
   This task does not grant it. Do not change default branch, protections, tokens,
   Actions settings or deploy the site as part of preparation.
3. After approved merge only, verify main contains the workflow/handler/runbook,
   the default remains main, trusted event SHA/ref are main, and effective job
   permissions remain read contents/actions + write Issues. Record the actual
   main merge SHA and focused validation run; do not use the PR SHA as merge proof.
4. Confirm repository/operator deployment automation will not restart/rebuild
   the website. No Docker, account provision, DB reset or Cloudflare action is
   required for coordination. Inspect run metadata using the Actions UI; never
   print the token or run the mutation CLI manually outside Actions.

### Post-approval smoke checklist — NOT EXECUTED in C1-A

Only the project lead may perform these steps after later activation approval,
verified merge and explicit smoke permission. No #37/#38 commands were posted
in this task. Keep a source-comment/run/ledger/revision log with no credentials.

For each Issue (#37 banking, #38 automation), sequentially:

- [ ] Verify Issue is open/unlocked, existing domain scope unchanged, no active
  ledger/uncertain delivery and budget available. Read current comments first.
- [ ] An authorized write/admin human posts ONE matching request. Label notes
  `C1-A protocol smoke only; not domain review or implementation approval`.
  Observe a created-comment run using trusted main SHA and exactly one authentic
  same-Issue AWAITING_REVIEW acknowledgment with correct target/correlation.
- [ ] Inspect bot-event/no-op behavior: acknowledgment causes no responding job
  or new acknowledgment. Ordinary human prose/quoted command must not mutate
  the ledger. Observe events/logs without modifying existing source comments.
- [ ] If the accepted run has a ledger receipt, an explicitly authorized rerun
  of that SAME run may check DUPLICATE_NO_WRITE; revision/comment count must not
  change. Never rerun an unacknowledged/uncertain write. Reruns are not a test of
  simultaneous delivery; that remains pending unless separately exercised.
- [ ] A human independently reviews the protocol smoke evidence (not the domain
  implementation), posts explicit `review ... outcome=review-posted` using the
  live revision, then an authorized human posts `handoff` using the new revision.
  Observe the same ledger updated through REVIEW_POSTED and
  AWAITING_HUMAN_APPROVAL, each exactly once with evidence links.
- [ ] Admin posts `close ... decision=acknowledged` at the new revision if the
  smoke review is complete, or `decision=cancelled` to stop a known-safe active
  cycle. Observe CLOSED while the authoritative Issue remains open. No new
  domain task, technical approval, merge or next cycle is implied.
- [ ] Record true outcomes and remaining unknowns: real token permissions,
  POST/PATCH identity, run-history visibility and no unexpected mutations.
  On missing receipt, API failure or hold, STOP and follow recovery above; do
  not use cancellation as a way to bypass an uncertain-write hold.

Unauthorized/other-Issue/PR rejection, malformed input, simulated concurrency
and ambiguous failures are already covered with mocks. Do not grant accounts
new permissions, force network failures or edit/delete evidence to test them.
Real redelivery/concurrent delivery and failure paths need separate bounded
verification; successful ordinary smoke does not prove them.

### Disable / rollback without website changes

This is an operator plan, not a command executed by C1-A:

1. If unexpected behavior appears, stop human commands and disable only the
   `C1 coordination` workflow in the Actions UI after explicit operator approval.
   See [GitHub's disable/enable procedure](https://docs.github.com/en/actions/how-tos/manage-workflow-runs/disable-and-enable-workflows).
   Disabling prevents new triggers; it does not prove in-flight writes stopped.
2. Inspect queued/running coordination jobs. Owner-authorized cancellation may
   leave an uncertain write; wait for run completion, reconcile comments and
   preserve all ledgers/source/run history. Treat missing receipts as unresolved.
   Do not clear holds or delete receipts. Existing `tests` CI remains enabled.
3. Prepare a separate reviewed rollback PR from fresh main removing only
   `.github/workflows/coordination.yml` (or restoring its pre-activation absence).
   Retain handler/tests/runbook for audit. Do not revert all of develop or later
   unrelated main commits. Removal of this workflow requires no app rebuild,
   deployment, migration, database reset, volume deletion or tunnel change.
4. Verify the coordination workflow remains disabled/absent and no new mutating
   jobs run; verify website configuration/source/data were not altered. Rollback
   does not undo existing status comments or settle uncertain deliveries.
5. Re-enablement needs independent review, reconciled evidence, explicit user
   approval, fresh hashes/head/CI and a bounded smoke plan. Never resume a stale
   command or assume that expiration of the 24-hour scan window proves safety.

Unverified until activation: real issue_comment event/ref/SHA, Actions token
permission behavior, bot POST/PATCH, run-history consistency and simultaneous
delivery. No live activation, deployment or domain mutation was performed.
