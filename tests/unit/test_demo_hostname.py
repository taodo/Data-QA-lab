"""Exercise the actual PowerShell action with isolated env files and a fake Docker.

Never invoke the user's demo project, cloudflared, credentials or PostgreSQL.
"""
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from scripts.demo_verify import valid_demo_hostname

ROOT = Path(__file__).resolve().parents[2]
SHELL = shutil.which("pwsh") or shutil.which("powershell")
VALID = ("data-qa-lab.store", "a.trycloudflare.com", "demo-123.trycloudflare.com", "a" * 63 + ".trycloudflare.com")
INVALID = ("", "*", "*.trycloudflare.com", "*.data-qa-lab.store", "https://data-qa-lab.store", "data-qa-lab.store:443",
           "DATA-QA-LAB.STORE", "Demo.trycloudflare.com", "demo.trycloudflare.com:443", "https://demo.trycloudflare.com",
           "www.data-qa-lab.store", "other.store", "data-qa-lab.store.evil.example", "trycloudflare.com",
           "a.b.trycloudflare.com", "-a.trycloudflare.com", "a-.trycloudflare.com", "a" * 64 + ".trycloudflare.com",
           "bad..trycloudflare.com", " demo.trycloudflare.com", "demo.trycloudflare.com\n", "data-qa-lab.store\n",
           "demo.trycloudflare.com.", "data-qa-lab.store/path", "demo.trycloudflare.com,evil.example")


class DemoHostnameTests(unittest.TestCase):
    def test_verifier_hostname_policy(self):
        for host in VALID:
            with self.subTest(host=host):
                self.assertTrue(valid_demo_hostname(host))
        for host in INVALID:
            with self.subTest(host=host):
                self.assertFalse(valid_demo_hostname(host))

    @unittest.skipUnless(SHELL, "PowerShell required for real SetHostname execution")
    def test_sethostname_exact_policy_and_env_preservation(self):
        directory = ROOT / "data/generated/hostname-tests"
        directory.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=directory) as temporary:
            fixture = Path(temporary)
            cases = [{"host": host, "valid": host in VALID} for host in (*VALID, *INVALID)]
            (fixture / "cases.json").write_text(json.dumps(cases), encoding="utf-8")
            # Mock only filesystem routing and Docker. All validation, env writes
            # and Compose argument construction execute scripts/demo.ps1 itself.
            wrapper = r'''
param([string]$Script, [string]$Fixture)
$ErrorActionPreference = 'Stop'
$global:demoFixture = $Fixture
function Resolve-Path { param($Path) [pscustomobject]@{Path='D:\Data-QA-Lab'} }
function Set-Location { param($LiteralPath) }
function Join-Path {
    param($Path,$ChildPath)
    if ($ChildPath -eq 'data\generated\demo') { return $global:demoFixture }
    Microsoft.PowerShell.Management\Join-Path -Path $Path -ChildPath $ChildPath
}
function docker { $global:dockerCalls += ,@($args); $global:LASTEXITCODE=0 }
$results = @()
$envPath = Microsoft.PowerShell.Management\Join-Path $Fixture '.env.demo'
foreach ($case in (Get-Content (Microsoft.PowerShell.Management\Join-Path $Fixture 'cases.json') -Raw | ConvertFrom-Json)) {
    $initial = "DEMO_DB_PASSWORD=test-only-placeholder`nDEMO_PUBLIC_HOST=old.trycloudflare.com`nOTHER_SETTING=retained`n"
    [IO.File]::WriteAllText($envPath,$initial)
    $global:dockerCalls=@()
    $accepted=$true
    try { & $Script -Action SetHostname -Hostname $case.host | Out-Null } catch { $accepted=$false }
    $text=[IO.File]::ReadAllText($envPath)
    $results += [pscustomobject]@{
        accepted=$accepted
        hostname=[regex]::Match($text,'(?m)^DEMO_PUBLIC_HOST=([^\r\n]*)').Groups[1].Value
        unchanged=($text -ceq $initial)
        retained=($text.Contains('DEMO_DB_PASSWORD=test-only-placeholder') -and $text.Contains('OTHER_SETTING=retained'))
        calls=@($global:dockerCalls)
    }
}
ConvertTo-Json -Depth 5 -InputObject @($results) -Compress
'''
            script = fixture / "run.ps1"
            script.write_text(wrapper, encoding="utf-8")
            result = subprocess.run([SHELL, "-NoProfile", "-NonInteractive", "-File", str(script), "-Script", str(ROOT / "scripts/demo.ps1"), "-Fixture", str(fixture)], capture_output=True, text=True, timeout=60)
            self.assertEqual(result.returncode, 0, result.stderr)
            observed = json.loads(result.stdout)
            self.assertEqual(len(observed), len(cases))
            for case, outcome in zip(cases, observed):
                with self.subTest(host=case["host"]):
                    self.assertEqual(outcome["accepted"], case["valid"])
                    self.assertTrue(outcome["retained"])
                    if case["valid"]:
                        self.assertEqual(outcome["hostname"], case["host"])
                        self.assertEqual(len(outcome["calls"]), 1)
                        args = outcome["calls"][0]
                        self.assertEqual(args[:4], ["compose", "-p", "data-qa-demo", "--env-file"])
                        self.assertEqual(args[4], str(fixture / ".env.demo"))
                        self.assertIn("--no-deps", args)
                        self.assertEqual(args[-2:], ["app", "proxy"])
                    else:
                        self.assertTrue(outcome["unchanged"])
                        self.assertEqual(outcome["calls"], [])
