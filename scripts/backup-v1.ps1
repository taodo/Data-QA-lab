$ErrorActionPreference = 'Stop'
Set-Location (Split-Path $PSScriptRoot -Parent)
New-Item -ItemType Directory -Force -Path '.\backups' | Out-Null
$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
# Container shell expands its own configured credentials; no binary stdout redirection.
docker compose exec -T postgres sh -c 'pg_dump -U $POSTGRES_USER -d $POSTGRES_DB -Fc -f /tmp/data-qa-lab.backup'
if ($LASTEXITCODE -ne 0) { throw 'Database backup failed.' }
docker compose cp postgres:/tmp/data-qa-lab.backup ".\backups\data-qa-lab-$stamp.backup"
if ($LASTEXITCODE -ne 0) { throw 'Copying backup failed.' }
Write-Output "Backup saved: backups\data-qa-lab-$stamp.backup"
