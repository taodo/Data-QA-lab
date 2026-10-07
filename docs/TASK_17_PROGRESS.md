# Task 17 — Databricks, Synapse and Azure beginner guidance

Engineering objective: explain six existing lessons in ENG/VIE using the current
content fields and GuidanceText, preserving challenges, graders, fixtures,
simulation/import behavior, limits, APIs, permissions, accounts and history.
Learning objective: help beginners interpret routing, explicit versions, fact
identity, report grain, file expectations and access observations using evidence.

Base: origin/feature/develop e0be176, Task 16 PR #21 merged.
Branch: feature/task-17-foundations-learning-guidance. No merge/next task approved.

## Implementation checkpoint

- Six lessons × two languages, each with checking, why, illustrative example,
  actual practice, challenge explanation, common mistake and private solution.
- New foundations_guidance module applies only to foundation catalog entries;
  original challenge text remains an unchanged prefix. Private explanations stay
  behind existing reveal/completion gates. Written answers are saved, not graded
  semantically. GuidanceText enabled for these three courses only.
- Foundation JSON envelope is distinct from Task 16 JSON/CSV: version/kind,
  exact lab_id/contract_id/provider, required context/runs/steps/datasets and typed
  observed rows. No importable expected tables. Unknown context remains unknown;
  imported checkpoints are claims. Portable bounds, no truncation, local mutation
  revisions and retained import audit explicitly described.
- SIMULATED/IMPORTED PostgreSQL provenance throughout. No cloud adapters, Spark/
  Delta execution, transaction log/time travel, Synapse engine, real file reads
  or Azure authorization. No dependencies or storage changes.
- Representative classification guidance/browser checked before the other five.

Actual reference-SQL miniature outcomes:

| Lesson | Expected violation_count | Explanation |
|---|---:|---|
| Classification | 3 | Wrong classification + missing key + matching duplicate group; correct reject is valid |
| Versions | 3 | Stale version + lost untouched key + matching duplicate group |
| Fact publication | 3 | Wrong customer mapping + missing sale + unexpected sale; equal counts/totals |
| Reporting grain | 1 | Fanout doubles North count and exact total; one failing report row |
| File manifest | 4 | Wrong path/route once + missing + unexpected + duplicate group |
| Access observations | 4 | Denied + unknown identity + missing + unexpected; evidence investigation, not data defects |

## Existing implementation limits / discrepancies

- Version actions apply greater-version guards to current db_after, not rebuild
  from db_before. Replay need not repair existing duplicates or recover a lost
  newer value. Tied incoming revisions have no deterministic arbitration here;
  final-state reconciliation does not prove each transition or Delta transactions.
- Fact/report publication reruns observed JOINs. Missing/duplicated dimensions
  can omit/multiply facts; rerunning does not repair dimension evidence. Truth
  must stay independent. Equal-price sales defeat SUM(DISTINCT amount).
- Azure Capture records run/step while retaining existing observations; it does
  not refresh row capture times, repair paths, fetch files or grant access.
- Manifest diagnostic does not compare observed_at/run_id; evidence completeness
  separately checks capture/context/run gaps. Paths are exact labels only.
- Access DENIED is ACCESS_ERROR, missing/mismatched/unknown observations are
  INCOMPLETE (denial takes precedence). Quality remains NOT_VERIFIED in either
  case. Zero with complete evidence validates access_evidence only. Equality at
  as_of passes; there is no freshness SLA here. No data-quality verdict inferred.
- Duplicate terms count groups, not excess copies. Failing duplicate joined
  rows can contribute to reconciliation too. No grader changed.

## Verification / resume

- npm run build --prefix frontend: PASS, Vite 2.75s. First sandbox attempt failed
  EPERM resolving index.html; rebuilt with required runtime permissions. Initial
  browser ran stale assets and timed out; rerun after build PASS (11.537s).
- Six illustrative examples PASS using actual reference SQL in connection-local
  TEMP tables with exact Decimal money and UTC/date values. Extra boundaries:
  third matching duplicate still one group; run_id excluded from version
  diagnostic; actual JOIN fanout/equal-price DISTINCT trap; manifest NULL capture
  separate from diagnostic; multi-predicate access row counted once; duplicate
  denied observations contribute failing rows plus group.
- Existing Task 12 units/course contracts, all-six fault round-trip/reset/session
  portability/immutable truth, access status/restricted SQL/overflow regressions
  passed. Initial privacy check requested explicit NOT_VERIFIED in public theory;
  added equivalent status wording to both languages. Affected privacy rerun PASS.
- Independent-process catalog comparison PASS: other 30 entries unchanged;
  12 original challenge prefixes and all other fields preserved.
- Final targeted browser/content results recorded below before commit. Browser
  covers all six × ENG/VIE practice and completed private explanations, typed
  download/import, controls, reveal/keyboard/mobile/history and prior-course UI.
- Dedicated DB: data_qa_task13_browser, loopback PostgreSQL. Learner database and
  Docker volumes untouched. D-drive artifacts/cache/temp only.
- No local full-suite duplication. Final exact-head CI supplies full validation.
  Pending: commit/push, PR to feature/develop, wait both full tests and packaged-v1
  green. Record final head/CI in PR and ignored D-drive HANDOFF.txt, no later commit.
  Resume by checking branch/status/head and PR runs; never merge or start another task.

## Primary-source references

Verified 2026-10-07, basic purpose only; advanced provider behavior not claimed:

- [Databricks introduction](https://docs.databricks.com/aws/en/introduction)
- [Azure Synapse overview](https://learn.microsoft.com/en-us/azure/synapse-analytics/overview-what-is)
- [Azure Data Lake Storage overview](https://learn.microsoft.com/en-us/azure/storage/blobs/data-lake-storage-introduction)

## Local PowerShell verification

```powershell
Set-Location D:\Data-QA-Lab
$env:DATA_QA_TEST_DATABASE_URL = 'postgresql://data_qa_lab:data_qa_lab@127.0.0.1:5432/data_qa_task13_browser'
$env:PLAYWRIGHT_BROWSERS_PATH = 'D:\Data-QA-Lab\data\generated\playwright-browsers'
$env:TEMP = 'D:\Data-QA-Lab\data\generated\task17-20261007\tmp'
$env:TMP = $env:TEMP
.venv\Scripts\python.exe -m unittest tests.integration.test_foundations_guidance tests.unit.test_task12 -v
npm run build --prefix frontend
.venv\Scripts\python.exe -m unittest tests.e2e.test_browser.BrowserTests.test_foundations_beginner_guidance_envelope_controls_language_and_reveal tests.e2e.test_browser.BrowserTests.test_task12_six_lessons_challenge_import_language_mobile_history -v
```

Final targeted run: 12 tests PASS in 140.749s (2 miniature SQL/privacy, 4 foundation units, 6 browser tests). All six completed private explanations checked in ENG/VIE; prior SQL/ETL/API/Fabric/ADF/OneLake browser rendering preserved. Frontend build and git diff --check PASS. Other dedicated import/access regressions PASS as recorded above. Final-head full CI pending.
