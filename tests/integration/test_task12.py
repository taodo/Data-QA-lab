"""Real PostgreSQL independent fixtures, ownership and portable foundation evidence."""
import json
import os
import unittest
from backend.app.learning import foundations as f,service
from backend.app.learning.profiles import PROFILES
from backend.app.learning.sql_runtime import initialize_sql_security,run_sql
from backend.app.learning.contracts import violation_count
from backend.app.persistence.database import initialize_database,connect
from tests.auth_helpers import signed_client

DB=os.getenv('DATA_QA_TEST_DATABASE_URL')


@unittest.skipUnless(DB,'Dedicated PostgreSQL test database required')
class Task12IntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from pipeline.source.seed import seed_source
        from pipeline.jobs.orders import run_orders_pipeline
        initialize_database(DB);initialize_sql_security(DB);seed_source(DB,20)
        cls.run_id=run_orders_pipeline(DB).run_id
        with connect(DB) as c:
            c.execute('UPDATE metadata.pipeline_runs SET is_shared=true WHERE run_id=%s',(cls.run_id,))
            c.execute('DELETE FROM metadata.auth_budgets')
        cls.a,cls.owner=signed_client(DB);cls.b,_=signed_client(DB)

    def start(self,key,scenario='clean',mode='SANDBOX'):
        return service.start_session(DB,key,self.run_id,mode,scenario if mode=='SANDBOX' else None,self.owner['user_id'])

    def schema(self,sid):
        with connect(DB) as c:return c.execute('SELECT snapshot_schema FROM metadata.lab_sessions WHERE session_id=%s',(sid,)).fetchone()[0]

    def test_independent_clean_fault_alternate_expectations_and_hardcoded_rejection(self):
        for key in f.IDS:
            sid=self.start(key)['session_id'];schema=self.schema(sid)
            for variant in PROFILES[key].variants:
                with self.subTest(key=key,variant=variant):
                    result=run_sql(DB,schema,f.SOLUTIONS[key],variant)
                    self.assertEqual(result.status,'SUCCESS',result)
                    self.assertEqual(violation_count(result),f.expected_count(variant))
            bad=service.submit_solution(DB,sid,'SELECT 0 AS violation_count','Not enough to return zero.')
            self.assertEqual(bad['status'],'FAIL')
            good=service.submit_solution(DB,sid,f.SOLUTIONS[key],'Compared independent expected keys and exact values.')
            self.assertEqual(good['status'],'PASS',good)
            history=service.inspect_session(DB,sid)
            self.assertEqual(history['submissions'][-1]['conclusion'],'Compared independent expected keys and exact values.')
            self.assertEqual(history['status'],'COMPLETED')

    def test_fault_round_trips_reset_other_session_local_revision_and_immutable_truth(self):
        for key in f.IDS:
            sid=self.start(key,f.SCENARIOS[key][0])['session_id']
            result=service.query_session(DB,sid,f.SOLUTIONS[key])
            before=service.inspect_session(DB,sid)['cloud_evidence']
            exported=service.export_cloud_evidence(DB,sid)
            service.simulate_session(DB,sid,'RESET')
            self.assertEqual(service.inspect_session(DB,sid)['cloud_evidence']['quality_status'],'NOT_RUN')
            for target in (sid,self.start(key)['session_id']):
                imported=service.import_cloud_evidence(DB,target,**exported)['cloud_evidence']
                self.assertEqual(imported['quality_status'],'NOT_RUN')
                self.assertEqual(imported['contract_id'],before['contract_id'])
                self.assertEqual(service.query_session(DB,target,f.SOLUTIONS[key])['rows'],result['rows'])
                self.assertEqual(service.inspect_session(DB,target)['cloud_evidence']['quality_status'],before['quality_status'])
            payload=json.loads(exported['content'])
            truth=next(t for t in f.DATASETS[key] if t in f.TRUTH)
            payload['datasets'][truth]=[]
            response=self.a.post('/api/sessions/'+str(sid)+'/evidence-import',json={**exported,'content':json.dumps(payload)})
            self.assertEqual(response.status_code,422,response.text)
            self.assertEqual(self.b.get('/api/sessions/'+str(sid)+'/evidence-export').status_code,404)

    def test_versions_replay_future_provider_and_unknown_context(self):
        key=f.IDS[1];sid=self.start(key)['session_id']
        for _ in range(21):service.simulate_session(DB,sid,'REPLAY')
        exported=service.export_cloud_evidence(DB,sid)
        data=json.loads(exported['content']);self.assertEqual(len(data['runs']),22)
        self.assertEqual(len(data['datasets']['db_after']),4)
        for row in data['runs']:row['ended_at']='2099-01-01T00:00:00Z'
        service.import_cloud_evidence(DB,sid,exported['filename'],'json',json.dumps(data))
        self.assertEqual(service.query_session(DB,sid,f.SOLUTIONS[key])['rows'],(('0',),))
        self.assertEqual(service.inspect_session(DB,sid)['cloud_evidence']['quality_status'],'PASS')
        data['as_of']=None;data['batch_no']=None
        service.import_cloud_evidence(DB,sid,exported['filename'],'json',json.dumps(data))
        service.query_session(DB,sid,f.SOLUTIONS[key])
        self.assertEqual(service.inspect_session(DB,sid)['cloud_evidence']['quality_status'],'NOT_VERIFIED')

    def test_access_execution_incomplete_evidence_not_data_defects_and_restricted_sql(self):
        for scenario,execution,status in (('clean','SUCCESS','OBSERVED'),('f_access_denied','FAILED','ACCESS_ERROR'),
                ('f_access_identity','UNKNOWN','INCOMPLETE'),('f_access_scope','UNKNOWN','INCOMPLETE'),
                ('f_access_missing','UNKNOWN','INCOMPLETE'),('f_access_future','UNKNOWN','INCOMPLETE')):
            sid=self.start(f.IDS[5],scenario)['session_id']
            service.query_session(DB,sid,f.SOLUTIONS[f.IDS[5]])
            state=service.inspect_session(DB,sid)['cloud_evidence']
            self.assertEqual((state['execution_status'],state['access_status']),(execution,status))
            self.assertEqual(state['quality_status'],'PASS' if scenario=='clean' else 'NOT_VERIFIED')
            error=service.query_session(DB,sid,'SELECT * FROM metadata.accounts')
            self.assertEqual(error['status'],'ERROR')
            self.assertEqual(service.inspect_session(DB,sid)['cloud_evidence']['quality_status'],'ERROR')
        for language in ('ENG','VIE'):
            key=f.IDS[4];sid=self.start(key)['session_id'];exported=service.export_cloud_evidence(DB,sid)
            before=service.inspect_session(DB,sid)['cloud_evidence']['mutation_revision']
            data=json.loads(exported['content']);data['datasets']['az_files'][0]['observed_at']='9999-12-31T23:59:59-23:59'
            response=self.a.post('/api/sessions/'+str(sid)+'/evidence-import?language='+language,json={**exported,'content':json.dumps(data)})
            self.assertEqual(response.status_code,422,response.text)
            self.assertEqual(service.inspect_session(DB,sid)['cloud_evidence']['mutation_revision'],before)
