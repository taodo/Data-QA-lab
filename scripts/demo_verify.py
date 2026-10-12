"""Exercise the real loopback proxy using a simulated external HTTPS origin.

Never starts cloudflared. Secure cookies are explicitly forwarded over the local
origin leg only. This cannot verify Cloudflare edge TLS or an external device.
"""
import argparse
from getpass import getpass
import json
from pathlib import Path
import secrets
import re
import subprocess
import time
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
COMPOSE = ["docker", "compose", "-p", "data-qa-demo", "--env-file", str(ROOT / "data/generated/demo/.env.demo"), "-f", str(ROOT / "docker-compose.demo.yml")]


def valid_demo_hostname(hostname):
    return hostname == "data-qa-lab.store" or re.fullmatch(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.trycloudflare\.com", hostname) is not None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--hostname", required=True)
    parser.add_argument("--username", default="demo_learner")
    parser.add_argument("--self-test", action="store_true", help="Provision one random test account through existing signup; no password is saved")
    parser.add_argument("--public-account", help="Use one explicitly public shared account from the read-only listing; never prints credentials")
    parser.add_argument("--restart", action="store_true", help="Restart only the demo app and verify retained history")
    args = parser.parse_args()
    if not valid_demo_hostname(args.hostname):
        raise SystemExit("Supply one exact lowercase generated trycloudflare.com hostname or data-qa-lab.store")
    if args.public_account and args.self_test:
        raise SystemExit("Choose --public-account or --self-test")
    name = "probe_" + secrets.token_hex(6) if args.self_test else args.username
    password = secrets.token_urlsafe(24) if args.self_test else (None if args.public_account else getpass("Demo password: "))
    if args.self_test:
        code = "import json,sys; from backend.app import accounts; from backend.app.config import Settings; name,password=json.load(sys.stdin); db=Settings.from_env().database_url; payload,token=accounts.signup(db,name,'Proxy verification',password); accounts.logout(db,{'token_hash':accounts.token_hash(token)})"
        subprocess.run([*COMPOSE, "exec", "-T", "app", "python", "-c", code], input=json.dumps([name, password]), text=True, check=True, cwd=ROOT)
    origin = "https://" + args.hostname
    headers = {"Host": args.hostname, "Origin": origin, "X-Forwarded-Proto": "https", "X-DQA-Intent": "1"}

    def api(path, body=None, extra=None, status=200):
        request_headers = {**headers, **(extra or {})}
        if body is not None:
            request_headers["Content-Type"] = "application/json"
        request = urllib.request.Request("http://127.0.0.1:8001/api" + path, data=json.dumps(body).encode() if body is not None else None, headers=request_headers)
        try:
            result = urllib.request.urlopen(request, timeout=35)
        except urllib.error.HTTPError as error:
            result = error
        assert result.status == status, (path, result.status)  # Never log credential responses.
        raw = result.read()
        payload = json.loads(raw) if result.headers.get_content_type() == "application/json" else raw.decode()
        return payload, result.headers

    if args.public_account:
        catalog, catalog_headers = api("/auth/demo")
        assert catalog_headers["Cache-Control"] == "no-store"
        assert 0 < len(catalog["accounts"]) <= 10
        entry = next((e for e in catalog["accounts"] if e["username"] == args.public_account), None)
        if not entry:
            raise SystemExit("Selected public demo account unavailable")
        name, password = entry["username"], entry["password"]
    auth, cookies = api("/auth/login", {"username": name, "password": password})
    cookie = cookies["Set-Cookie"]
    assert "Secure" in cookie and "HttpOnly" in cookie and "SameSite=lax" in cookie
    headers.update({"Cookie": cookie.split(";", 1)[0], "X-CSRF-Token": auth["csrf_token"]})
    assert api("/auth/me")[0]["user"]["username"] == name
    if args.public_account:
        assert auth["user"]["public_shared"]
        denied, _ = api("/auth/password", {"current_password": password, "new_password": secrets.token_urlsafe(24)}, status=403)
        assert denied["error"]["code"] == "PUBLIC_DEMO_PASSWORD_LOCKED"
    for language in ("ENG", "VIE"):
        courses = api("/courses?language=" + language)[0]
        assert len(courses) == 10
        executable = [c for c in courses if c["learning_kind"] == "executable_lab"]
        assert len(executable) == 9 and sum(c["lesson_count"] for c in executable) == 36
        tutorial = next(c for c in courses if c["id"] == "ai-test-automation")
        assert tutorial["learning_kind"] == "tutorial" and tutorial["available_lesson_count"] == 1
        api("/courses/sql-data-qa?language=" + language)
    session, _ = api("/sessions", {"lab_id": "lab_001_record_count", "mode": "SANDBOX", "scenario": "clean"}, status=201)
    path = "/sessions/" + session["session_id"]
    assert api(path + "/query", {"sql": "SELECT COUNT(*) FROM source_orders"})[0]["status"] == "SUCCESS"
    check = (ROOT / "examples/lab_001_key_check.sql").read_text()
    assert api(path + "/submit", {"sql": check, "conclusion": "Reconciled source and target keys through the HTTPS proxy origin."})[0]["status"] == "PASS"
    before = [api(path + "/history/" + kind)[0] for kind in ("queries", "submissions")]
    api(path + "/hint", {}, {"X-CSRF-Token": "wrong"}, status=403)
    api(path + "/hint", {}, {"Origin": "https://evil.example"}, status=403)
    api("/courses", extra={"Host": "unapproved.invalid"}, status=400)
    api("/courses", extra={"X-Forwarded-Proto": "http"}, status=400)
    api("/courses", extra={"X-Forwarded-Proto": "https,http"}, status=400)
    api("/courses", extra={"X-Forwarded-Proto": "ftp"}, status=400)
    api("/courses", extra={"Host": "localhost", "Origin": "http://localhost", "X-Forwarded-Proto": "http"})
    api("/auth/signup", {"username": "public_signup", "display_name": "Public", "password": password}, status=403)
    if args.restart:
        subprocess.run([*COMPOSE, "restart", "app"], check=True, cwd=ROOT)
        for _ in range(60):
            try:
                api("/health")
                break
            except (AssertionError, OSError):
                time.sleep(1)
        else:
            raise RuntimeError("Demo app did not recover")
    assert before == [api(path + "/history/" + kind)[0] for kind in ("queries", "submissions")]
    if args.public_account:
        assert api("/auth/demo")[0] == catalog
    api("/auth/logout", {})
    assert api("/auth/me")[0]["user"] is None
    print("PASS: real demo proxy HTTPS-origin login, ENG/VIE courses, SQL, submission, saved history, CSRF, exact hosts, logout" + (", restart retention" if args.restart else ""))
    print("PENDING: public tunnel / Cloudflare edge / external-device verification. No tunnel was opened.")


if __name__ == "__main__":
    main()
