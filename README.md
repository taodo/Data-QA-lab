# Data QA Lab

A hands-on web app for learning data quality assurance through guided lessons, SQL practice, simulated defects and evidence-based testing.

**V1.5: 36 lessons across nine courses, with English and Vietnamese (ENG/VIE).** All 36 lessons include beginner explanations, worked examples, practice guidance and private step-by-step solutions. Runs locally with Docker and PostgreSQL; no AI API key or cloud subscription is needed.

## What you can do

- Browse courses, expand introductory explanations and follow lesson instructions.
- Create a local account and resume your own sessions from My Learning.
- Practice SQL against real PostgreSQL datasets in Sandbox or Challenge mode.
- Inspect clean and faulty data, request hints, submit checks and review grading evidence.
- Save queries, written answers, submissions and progress across restarts.
- Run a real orders pipeline and evaluate its data quality independently.

**Pipeline SUCCESS ≠ Data Quality PASS.** A pipeline can finish successfully while losing records or producing incorrect values. The quality engine checks business rules and source-to-target reconciliation separately.

## Courses

| Course | Lessons | Practice |
| --- | ---: | --- |
| SQL | 13 | Completeness, NULLs, duplicates, calculations, joins, windows, time boundaries and history |
| ETL Testing | 5 | Transformation, rejects, incremental batches, replay and recovery |
| API Testing | 4 | Real local HTTP requests, contracts, pagination, retries and ingestion |
| Microsoft Fabric | 3 | Run lineage, contracts and layered data snapshots |
| Azure Data Factory | 3 | Activity outcomes, dependencies and recovery |
| OneLake | 2 | Partitions, reference freshness and imported evidence |
| Databricks | 2 | Classification and explicit version updates |
| Azure Synapse | 2 | Fact/dimension publication and reporting grain |
| Azure | 2 | File routing and access observations |

Cloud courses use **SIMULATED or IMPORTED evidence** in isolated local PostgreSQL workspaces. They teach testing concepts without connecting to live cloud services. They do not emulate Spark, Delta, Synapse engines, actual Azure authorization or real OneLake shortcuts.

## Quick start

### Requirements

- Windows: Docker Desktop running with Linux containers and WSL 2.
- Linux: Docker Engine and the Docker Compose plugin. macOS: Docker Desktop.
- Git and internet access for the initial clone, image download and build.

The packaged app includes the frontend and backend. You do not need Python or Node installed on the host.

### Windows / PowerShell

To keep the checkout and its default PostgreSQL data on drive D:

```powershell
Set-Location D:\
git clone --branch main https://github.com/taodo/Data-QA-lab.git Data-QA-Lab
Set-Location D:\Data-QA-Lab
docker compose up -d --build --wait --wait-timeout 180
Start-Process 'http://127.0.0.1:8000'
```

If you already have a checkout, use the update instructions below instead of cloning into the same folder.

### macOS / Terminal

Install Git and Docker Desktop for your Mac (choose the installer for your processor), then open Docker Desktop and wait until it is running. The following uses a new folder under your home directory:

```bash
mkdir -p ~/Projects
cd ~/Projects
git clone --branch main https://github.com/taodo/Data-QA-lab.git Data-QA-Lab
cd Data-QA-Lab
docker compose up -d --build --wait --wait-timeout 180
open 'http://127.0.0.1:8000'
```

These are setup instructions; macOS hardware has not been independently tested by this project. CI verifies the packaged app on Linux. If Git is unavailable, macOS may prompt you to install Command Line Tools.

### Linux / Terminal

With Docker Engine and Compose installed and running:

```bash
git clone --branch main https://github.com/taodo/Data-QA-lab.git Data-QA-Lab
cd Data-QA-Lab
docker compose up -d --build --wait --wait-timeout 180
```

Open **http://127.0.0.1:8000**. Sign up, select ENG or VIE, choose a course and start a lesson.

A fresh packaged setup creates **1,000 deterministic orders**. An existing usable pipeline run is retained. Lesson sessions use isolated workspaces. The first build may take several minutes; the built app uses local assets.

## How to learn

1. Read the course introduction and expand the lesson sections: what we check, why it matters, illustrative example and common mistake.
2. Explore the data and run a query in Sandbox, or investigate a hidden defect in Challenge.
3. Read the challenge and write a check that detects violations.
4. Submit your check and written answer, then inspect the evidence and feedback. SQL lessons use SQL; API lessons use a bounded JSON request/check plan.
5. Improve the check and resume the next lesson from My Learning. Step-by-step solution explanations are available through the existing reveal/completion gate; revealing alone does not award completion.

