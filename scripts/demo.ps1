param(
    [Parameter(Mandatory=$true)]
    [ValidateSet('Prepare','Start','SetHostname','LocalOnly','Account','Status','Stop')]
    [string]$Action,
    [string]$Hostname,
    [string]$Username = 'demo_learner'
)
$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
if ($repo -ne 'D:\Data-QA-Lab') { throw 'This runbook is restricted to D:\Data-QA-Lab' }
Set-Location -LiteralPath $repo
$demoDir = Join-Path $repo 'data\generated\demo'
$envFile = Join-Path $demoDir '.env.demo'
$compose = @('compose','-p','data-qa-demo','--env-file',$envFile,'-f','docker-compose.demo.yml')
if ($Action -eq 'Prepare') {
    foreach ($dir in @($demoDir, "$demoDir\tools", "$demoDir\logs", "$demoDir\tmp")) {
        New-Item -ItemType Directory -Force -Path $dir | Out-Null
    }
    if (!(Test-Path -LiteralPath $envFile)) {
        $bytes = New-Object byte[] 32
        $rng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
        $rng.GetBytes($bytes); $rng.Dispose()
        $secret = -join ($bytes | ForEach-Object { $_.ToString('x2') })
        [IO.File]::WriteAllText($envFile, "DEMO_DB_PASSWORD=$secret`nDEMO_PUBLIC_HOST=`n")
        # Restrict the ignored credentials file to this Windows user.
        & icacls $envFile /inheritance:r /grant:r "$([Security.Principal.WindowsIdentity]::GetCurrent().Name):(F)" | Out-Null
        if ($LASTEXITCODE -ne 0) { throw 'Could not restrict demo credentials file' }
    }
    [IO.File]::WriteAllText("$demoDir\cloudflared.yml", "{}")
    Write-Output "Prepared isolated demo files at $demoDir. No tunnel started."
    return
}
if (!(Test-Path -LiteralPath $envFile)) { throw 'Run Prepare first' }
$env:TEMP = "$demoDir\tmp"
$env:TMP = $env:TEMP
switch ($Action) {
    'Start' { & docker @compose up -d --build --wait --wait-timeout 180 }
    'SetHostname' {
        if ($Hostname -cnotmatch '^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.trycloudflare\.com$') {
            throw 'Supply only the exact generated lowercase trycloudflare.com hostname; no URL, port or wildcard'
        }
        $text = [IO.File]::ReadAllText($envFile) -replace '(?m)^DEMO_PUBLIC_HOST=.*$', "DEMO_PUBLIC_HOST=$Hostname"
        [IO.File]::WriteAllText($envFile, $text)
        & docker @compose up -d --no-deps --force-recreate --wait --wait-timeout 180 app proxy
    }
    'LocalOnly' {
        $text = [IO.File]::ReadAllText($envFile) -replace '(?m)^DEMO_PUBLIC_HOST=.*$', 'DEMO_PUBLIC_HOST='
        [IO.File]::WriteAllText($envFile, $text)
        & docker @compose up -d --no-deps --force-recreate --wait --wait-timeout 180 app proxy
    }
    'Account' { & docker @compose exec app python -m backend.app.main demo-account --username $Username }
    'Status' { & docker @compose ps }
    'Stop' { & docker @compose stop }
}
if ($LASTEXITCODE -ne 0) { throw "Docker command failed: $LASTEXITCODE" }
