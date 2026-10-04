"""Real browser + HTTP + PostgreSQL, with no mocked API responses."""
import os
from pathlib import Path
import socket
import subprocess
import sys
import time
import unittest
import urllib.request

DB = os.getenv("DATA_QA_TEST_DATABASE_URL")
ROOT = Path(__file__).resolve().parents[2]


@unittest.skipUnless(DB, "PostgreSQL and built frontend required")
class BrowserTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from backend.app.persistence.database import initialize_database
        from backend.app.learning.sql_runtime import initialize_sql_security
        from pipeline.source.seed import seed_source
        from pipeline.jobs.orders import run_orders_pipeline
        from playwright.sync_api import sync_playwright
        initialize_database(DB)
        initialize_sql_security(DB)
        seed_source(DB, 20)
        run_orders_pipeline(DB)
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            cls.port = sock.getsockname()[1]
        cls.url = f"http://127.0.0.1:{cls.port}"
        cls.log = open(ROOT / "e2e-server.log", "w")
        cls.server = subprocess.Popen([sys.executable,"-m","uvicorn","backend.app.api:app","--host","127.0.0.1","--port",str(cls.port)], cwd=ROOT,env={**os.environ,"DATABASE_URL":DB},stdout=cls.log,stderr=cls.log)
        for _ in range(100):
            try:
                urllib.request.urlopen(cls.url+"/api/health", timeout=1)
                break
            except Exception:
                if cls.server.poll() is not None:
                    raise RuntimeError("API server exited; inspect e2e-server.log")
                time.sleep(.1)
        else:
            cls.server.terminate()
            raise RuntimeError("API startup timeout")
        cls.playwright = sync_playwright().start()
        cls.browser = cls.playwright.chromium.launch(headless=True)
        cls.artifacts = ROOT / "e2e-artifacts"
        cls.artifacts.mkdir(exist_ok=True)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright.stop()
        cls.server.terminate()
        cls.server.wait(timeout=10)
        cls.log.close()

    def setUp(self):
        self.context = self.browser.new_context(viewport={"width":1440,"height":1000})
        self.page = self.context.new_page()
        self.errors = []
        self.page.on("pageerror", lambda exc:self.errors.append(str(exc)))

    def tearDown(self):
        self.page.screenshot(path=str(self.artifacts / (self._testMethodName+".png")), full_page=True)
        self.context.close()
        self.assertEqual(self.errors, [])

    def idle(self):
        self.page.locator(".working").wait_for(state="hidden")

    def select_lab(self):
        self.page.goto(self.url)
        self.page.locator(".lesson-card").first.wait_for()
        self.idle()
        self.page.get_by_label("Select language").select_option("ENG")
        card = self.page.locator(".lesson-card").filter(has_text="Equal counts, different orders")
        card.wait_for()
        card.get_by_role("button").click()
        if self.page.locator(".new-attempt").count():
            self.page.locator(".new-attempt").click()
        self.page.get_by_label("Mode", exact=True).select_option("SANDBOX")
        self.page.get_by_label("Scenario", exact=True).select_option("equal_count_swap")
        self.page.locator(".work-column .primary").click()
        self.page.get_by_label("SQL editor", exact=True).wait_for()
        self.idle()

    def sql(self, text):
        editor = self.page.get_by_label("SQL editor", exact=True)
        editor.click()
        editor.press("ControlOrMeta+a")
        editor.fill(text)

    def test_browser_learning_loop_language_history_and_pipeline(self):
        from backend.app.learning.content import SOLUTION
        from playwright.sync_api import expect
        self.select_lab()
        self.sql("SELECT abs((SELECT COUNT(*) FROM source_orders) - (SELECT COUNT(*) FROM target_orders)) AS violation_count")
        self.page.get_by_role("button",name="Run SQL",exact=False).click()
        self.idle()
        expect(self.page.locator(".table-scroll tbody td").first).to_have_text("0")
        draft=self.page.get_by_label("SQL editor",exact=True).inner_text()
        self.page.get_by_label("Select language").select_option("VIE")
        expect(self.page.locator(".lesson-heading h1")).to_have_text("Bằng số lượng, khác bản ghi")
        expect(self.page.get_by_label("SQL editor",exact=True)).to_have_text(draft)
        self.page.locator("#conclusion").fill("Count bằng nhau chưa chứng minh đầy đủ.")
        self.page.get_by_role("button",name="Nộp bài",exact=True).click()
        self.idle()
        expect(self.page.locator(".notice.fail .badge")).to_have_text("FAIL")
        self.page.get_by_role("button",name="Nhận gợi ý",exact=False).click()
        self.idle()
        self.sql(SOLUTION)
        self.page.get_by_role("button",name="Nộp bài",exact=True).click()
        self.idle()
        expect(self.page.locator(".lesson-heading .badge")).to_have_text("COMPLETED")
        expect(self.page.locator(".solution")).to_be_visible()
        self.page.reload()
        expect(self.page.locator(".lesson-heading .badge")).to_have_text("COMPLETED")
        expect(self.page.get_by_label("Select language")).to_have_value("VIE")
        self.page.get_by_role("button",name="Lịch sử học",exact=False).click()
        expect(self.page.locator(".session-row").first).to_be_visible()
        self.page.get_by_role("button",name="Pipeline & QA",exact=False).click()
        self.idle()
        expect(self.page.locator(".stage-grid .stage")).to_have_count(5)
        self.page.get_by_role("button",name="Chạy bộ QA",exact=True).click()
        self.idle()
        expect(self.page.locator(".run-status .badge").nth(1)).to_have_text("PASS")
        self.page.set_viewport_size({"width":390,"height":844})
        self.assertLessEqual(self.page.evaluate("document.documentElement.scrollWidth"), 390)

    def test_reveal_is_not_completion_and_mobile_layout(self):
        from playwright.sync_api import expect
        self.select_lab()
        self.page.on("dialog", lambda dialog:dialog.accept())
        self.page.get_by_role("button",name="Reveal solution",exact=True).click()
        self.idle()
        expect(self.page.locator(".lesson-heading .badge")).to_have_text("REVEALED")
        expect(self.page.get_by_role("button",name="Submit check",exact=True)).to_be_disabled()
        self.page.set_viewport_size({"width":390,"height":844})
        self.assertLessEqual(self.page.evaluate("document.documentElement.scrollWidth"),390)

    def test_all_six_lessons_are_usable_through_the_browser(self):
        from playwright.sync_api import expect
        from backend.app.learning.lessons import CATALOG
        from backend.app.learning.profiles import PROFILES
        self.page.goto(self.url)
        self.page.locator(".lesson-card").first.wait_for()
        self.idle()
        self.page.get_by_label("Select language").select_option("ENG")
        expect(self.page.locator(".lesson-card")).to_have_count(6)
        for lab_id in sorted(CATALOG, key=lambda key:CATALOG[key]["order"]):
            title=CATALOG[lab_id]["ENG"]["title"]
            self.page.locator(".lesson-card").filter(has_text=title).get_by_role("button").click()
            if self.page.locator(".new-attempt").count():
                self.page.locator(".new-attempt").click()
            self.page.locator(".work-column .primary").click()
            self.page.get_by_label("SQL editor",exact=True).wait_for()
            self.idle()
            self.page.get_by_role("button",name="Run SQL",exact=False).click()
            self.idle()
            expect(self.page.locator(".work-column .panel").nth(1).locator(".badge")).to_have_text("SUCCESS")
            self.sql(PROFILES[lab_id].solution)
            self.page.locator("#conclusion").fill("Checked the documented contract on clean and defective data.")
            self.page.get_by_role("button",name="Submit check",exact=True).click()
            self.idle()
            expect(self.page.locator(".lesson-heading .badge")).to_have_text("COMPLETED")
            self.page.locator(".back").click()
        self.page.screenshot(path=str(self.artifacts/"v1-learning-catalog-desktop.png"),full_page=True)