SQL submissions are tested against independent clean and faulty fixtures. Written answers are saved for review; their prose is not semantically graded. Learner SQL runs through a restricted, bounded read-only interface. See [SQL security](docs/SQL_SECURITY.md) for its limits.

The Pipeline page follows orders through Source, Bronze, Silver, Gold and Target. Run the pipeline first, then run the QA suite to investigate completeness, values and daily aggregates. Execution status and data quality status describe different results.

## Stop, restart and update

Stop services while keeping database files:

```bash
docker compose stop
```

Restart:

```bash
docker compose up -d --wait --wait-timeout 180
```

To update an existing checkout with no uncommitted changes, first enter its folder:

- Windows: `Set-Location D:\Data-QA-Lab`
- macOS: `cd ~/Projects/Data-QA-Lab`

Then run these commands in either shell:

```bash
git fetch origin
git switch main
git pull --ff-only origin main
docker compose up -d --build --wait --wait-timeout 180
```

After rebuilding, reload the browser (Windows: Ctrl+F5; macOS: Command+Shift+R). No reseeding is needed for the guidance update.

The default database bind mount is `./data/postgres`. On macOS it is inside your checkout, normally `~/Projects/Data-QA-Lab/data/postgres`. With the Windows checkout above, accounts, sessions and evidence live under `D:\Data-QA-Lab\data\postgres`. Keep this directory when upgrading. Docker Desktop images, cache and virtual disk use Docker Desktop's separately configured storage location; installing this repository on D does not move those files. See the [D-drive guide](docs/WINDOWS_D_DRIVE.md).

The default app and PostgreSQL ports are bound to the local loopback interface. Compose database credentials are local development defaults.

## Share an online demo

For a temporary showcase, follow [the free online demo guide](docs/DEMO_ONLINE.md). It uses a separate demo stack/database, operator-created accounts and a Cloudflare Tunnel. Configure the exact tunnel hostname as described there. Public signup is disabled in demo mode.

The host computer, Docker and tunnel must remain running. A temporary tunnel URL can change when restarted. Do not publish generated configuration, account passwords or database files.

## Development and verification

The backend requires Python 3.11+. For Windows:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[test,e2e]"
.\.venv\Scripts\python.exe -m unittest discover -s tests/unit -v
```

**Run integration tests only against a dedicated test database.** They reseed data and alter fixtures. Do not point them at the database containing your learning history.

With the default Compose PostgreSQL credentials, create a separate database once:

```powershell
docker compose up -d --wait postgres
docker compose exec postgres createdb -U data_qa_lab data_qa_lab_test
$env:DATA_QA_TEST_DATABASE_URL = 'postgresql://data_qa_lab:data_qa_lab@127.0.0.1:5432/data_qa_lab_test'
.\.venv\Scripts\python.exe -m unittest discover -s tests/integration -v
Remove-Item Env:DATA_QA_TEST_DATABASE_URL
```

If `data_qa_lab_test` already exists, skip its creation. Adjust the connection string if you changed Compose credentials or ports. On Linux/macOS, use the equivalent virtual-environment Python and export the same test variable.

CI covers unit, PostgreSQL integration, browser and packaged startup/restart checks, including the separate demo stack. During development, run tests relevant to the change first. **Avoid repeated full-suite runs unless a failure requires them.** A green CI run on the final commit can provide full-suite verification without repeating it locally.

The CLI also supports pipeline, quality, fault and lab commands:

```powershell
.\.venv\Scripts\python.exe -m backend.app.main --help
```

The explicit CLI `seed` command defaults to 10,000 orders; that is a different baseline from the packaged app's initial 1,000 orders.

## Documentation

| Guide | Purpose |
| --- | --- |
| [V1 guide](docs/V1_GUIDE.md) | Local startup, troubleshooting and learning workflow |
| [Learning model](docs/LEARNING_MODEL.md) | Lessons, challenges and grading concepts |
| [Architecture](docs/ARCHITECTURE.md) | Components and pipeline design |
| [Data model](docs/DATA_MODEL.md) | Schemas and stored evidence |
| [SQL security](docs/SQL_SECURITY.md) | Query execution boundaries |
| [Online demo](docs/DEMO_ONLINE.md) | Separate public showcase setup |
| [Roadmap](docs/ROADMAP.md) | Planned work; availability is described above |

`main` contains the approved application. New task branches start from `feature/develop` and return there through review before a release is promoted to `main`. Task documents under `docs/` preserve implementation history and may describe earlier versions.
