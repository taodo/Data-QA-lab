# Task 16 — Fabric, ADF and OneLake beginner guidance

Engineering objective: add equivalent ENG/VIE guidance to eight existing local
lessons using existing fields and accessible GuidanceText, preserving every
challenge, grader, fixture, action, import limit, account and history contract.
Learning objective: explain what evidence proves, how to practice, what each
violation_count counts and how the revealed reference SQL answers the question.

Base: origin/feature/develop deab838 (Task 15 PR #20 merged).
Branch: feature/task-16-cloud-learning-guidance. No merge or Task 17 authorized.

## Completed implementation

- Fabric: lineage dependencies, declared schema drift, Source/Bronze/Silver/Target
  reconciliation. ADF: copy metrics versus keys, selected-batch watermark/replay,
  recovery evidence. OneLake: partition manifest totals/duplicates and fixed-clock
  reference freshness. All eight have seven sections in both languages.
- Original challenges remain unchanged prefixes. Private step-by-step explanations
  remain behind the existing reveal/completion gate. Written answers are saved,
  not semantically graded. Other 28 lesson entries unchanged.
- Describe actual Reset/Publish/Next/Replay/Recover controls and before/after
  evidence. JSON preserves selected context; CSV snapshots do not invent it.
  Document import/export limits, retained audit, provenance and UNKNOWN evidence.
- GuidanceText enabled for these three courses only. Scoped wrapping fixes the
  exact CSV header overflowing 390px mobile guidance/import panels.
- Representative lineage display verified before authoring the other seven.

Illustrative miniature outcomes, verified by unchanged reference SQL:
lineage 3; schema 3; layers 2; copy 2; watermark 1; recovery 3;
partition manifest 2; reference freshness 4. Fixtures use exact Decimal money,
aware UTC and connection-local temporary tables in a dedicated test database.

## Existing boundaries / discrepancies

- Lineage SQL counts missing/UNKNOWN links, dependency failures and orphan Target
  runs, not every FAILED activity or cycles. Execution and quality stay separate.
- Recovery counts current activity observations and the latest step; a final
  snapshot does not prove every earlier execution. Activities are not an immutable
  complete execution history. Reset reloads the selected scenario, not always clean.
- Partition SUM ignores partial NULL row_count. A known subtotal can match while
  another observation is unknown: SQL may return zero, but incomplete evidence
  remains NOT_VERIFIED. Original prose about incomplete counts is broader than
  this diagnostic. Explained and regression-tested; no grading change.
- Freshness uses strict age > SLA (equality passes) and rejects future observations;
  it has no separate duplicate-group term. Schema duplicates count groups.
- All evidence is SIMULATED/IMPORTED local PostgreSQL. No live connections,
  Microsoft service emulation, Spark/Delta execution, actual shortcut resolution
  or cloud authorization. Imported evidence never supplies independent truth.

## Observed verification / resume checkpoint

- Frontend: npm run build --prefix frontend PASS after the scoped mobile fix.
- Representative browser: PASS (11.902s), keyboard/ENG/VIE/private gate,
  actual download/import/Reset/Publish and 390px mobile.
- Targeted cloud unit/course/content and import regressions: 15/16 initially
  passed; existing content assertion required NUMERIC in public schema theory.
  Added an equivalent exact-decimal versus float definition to ENG/VIE and rerun.
  Both actual reference-SQL/privacy tests and portable watermark/recovery import
  context + import atomicity/retention regressions passed.
- Independent-process catalog comparison PASS: 28 unrelated entries identical;
  16 original challenge prefixes and other fields preserved.
- Initial browser upload used a temporary UUID filename without .json; corrected
  test to retain the actual downloaded suggested filename. Importer unchanged.
- Final targeted run: cloud units, miniature SQL/privacy, cloud guidance browser,
  all-eight grading/import/resume browser and SQL/ETL/API rendering regressions.
  Final result recorded below before commit.
- Dedicated DB: data_qa_task13_browser on loopback PostgreSQL. Learner DB and
  Docker volumes untouched. Artifacts/cache/temp: D:\Data-QA-Lab\data\generated.
- Workspace was externally switched to develop during implementation; restored
  Task 16 branch with changes intact. Guard branch before any commit/push.

No full suite duplicated locally. Exact final-head CI supplies full verification.
Pending release: commit/push, PR to feature/develop and green CI on its exact head.
Record final head/results in PR and D-drive HANDOFF.txt without another doc commit.

## Primary references

Verified 2026-10-06 for basic subject purpose only; no advanced provider claims:

- [Microsoft Fabric overview](https://learn.microsoft.com/en-us/fabric/fundamentals/microsoft-fabric-overview)
- [Azure Data Factory introduction](https://learn.microsoft.com/en-us/azure/data-factory/introduction)
- [OneLake overview](https://learn.microsoft.com/en-us/fabric/onelake/onelake-overview)

## Local commands (PowerShell)

```powershell
Set-Location D:\Data-QA-Lab
$env:DATA_QA_TEST_DATABASE_URL = 'postgresql://data_qa_lab:data_qa_lab@127.0.0.1:5432/data_qa_task13_browser'
$env:PLAYWRIGHT_BROWSERS_PATH = 'D:\Data-QA-Lab\data\generated\playwright-browsers'
$env:TEMP = 'D:\Data-QA-Lab\data\generated\task16-20261006\tmp'
$env:TMP = $env:TEMP
.venv\Scripts\python.exe -m unittest tests.unit.test_cloud tests.integration.test_cloud_guidance -v
npm run build --prefix frontend
.venv\Scripts\python.exe -m unittest tests.e2e.test_browser.BrowserTests.test_cloud_beginner_guidance_import_controls_language_and_reveal tests.e2e.test_browser.BrowserTests.test_task11_eight_lessons_grading_imports_language_and_resume tests.e2e.test_browser.BrowserTests.test_sql_beginner_guidance_keyboard_language_and_reveal tests.e2e.test_browser.BrowserTests.test_etl_beginner_guidance_practice_language_keyboard_and_reveal tests.e2e.test_browser.BrowserTests.test_api_beginner_guidance_json_evidence_language_and_reveal -v
```

Final targeted run: 17 tests PASS in 205.296s (10 cloud unit, 2 SQL/content/privacy, 5 real browser tests). All-eight grading/history and SQL/ETL/API display regressions passed. Frontend build and git diff --check passed. Full CI pending on final commit.
