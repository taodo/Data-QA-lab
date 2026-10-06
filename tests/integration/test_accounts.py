"""Real PostgreSQL authorization, durable sessions and explicit legacy upgrade."""
import os
import unittest
from uuid import uuid4
from fastapi.testclient import TestClient
from psycopg import sql
from psycopg.conninfo import make_conninfo
from backend.app.api import create_app
from backend.app import accounts
from backend.app.persistence.database import connect, transaction
from tests.auth_helpers import signed_client, PASSWORD

DB=os.getenv('DATA_QA_TEST_DATABASE_URL')


@unittest.skipUnless(DB,'PostgreSQL test database required')
class AccountIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from backend.app.bootstrap import prepare_local
        cls.name='accounts_test_'+uuid4().hex
        cls.db=make_conninfo(DB,dbname=cls.name)
        with connect(DB) as admin:
            admin.autocommit=True
            admin.execute(sql.SQL('CREATE DATABASE {}').format(sql.Identifier(cls.name)))
        cls.baseline=prepare_local(cls.db)['run_id']

    @classmethod
    def tearDownClass(cls):
        with connect(DB) as admin:
            admin.autocommit=True
            admin.execute(sql.SQL('DROP DATABASE {} WITH (FORCE)').format(sql.Identifier(cls.name)))

    def setUp(self):
        with transaction(self.db) as connection:
            connection.execute('DELETE FROM metadata.auth_budgets')
        self.a,self.user=signed_client(self.db)

    def session(self,client=None,**extra):
        result=(client or self.a).post('/api/sessions',json={'lab_id':'lab_001_record_count',**extra})
        self.assertEqual(result.status_code,201,result.text)
        return result.json()['session_id']

    def test_password_hash_duplicate_signup_and_cookie_contract(self):
        with connect(self.db) as connection:
            stored=connection.execute('SELECT password_hash FROM metadata.accounts WHERE user_id=%s',(self.user['user_id'],)).fetchone()[0]
            token=connection.execute('SELECT token_hash FROM metadata.account_sessions WHERE user_id=%s',(self.user['user_id'],)).fetchone()[0]
        self.assertTrue(stored.startswith('$argon2id$'))
        self.assertTrue(accounts.HASHER.verify(stored,PASSWORD))
        self.assertNotEqual(token,self.a.cookies.get(accounts.COOKIE))
        name='mixed_'+uuid4().hex[:8]
        client=TestClient(create_app(self.db))
        body={'username':name.upper(),'display_name':'Tên học viên','password':PASSWORD}
        result=client.post('/api/auth/signup',json=body,headers={'X-DQA-Intent':'1'})
        self.assertEqual(result.json()['user']['username'],name)
        cookie=result.headers['set-cookie']
        self.assertIn('HttpOnly',cookie);self.assertIn('SameSite=lax',cookie);self.assertIn('Path=/',cookie)
        self.assertEqual(client.post('/api/auth/signup',json={**body,'username':name},headers={'X-DQA-Intent':'1'}).status_code,409)
        self.assertNotIn('password_hash',result.text)
        self.assertEqual(self.a.get('/api/progress').json(),[])
        self.assertEqual(self.a.get('/api/sessions').json(),[])

    def test_csrf_intent_origin_account_and_bounds(self):
        sid=self.session()
        anonymous=TestClient(create_app(self.db))
        self.assertEqual(anonymous.get('/api/sessions/'+sid).status_code,401)
        self.assertEqual(anonymous.post('/api/auth/login',json={'username':self.user['username'],'password':PASSWORD}).status_code,403)
        for headers in ({'X-CSRF-Token':''},{'X-CSRF-Token':'wrong'},{'Origin':'https://other.example'},{'Sec-Fetch-Site':'cross-site'}):
            self.assertEqual(self.a.post('/api/sessions/'+sid+'/hint',headers=headers).status_code,403)
        self.assertEqual(self.a.get('/api/sessions/'+sid,headers={'X-DQA-Account':str(uuid4())}).status_code,409)
        self.assertEqual(self.a.post('/api/sessions',json={'lab_id':'x','admin':True}).status_code,422)
        for path in ('/api/sessions?limit=51','/api/sessions?offset=-1','/api/sessions/not-uuid'):
            self.assertEqual(self.a.get(path).status_code,422)
        self.assertEqual(self.a.post('/api/courses/synapse-testing/enroll').status_code,200)

    def test_password_rotation_logout_expiry_and_operator_recovery(self):
        second=TestClient(create_app(self.db))
        auth=second.post('/api/auth/login',json={'username':self.user['username'],'password':PASSWORD},headers={'X-DQA-Intent':'1'})
        self.assertEqual(auth.status_code,200)
        self.assertEqual(second.get('/api/auth/me').json()['user']['user_id'],self.user['user_id'])
        # Recreate the app with the same DB and cookie: sessions survive server restart.
        restarted=TestClient(create_app(self.db));restarted.cookies.update(second.cookies)
        self.assertEqual(restarted.get('/api/auth/me').json()['user']['user_id'],self.user['user_id'])
        before=self.a.cookies.get(accounts.COOKIE)
        self.assertEqual(self.a.post('/api/auth/password',json={'current_password':'incorrect-passphrase','new_password':PASSWORD+'new'}).status_code,401)
        result=self.a.post('/api/auth/password',json={'current_password':PASSWORD,'new_password':PASSWORD+'new'})
        self.assertEqual(result.status_code,200,result.text)
        self.assertNotEqual(before,self.a.cookies.get(accounts.COOKIE))
        self.a.headers['X-CSRF-Token']=result.json()['csrf_token']
        self.assertIsNone(second.get('/api/auth/me').json()['user'])
        self.assertIsNone(restarted.get('/api/auth/me').json()['user'])
        self.assertEqual(self.a.post('/api/auth/logout').status_code,200)
        self.assertIsNone(self.a.get('/api/auth/me').json()['user'])
        login=second.post('/api/auth/login',json={'username':self.user['username'],'password':PASSWORD+'new'},headers={'X-DQA-Intent':'1'})
        self.assertEqual(login.status_code,200)
        with transaction(self.db) as connection:
            connection.execute('UPDATE metadata.account_sessions SET expires_at=NOW()-interval \'1 second\' WHERE user_id=%s',(self.user['user_id'],))
        self.assertEqual(second.get('/api/progress').status_code,401)
        accounts.reset_password(self.db,self.user['username'],PASSWORD+'reset')
        self.assertEqual(second.post('/api/auth/login',json={'username':self.user['username'],'password':PASSWORD+'new'},headers={'X-DQA-Intent':'1'}).status_code,401)
        self.assertEqual(second.post('/api/auth/login',json={'username':self.user['username'],'password':PASSWORD+'reset'},headers={'X-DQA-Intent':'1'}).status_code,200)
        with transaction(self.db) as connection:
            connection.execute('UPDATE metadata.accounts SET active=false WHERE user_id=%s',(self.user['user_id'],))
        self.assertEqual(second.get('/api/progress').status_code,401)

    def test_two_accounts_cannot_read_or_mutate_each_others_sessions(self):
        b,_=signed_client(self.db)
        sid=self.session(mode='SANDBOX',scenario='equal_count_swap')
        other=self.session(b)
        for path in (f'/api/sessions/{sid}',f'/api/sessions/{sid}/history/queries',f'/api/sessions/{sid}/history/submissions'):
            self.assertEqual(b.get(path).status_code,404)
        for suffix,body in (('query',{'sql':'SELECT 1'}),('submit',{'sql':'SELECT 0 AS violation_count','conclusion':'x'}),('hint',{}),('reveal',{}),('simulation',{'action':'RESET'})):
            self.assertEqual(b.post(f'/api/sessions/{sid}/{suffix}',json=body).status_code,404)
        self.assertEqual([s['session_id'] for s in b.get('/api/sessions').json()],[other])
        for query in ('SELECT * FROM metadata.accounts','SELECT * FROM metadata.account_sessions'):
            self.assertEqual(self.a.post(f'/api/sessions/{sid}/query',json={'sql':query}).json()['status'],'ERROR')
        self.assertEqual(self.a.get('/api/sessions/'+sid).json()['status'],'ACTIVE')
        self.assertEqual(len(self.a.get('/api/enrollments').json()),1)
        self.assertEqual(b.get('/api/progress').json()[0]['attempts'],1)
        self.assertEqual(self.a.post('/api/sessions',json={'lab_id':'lab_001_record_count','run_id':str(uuid4())}).status_code,409)

    def test_shared_baseline_read_only_and_private_pipeline_fault_isolation(self):
        b,_=signed_client(self.db)
        self.assertEqual(self.a.get('/api/runs/'+self.baseline).status_code,200)
        self.assertEqual(self.a.post('/api/runs/'+self.baseline+'/quality').status_code,409)
        self.assertEqual(self.a.post('/api/faults',json={'run_id':self.baseline,'scenario':'missing_order'}).status_code,409)
        own=self.a.post('/api/runs').json()['run_id']
        self.assertEqual(b.get('/api/runs/'+own).status_code,404)
        self.assertEqual(b.get('/api/runs/'+own+'/quality').status_code,404)
        self.assertEqual(b.post('/api/runs/'+own+'/quality').status_code,404)
        self.assertEqual(b.post('/api/faults',json={'run_id':own,'scenario':'missing_order'}).status_code,404)
        self.assertNotIn(own,[r['run_id'] for r in b.get('/api/runs').json()])
        self.assertEqual(self.a.post('/api/runs/'+own+'/quality').json()['status'],'PASS')
        fault=self.a.post('/api/faults',json={'run_id':own,'scenario':'missing_order'})
        self.assertEqual(fault.status_code,200,fault.text)
        fid=fault.json()['fault_run_id']
        for suffix in ('quality','reset'):
            self.assertEqual(b.post(f'/api/faults/{fid}/{suffix}').status_code,404)
        self.assertEqual(b.get('/api/faults').json(),[])
        self.assertEqual(self.a.post(f'/api/faults/{fid}/quality').json()['status'],'FAIL')
        self.assertEqual(self.a.post(f'/api/faults/{fid}/reset').status_code,200)
        self.assertEqual(self.a.post(f'/api/faults/{fid}/quality').status_code,409)
        self.assertEqual(self.a.post('/api/sessions',json={'lab_id':'lab_001_record_count','run_id':self.baseline}).status_code,201)
        self.assertEqual(b.post('/api/sessions',json={'lab_id':'lab_001_record_count','run_id':own}).status_code,409)

    def test_persistent_auth_rate_budget_and_window_reset(self):
        name='unknown_'+uuid4().hex[:12]
        client=TestClient(create_app(self.db))
        for _ in range(10):
            self.assertEqual(client.post('/api/auth/login',json={'username':name,'password':PASSWORD},headers={'X-DQA-Intent':'1'}).status_code,401)
        restarted=TestClient(create_app(self.db))
        result=restarted.post('/api/auth/login',json={'username':name,'password':PASSWORD},headers={'X-DQA-Intent':'1'})
        self.assertEqual(result.status_code,429);self.assertEqual(result.headers['retry-after'],'900')
        with transaction(self.db) as connection:
            connection.execute("UPDATE metadata.auth_budgets SET window_start=NOW()-interval '16 minutes'")
        self.assertEqual(restarted.post('/api/auth/login',json={'username':name,'password':PASSWORD},headers={'X-DQA-Intent':'1'}).status_code,401)

    def test_legacy_import_is_explicit_retains_history_and_is_idempotent(self):
        from pipeline.jobs.orders import run_orders_pipeline
        from backend.app.learning.service import start_session,query_session
        from faults.service import apply_fault
        run=run_orders_pipeline(self.db)
        old=start_session(self.db,pipeline_run_id=run.run_id)
        query_session(self.db,old['session_id'],'SELECT COUNT(*) FROM source_orders')
        fault=apply_fault(self.db,'wrong_net_amount',run.run_id)
        self.assertEqual(self.a.get('/api/sessions/'+str(old['session_id'])).status_code,404)
        preview=accounts.import_legacy(self.db,self.user['username'])
        self.assertEqual(preview['counts'],{'pipeline_runs':1,'lab_sessions':1,'fault_runs':1})
        self.assertEqual(self.a.get('/api/sessions').json(),[])
        done=accounts.import_legacy(self.db,self.user['username'],True)
        self.assertEqual(done['counts'],preview['counts'])
        preserved=self.a.get('/api/sessions/'+str(old['session_id'])).json()
        self.assertEqual(preserved['query_count'],1)
        self.assertEqual(preserved['queries'][0]['result']['rows'],[['1000']])
        self.assertEqual(self.a.get('/api/runs/'+str(run.run_id)).status_code,200)
        self.assertIn(str(fault.fault_run_id),[f['fault_run_id'] for f in self.a.get('/api/faults').json()])
        self.assertEqual(accounts.import_legacy(self.db,self.user['username'],True)['counts'],{'pipeline_runs':0,'lab_sessions':0,'fault_runs':0})
        with connect(self.db) as connection:
            self.assertIsNone(connection.execute('SELECT owner_id FROM metadata.pipeline_runs WHERE run_id=%s',(self.baseline,)).fetchone()[0])
        self.assertEqual(self.a.post(f'/api/faults/{fault.fault_run_id}/reset').status_code,200)

    def test_spa_reload_routes_do_not_swallow_missing_assets_or_api(self):
        for path in ('/courses','/courses/sql-data-qa','/subjects/fabric','/login','/signup','/my-learning','/account','/courses/sql-data-qa/lessons/lab_001_record_count','/learn/lab_001_record_count'):
            response=self.a.get(path)
            self.assertEqual(response.status_code,200,path)
            self.assertIn('<div id="root"></div>',response.text)
        for path in ('/api/missing','/assets/missing.js','/random'):
            self.assertEqual(self.a.get(path).status_code,404,path)
