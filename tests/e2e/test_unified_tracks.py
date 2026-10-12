"""Actual U2 public HTTP/browser checks; no database or domain services needed."""
import unittest
from urllib.parse import urlparse
from tests.e2e import test_tutorial_browser as public_fixture


class UnifiedTrackBrowserTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Reuse the existing real public server/browser setup, not its tests.
        public_fixture.TutorialBrowserTests.setUpClass.__func__(cls)

    @classmethod
    def tearDownClass(cls):public_fixture.TutorialBrowserTests.tearDownClass.__func__(cls)

    def test_tracks_discovery_preferences_keyboard_and_responsive(self):
        from playwright.sync_api import expect
        with self.browser.new_context() as context:
            page=context.new_page();requests=[]
            page.on('request',lambda r:requests.append((r.method,r.url)))
            for language in ('ENG','VIE'):
                page.goto(self.url);page.get_by_label('Select language').select_option(language)
                for theme in ('dark','light'):
                    if page.locator('html').get_attribute('data-theme')!=theme:page.locator('.theme-toggle').click()
                    for width in (375,768,1280):
                        page.set_viewport_size({'width':width,'height':900})
                        page.goto(self.url)
                        expect(page.locator('.learning-track-card')).to_have_count(3)
                        expect(page.locator('.unified-hero h1')).to_have_text('Unified QA Learning Platform' if language=='ENG' else 'Nền tảng học QA thống nhất')
                        expect(page.locator('[data-track-id="data-qa"] .track-facts')).to_contain_text('36')
                        expect(page.locator('[data-track-id="automation-qa"] .track-facts')).to_contain_text('29')
                        expect(page.locator('[data-track-id="banking-qa"]')).to_contain_text('Planned / Coming Soon' if language=='ENG' else 'Dự kiến / Sắp có')
                        page.screenshot(path=str(self.artifacts/f'u2-home-{language}-{theme}-{width}.png'),full_page=True)
                        for track in ('data','banking','automation'):
                            page.goto(self.url)
                            action=page.locator(f'[data-track-id="{track}-qa"] .track-primary-action')
                            action.focus();expect(action).to_be_focused()
                            self.assertEqual(action.evaluate('e=>getComputedStyle(e).outlineStyle'),'solid')
                            action.press('Enter');expect(page).to_have_url(self.url+'/learn/'+track)
                            expect(page.locator('.learning-track-nav [aria-current=page]')).to_have_attribute('href','/learn/'+track)
                            if track=='data':
                                expect(page.locator('.data-track-courses .course-card')).to_have_count(9)
                                expect(page.locator('.landing-metrics')).to_contain_text('36')
                                self.assertNotIn('ai-test-automation',page.locator('.data-track-courses').inner_html())
                            elif track=='banking':
                                expect(page.locator('.planned-track-feature')).to_have_count(2)
                                expect(page.locator('.banking-track')).to_contain_text('not connected' if language=='ENG' else 'chưa kết nối')
                                expect(page.locator('.banking-track :is(form,input,iframe,button,progress)')).to_have_count(0)
                            else:
                                expect(page.locator('.automation-track .course-metadata')).to_contain_text('10')
                                expect(page.locator('.automation-track .course-metadata')).to_contain_text('30')
                                expect(page.locator('.automation-track .button-row a')).to_have_count(2)
                                expect(page.locator('.automation-track a[href="/courses/ai-test-automation/tutorials/m01-l01"]')).to_be_visible()
                                expect(page.locator('.automation-track')).to_contain_text('runs no code' if language=='ENG' else 'không chạy code')
                            page.reload();expect(page.locator('.'+track+'-track')).to_be_visible()
                            expect(page.get_by_label('Select language')).to_have_value(language)
                            expect(page.locator('html')).to_have_attribute('data-theme',theme)
                            expect(page.locator('html')).to_have_attribute('lang','en' if language=='ENG' else 'vi')
                            self.assertLessEqual(page.evaluate('document.documentElement.scrollWidth'),width)
                            page.screenshot(path=str(self.artifacts/f'u2-{track}-{language}-{theme}-{width}.png'))
                            page.go_back();expect(page.locator('.unified-home')).to_be_visible()
                            page.go_forward();expect(page.locator('.'+track+'-track')).to_be_visible()
                        page.locator('.automation-track a[href="/courses/ai-test-automation"]').click()
                        expect(page.locator('[data-tutorial-id]')).to_have_count(30)
                        expect(page.locator('[data-tutorial-id] a')).to_have_count(1)
                        page.locator('[data-tutorial-id="m01-l01"] a').click()
                        expect(page.locator('.tutorial-section')).to_have_count(10)
                        # Same Subjects menu remains usable above the new track nav.
                        trigger=page.locator('.header-subjects summary');trigger.focus();trigger.press('Enter')
                        panel=page.locator('#header-subject-links');expect(panel.locator('a')).to_have_count(10)
                        for link in panel.locator('a').all():
                            link.scroll_into_view_if_needed()
                            self.assertTrue(link.evaluate('e=>{const r=e.getBoundingClientRect();return e.contains(document.elementFromPoint(r.x+r.width/2,r.y+r.height/2))}'))
                        page.keyboard.press('Escape');expect(trigger).to_be_focused()
                        expect(trigger).to_have_attribute('aria-expanded','false')
            page.emulate_media(reduced_motion='reduce');page.goto(self.url)
            expect(page.locator('.unified-home')).to_be_visible()
            self.assertEqual(page.locator('.learning-track-card').first.evaluate('e=>getComputedStyle(e).animationName'),'none')
            self.assertEqual([r for r in requests if r[0]!='GET'],[])
            self.assertTrue(all(urlparse(url).netloc==urlparse(self.url).netloc for _,url in requests))

    def test_unknown_routes_legacy_auth_and_missing_resources(self):
        from playwright.sync_api import expect
        with self.browser.new_context() as context:
            page=context.new_page();page.goto(self.url)
            # Exercise in-app dispatch with the same History event as Link.
            page.evaluate("history.pushState({},'', '/learn/not-a-track');dispatchEvent(new Event('dqa-route'))")
            expect(page.locator('main h1')).to_have_text('Page not found')
            expect(page.locator('main .working')).to_have_count(0)
            for path in ('/learn/not-a-track','/learn/banking/simulator','/learn/automation/playground','/api/not-real','/assets/not-real.js'):
                self.assertEqual(context.request.get(self.url+path).status,404)
            for path in ('/courses','/subjects/sql','/courses/sql-data-qa','/courses/ai-test-automation/tutorials/m01-l01','/login','/signup','/account','/my-learning','/history','/pipeline'):
                self.assertEqual(page.goto(self.url+path).status,200)
                expect(page.locator('main')).to_be_visible()
            for path in ('/my-learning','/history','/pipeline','/account','/courses/sql-data-qa/lessons/lab_001_record_count'):
                page.goto(self.url+path);expect(page.locator('.access-prompt')).to_be_visible()
                expect(page.locator('.access-prompt a.primary')).to_have_attribute('href','/login?next='+__import__('urllib.parse',fromlist=['quote']).quote(path,safe=''))
            page.goto(self.url+'/learn/lab_001_record_count?session=00000000-0000-0000-0000-000000000000')
            expect(page).to_have_url(self.url+'/courses/sql-data-qa/lessons/lab_001_record_count?session=00000000-0000-0000-0000-000000000000')
            expect(page.locator('.access-prompt')).to_be_visible()
            # Tutorial availability request failure is honest and recoverable.
            page.route('**/api/courses/ai-test-automation?language=*',lambda route:route.abort())
            page.goto(self.url+'/learn/automation')
            expect(page.locator('.automation-track [role=alert]')).to_contain_text('could not be loaded')
            expect(page.locator('.automation-track .button-row a')).to_have_count(0)
            page.unroute('**/api/courses/ai-test-automation?language=*')
            page.locator('.automation-track [role=alert] button').click()
            expect(page.locator('.automation-track .button-row a')).to_have_count(2)
