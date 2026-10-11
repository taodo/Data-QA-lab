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
        from backend.app import accounts, public_demo
        name = "data_qa_demo_browser_" + uuid4().hex
        db = make_conninfo(DB, dbname=name)
        with connect(DB) as admin:
            admin.autocommit = True
            admin.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(name)))
        server = None
        artifacts = ROOT / "e2e-artifacts"
        artifacts.mkdir(exist_ok=True)
        env = {**os.environ, "DATABASE_URL": db, "DATA_QA_DEMO_MODE": "1", "DATA_QA_PUBLIC_DEMO_ENABLED": "1", "DATA_QA_PUBLIC_HOSTS": HOST, "DATA_QA_TRUSTED_PROXIES": "127.0.0.1"}
        try:
            with patch.dict(os.environ, env):
                prepare_local(db)
                _, token = accounts.signup(db, "browser_demo", "Demo browser", PASSWORD)
                accounts.logout(db, {"token_hash": accounts.token_hash(token)})
                public_demo.provision(db, 2)
                entries = public_demo.listing(db)
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
                    disclosure = page.locator(".demo-accounts")
                    expect(disclosure).to_be_visible()
                    self.assertFalse(disclosure.evaluate("e=>e.open"))
                    disclosure.locator("summary").focus()
                    page.keyboard.press("Enter")
                    expect(page.locator(".demo-account-card")).to_have_count(2)
                    card = page.locator(".demo-account-card").first
                    expect(card.locator("code")).to_have_text("••••••••••••")
                    card.get_by_role("button", name="Show password", exact=False).click()
                    self.assertTrue(card.locator("code").inner_text() == entries[0]["password"])
                    card.get_by_role("button", name="Hide password", exact=False).click()
                    # Clipboard test retains no plaintext in artifacts/logs.
                    context.grant_permissions(["clipboard-read", "clipboard-write"])
                    card.get_by_role("button", name="Copy password", exact=False).click()
                    expect(card.get_by_role("status")).to_have_text("Password copied.")
                    self.assertTrue(page.evaluate("async p=>(await navigator.clipboard.readText())===p", entries[0]["password"]))
                    page.set_viewport_size({"width": 1440, "height": 900})
                    self.assertLessEqual(page.evaluate("document.documentElement.scrollWidth"), 1440)
                    page.screenshot(path=str(artifacts / "public-demo-login-desktop-ENG.png"), full_page=True)
                    for width, language, button, theme in ((375, "ENG", "Use this account", "dark"), (390, "VIE", "Dùng tài khoản này", "light")):
                        page.set_viewport_size({"width": width, "height": 844})
                        if page.locator('html').get_attribute('data-theme') != theme:
                            page.locator('.theme-toggle').click()
                        expect(page.locator('html')).to_have_attribute('data-theme', theme)
                        page.get_by_label("Select language").select_option(language)
                        card.get_by_role("button", name=button, exact=False).click()
                        self.assertTrue(page.locator('input[name="username"]').input_value() == entries[0]["username"])
                        self.assertTrue(page.locator('input[name="password"]').input_value() == entries[0]["password"])
                        expect(page.locator('input[name="password"]')).to_have_attribute("type", "password")
                        self.assertEqual(page.url, origin + "/login")
                        self.assertLessEqual(page.evaluate("document.documentElement.scrollWidth"), width)
                        page.screenshot(path=str(artifacts / f"public-demo-login-{width}-{language}.png"), full_page=True)
                        page.screenshot(path=str(artifacts / f"task20-{theme}-public-demo-{width}-{language}.png"), full_page=True)
                    page.get_by_label("Select language").select_option("ENG")
                    page.locator(".auth-form button.primary").click()
                    page.wait_for_url(origin + "/my-learning")
                    expect(page.locator('html')).to_have_attribute('data-theme', 'light')
                    page.goto(origin + "/account")
                    expect(page.get_by_text("Shared demo passwords can only be changed by the local operator.")).to_be_visible()
                    expect(page.locator(".auth-form")).to_have_count(0)
                    page.locator(".account-menu summary").click()
                    page.get_by_role("button", name="Log out", exact=True).click()
                    page.wait_for_url(origin + "/")
                    for language, title in (("ENG", "Sign Up — Coming Soon"), ("VIE", "Đăng ký — Sắp có")):
                        page.goto(origin + "/signup")
                        page.get_by_label("Select language").select_option(language)
                        expect(page.get_by_role("heading", name=title, exact=True)).to_be_visible()
                        expect(page.locator('input[name="username"]')).to_have_count(0)
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
                    with page.expect_response(lambda r: "/submit?" in r.url and r.request.method == "POST") as submitted:
                        page.get_by_role("button", name="Submit check", exact=True).click()
                    self.assertEqual(submitted.value.status, 200)
                    self.assertEqual(submitted.value.json()["status"], "PASS")
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
