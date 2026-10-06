$ErrorActionPreference = 'Stop'
Set-Location (Split-Path $PSScriptRoot -Parent)
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    throw 'Docker is not available. Start Docker Desktop and open a new PowerShell window.'
}
docker version
if ($LASTEXITCODE -ne 0) { throw 'Docker Engine is not ready. Open Docker Desktop, then retry.' }
docker compose up -d --build --wait --wait-timeout 180
if ($LASTEXITCODE -ne 0) { throw 'Startup failed. Run: docker compose logs --tail 100 app postgres' }
Start-Process 'http://127.0.0.1:8000'
