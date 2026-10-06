# Windows setup on D:\

The repository should remain at `D:\Data-QA-Lab`. Open that folder as its own Codex workspace.

Create the virtual environment and pip cache on D:

```powershell
New-Item -ItemType Directory -Force D:\DevCache\pip | Out-Null
$env:PIP_CACHE_DIR = 'D:\DevCache\pip'
Set-Location D:\Data-QA-Lab
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e .
```

Compose maps PostgreSQL data to `./data/postgres`, which resolves to `D:\Data-QA-Lab\data\postgres`. To choose another D-drive path, create `.env`:

```dotenv
DATA_QA_POSTGRES_DATA=D:/DockerData/data-qa-lab-postgres
```

Then run `docker compose up -d postgres`.

Use the IPv4 loopback address in the local connection settings:

```dotenv
DATABASE_URL=postgresql://data_qa_lab:data_qa_lab@127.0.0.1:5432/data_qa_lab
```

Compose intentionally publishes PostgreSQL only on `127.0.0.1`. Using `localhost` can make some Windows configurations try an unavailable IPv6 loopback connection first and wait for its network timeout.

The project and database bind mount are on D. Docker Desktop may still keep its Linux VM/WSL disk image on C. Move that disk image using Docker Desktop's storage setting if C remains constrained; this repository does not automate that machine-level change.

Keep QA Sentinel in its existing workspace. Follow `docs/BRANCHING.md` for task branches.
