# Windows setup on D:

This archive was built remotely; no files have been moved on your computer.

1. Download the ZIP directly to D if the browser permits it.
2. Extract its contents so `D:\Data-QA-Lab\pyproject.toml` exists.
3. Open this folder as a separate Codex project/workspace.
4. Run the README checks. Python 3.11+ must already be available or installed.

Create any virtual environment inside this project. No dependencies are required for Task 0.

For future pip installs, use a session-local cache on D:

```powershell
New-Item -ItemType Directory -Force D:\DevCache\pip | Out-Null
$env:PIP_CACHE_DIR = 'D:\DevCache\pip'
Set-Location D:\Data-QA-Lab
py -3 -m venv .venv
```

Project path and virtual environment placement do not move Python itself, browser downloads, Windows TEMP, Codex app data or Docker's disk image. Docker/WSL storage relocation should be configured separately before starting Task 1; no relocation script is included.

If a previous Data QA Lab folder already exists, extract this package into a new empty folder and compare changes. Avoid overwriting an existing project blindly. Keep QA Sentinel in its existing workspace.
