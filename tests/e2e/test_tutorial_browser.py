"""Public tutorial browsing uses no database, accounts or mocked responses."""
import os
from pathlib import Path
import socket
import subprocess
import sys
import time
import unittest
import urllib.request

ROOT=Path(__file__).resolve().parents[2]


class TutorialBrowserTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from playwright.sync_api import sync_playwright
        with socket.socket() as sock:
            sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
        cls.url=f'http://127.0.0.1:{port}'
        cls.artifacts=ROOT/'e2e-artifacts';cls.artifacts.mkdir(exist_ok=True)
        cls.log=open(cls.artifacts/'task21-1-public-server.log','w')
        cls.server=subprocess.Popen([sys.executable,'-m','uvicorn','backend.app.api:app','--host','127.0.0.1','--port',str(port)],cwd=ROOT,env={**os.environ,'DATABASE_URL':'postgresql://invalid','DATA_QA_DEMO_MODE':'0'},stdout=cls.log,stderr=cls.log)
        for _ in range(100):
            try:urllib.request.urlopen(cls.url+'/api/courses',timeout=1);break
            except Exception:
                if cls.server.poll() is not None:raise RuntimeError('Inspect task21-1-public-server.log')
                time.sleep(.1)
        else:raise RuntimeError('Public server startup timeout')
        cls.playwright=sync_playwright().start();cls.browser=cls.playwright.chromium.launch(headless=True)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close();cls.playwright.stop();cls.server.terminate();cls.server.wait(timeout=10);cls.log.close()

    def test_public_discovery_deep_links_translations_theme_copy_and_planned(self):
        from playwright.sync_api import expect
        base=self.url+'/courses/ai-test-automation'
        with self.browser.new_context(permissions=['clipboard-read','clipboard-write']) as context:
            page=context.new_page();writes=[]
            page.on('request',lambda request:writes.append(request.url) if request.method=='POST' else None)
            page.goto(self.url+'/courses')
            expect(page.locator('[data-course-id="ai-test-automation"]')).to_be_visible()
            page.locator('.header-subjects summary').click()
            page.locator('#header-subject-links a[href="/subjects/ai-test-automation"]').click()
            expect(page.locator('.course-grid .course-card')).to_have_count(1)
            page.locator('.course-card-link').click();expect(page.locator('[data-module-id]')).to_have_count(10)
            for language in ('ENG','VIE'):
                page.get_by_label('Select language').select_option(language)
                for theme in ('dark','light'):
                    if page.locator('html').get_attribute('data-theme')!=theme:page.locator('.theme-toggle').click()
                    for width in (375,768,1280):
                        page.set_viewport_size({'width':width,'height':900})
                        page.goto(self.url+'/courses')
                        expect(page.locator('[data-course-id="ai-test-automation"]')).to_be_visible()
                        page.screenshot(path=str(self.artifacts/f'task21-1-catalog-{language}-{theme}-{width}.png'),full_page=True)
                        page.goto(base)
                        expect(page.locator('[data-tutorial-id]')).to_have_count(30)
                        expect(page.locator('[data-tutorial-id] a')).to_have_count(1)
                        expect(page.locator('.tutorial-overview')).to_contain_text('29')
                        self.assertLessEqual(page.evaluate('document.documentElement.scrollWidth'),width)
                        page.screenshot(path=str(self.artifacts/f'task21-1-overview-{language}-{theme}-{width}.png'),full_page=True)
                        page.locator('[data-tutorial-id="m01-l01"] a').click()
                        expect(page.locator('.tutorial-section')).to_have_count(10)
                        page.reload();expect(page.locator('.tutorial-section')).to_have_count(10)
                        expect(page.locator('html')).to_have_attribute('data-theme',theme)
                        expect(page.get_by_label('Select language')).to_have_value(language)
                        self.assertLessEqual(page.evaluate('document.documentElement.scrollWidth'),width)
                        expect(page.locator('h1')).to_have_text('Why automate? Test pyramid & ROI' if language=='ENG' else 'Vì sao tự động hóa? Tháp kiểm thử & ROI')
                        expect(page.locator('.tutorial-player')).to_contain_text('not automatically graded' if language=='ENG' else 'không chấm tự động')
                        for block in page.locator('.tutorial-code').all():
                            text=block.locator('code').inner_text();button=block.locator('button')
                            button.focus();button.press('Enter')
                            expect(block.locator('[role=status]')).to_have_text('Copied' if language=='ENG' else 'Đã copy')
                            # Windows clipboard normalizes LF to CRLF.
                            self.assertEqual(page.evaluate('navigator.clipboard.readText()').replace('\r\n','\n'),text)
                        page.screenshot(path=str(self.artifacts/f'task21-1-player-{language}-{theme}-{width}.png'),full_page=True)
                        page.locator('.tutorial-code').nth(1).screenshot(path=str(self.artifacts/f'task21-1-code-{language}-{theme}-{width}.png'))
                        page.go_back();expect(page.locator('[data-tutorial-id]')).to_have_count(30)
                        page.go_forward();expect(page.locator('.tutorial-section')).to_have_count(10)
            # Failure feedback leaves selectable code intact.
            page.evaluate("()=>{navigator.clipboard.writeText=async()=>{throw new Error('denied')}}")
            block=page.locator('.tutorial-code').first;block.locator('button').click()
            expect(block.locator('[role=status]')).to_contain_text('copy thủ công')
            page.goto(base+'/tutorials/m01-l02');expect(page.locator('main')).to_contain_text('đang dự kiến')
            expect(page.locator('.tutorial-code')).to_have_count(0)
            page.goto(base+'/tutorials/m99-l01');expect(page.locator('main h1')).to_have_text('Không tìm thấy trang')
            self.assertEqual(writes,[])
            self.assertEqual(context.request.get(self.url+'/api/auth/me').json()['user'],None)
            for endpoint in ('sessions','progress','enrollments'):
                self.assertEqual(context.request.get(self.url+'/api/'+endpoint).status,401)
