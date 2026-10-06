"""Browser at a simulated HTTPS URL, actual HTTP origin/app; no public tunnel.

Playwright routes the local origin leg. Edge TLS/external-device proof is pending.
Real nginx packaging is independently covered by scripts.demo_verify in CI.
"""
import os
from pathlib import Path
import socket
import subprocess
import sys
import time
import unittest
from unittest.mock import patch
import urllib.request
from uuid import uuid4
from psycopg import sql
from psycopg.conninfo import make_conninfo
from backend.app.persistence.database import connect

DB = os.getenv("DATA_QA_TEST_DATABASE_URL")
ROOT = Path(__file__).resolve().parents[2]
HOST = "browser-demo.trycloudflare.com"
PASSWORD = "demo-browser-test-passphrase"


@unittest.skipUnless(DB, "PostgreSQL, built frontend and Playwright required")
class DemoBrowserTests(unittest.TestCase):
    def test_secure_cookie_login_mobile_courses_sql_submit_resume(self):
        from playwright.sync_api import sync_playwright, expect
        from backend.app.bootstrap import prepare_local
        from backend.app import accounts
        name = "data_qa_demo_browser_" + uuid4().hex
        db = make_conninfo(DB, dbname=name)
        with connect(DB) as admin:
            admin.autocommit = True
            admin.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(name)))
        server = None
        artifacts = ROOT / "e2e-artifacts"
        artifacts.mkdir(exist_ok=True)
        env = {**os.environ, "DATABASE_URL": db, "DATA_QA_DEMO_MODE": "1", "DATA_QA_PUBLIC_HOSTS": HOST, "DATA_QA_TRUSTED_PROXIES": "127.0.0.1"}
        try:
            with patch.dict(os.environ, env):
                prepare_local(db)
                _, token = accounts.signup(db, "browser_demo", "Demo browser", PASSWORD)
                accounts.logout(db, {"token_hash": accounts.token_hash(token)})
            with socket.socket() as sock:
                sock.bind(("127.0.0.1", 0))
                port = sock.getsockname()[1]
            local = f"http://127.0.0.1:{port}"
            origin = "https://" + HOST
            with (artifacts / "demo-origin.log").open("w") as log:
                server = subprocess.Popen([sys.executable, "-m", "uvicorn", "backend.app.api:app", "--host", "127.0.0.1", "--port", str(port), "--no-proxy-headers"], cwd=ROOT, env=env, stdout=log, stderr=log)
                for _ in range(100):
                    try:
                        urllib.request.urlopen(urllib.request.Request(local + "/api/health", headers={"X-Forwarded-Proto": "http"}), timeout=1)
                        break
                    except OSError:
                        time.sleep(.1)
                else:
                    raise RuntimeError("Demo origin startup failed")
                with sync_playwright() as playwright:
                    browser = playwright.chromium.launch(headless=True)
                    context = browser.new_context(viewport={"width": 390, "height": 844})
                    def origin_leg(route):
                        request = route.request
                        headers = {**request.all_headers(), "host": HOST, "x-forwarded-proto": "https"}
                        result = route.fetch(url=local + request.url[len(origin):], headers=headers)
                        route.fulfill(response=result)
                    context.route(origin + "/**", origin_leg)
                    page = context.new_page()
                    page.goto(origin + "/login")
                    page.get_by_label("Select language").select_option("ENG")
                    page.locator('input[name="username"]').fill("browser_demo")
                    page.locator('input[type="password"]').fill(PASSWORD)
                    page.locator(".auth-form button.primary").click()
                    page.wait_for_url(origin + "/my-learning")
                    cookies = [cookie for cookie in context.cookies() if cookie["name"] == accounts.COOKIE]
                    self.assertTrue(cookies and cookies[0]["secure"] and cookies[0]["httpOnly"])
                    page.goto(origin + "/courses/sql-data-qa")
                    expect(page.locator(".lesson-card")).to_have_count(13)
                    page.get_by_label("Select language").select_option("VIE")
                    expect(page.locator(".lesson-card")).to_have_count(13)
                    page.get_by_label("Select language").select_option("ENG")
                    page.locator(".lesson-card[data-lab-id='lab_001_record_count'] button").click()
                    page.locator(".work-column .primary").click()
                    editor = page.get_by_label("SQL editor", exact=True)
                    expect(editor).to_be_visible()
                    editor.fill("SELECT COUNT(*) FROM source_orders")
                    page.get_by_role("button", name="Run SQL", exact=False).click()
                    expect(page.locator(".query-result .badge")).to_have_text("SUCCESS")
                    editor.fill((ROOT / "examples/lab_001_key_check.sql").read_text())
                    page.locator("#conclusion").fill("Checked business keys through the HTTPS origin.")
                    page.get_by_role("button", name="Submit check", exact=True).click()
                    expect(page.locator(".lesson-heading .badge")).to_have_text("Completed")
                    page.reload()
                    expect(page.locator(".lesson-heading .badge")).to_have_text("Completed")
                    self.assertLessEqual(page.evaluate("document.documentElement.scrollWidth"), 390)
                    page.screenshot(path=str(artifacts / "demo-https-origin-mobile.png"), full_page=True)
                    context.close()
                    browser.close()
        finally:
            if server:
                server.terminate()
                server.wait(timeout=10)
            with connect(DB) as admin:
                admin.autocommit = True
                admin.execute(sql.SQL("DROP DATABASE {} WITH (FORCE)").format(sql.Identifier(name)))
