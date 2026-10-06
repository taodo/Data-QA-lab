"""Real restricted SQL, independent cloud fixtures, bounded imports and ownership."""
import json
import os
from pathlib import Path
import unittest
from backend.app.learning import cloud, service
from backend.app.learning.sql_runtime import run_sql, initialize_sql_security
from backend.app.learning.contracts import violation_count, QueryLimits
from backend.app.persistence.database import connect, initialize_database
from tests.auth_helpers import signed_client

DB=os.getenv('DATA_QA_TEST_DATABASE_URL')
ROOT=Path(__file__).resolve().parents[2]


@unittest.skipUnless(DB,'Dedicated PostgreSQL test database required')
class CloudIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from pipeline.source.seed import seed_source
        from pipeline.jobs.orders import run_orders_pipeline
        initialize_database(DB);initialize_sql_security(DB);seed_source(DB,20)
        cls.baseline=run_orders_pipeline(DB).run_id
        with connect(DB) as c:
            c.execute('UPDATE metadata.pipeline_runs SET is_shared=true WHERE run_id=%s',(cls.baseline,))
            c.execute('DELETE FROM metadata.auth_budgets')
        cls.a,cls.owner=signed_client(DB);cls.b,_=signed_client(DB)

    def session(self,key,scenario='clean',mode='SANDBOX'):
        return service.start_session(DB,key,self.baseline,mode,scenario if mode=='SANDBOX' else None,self.owner['user_id'])

    def schema(self,sid):
        with connect(DB) as c:return c.execute('SELECT snapshot_schema FROM metadata.lab_sessions WHERE session_id=%s',(sid,)).fetchone()[0]

    def check(self, sid, key):
        result = service.query_session(DB, sid, cloud.SOLUTIONS[key])
        self.assertEqual(result['status'], 'SUCCESS', result)
        return result['rows'], service.inspect_session(DB, sid)['cloud_evidence']['quality_status']

    def test_watermark_and_recovery_round_trip_keep_batch_and_checkpoint_context(self):
        for batch in range(4):
            origin = self.session(cloud.IDS[4]); sid = origin['session_id']
            service.simulate_session(DB, sid, 'RESET')
            for _ in range(batch):
                service.simulate_session(DB, sid, 'NEXT')
            before = self.check(sid, cloud.IDS[4])
            exported = service.export_cloud_evidence(DB, sid)
            self.assertEqual(json.loads(exported['content'])['batch_no'], batch)
            service.simulate_session(DB, sid, 'RESET')
            for destination in (sid, self.session(cloud.IDS[4])['session_id']):
                restored = service.import_cloud_evidence(DB, destination, **exported)['cloud_evidence']
                self.assertEqual(restored['batch_no'], batch)
                self.assertEqual(self.check(destination, cloud.IDS[4]), before)
        # Preserve faulty snapshot meaning too, not only a clean PASS.
        for key, scenario in ((cloud.IDS[4], 'cloud_skip_late'), (cloud.IDS[5], 'cloud_checkpoint')):
            sid = self.session(key, scenario)['session_id']
            before = self.check(sid, key)
            self.assertEqual(before, ((('1',),), 'FAIL'))
            exported = service.export_cloud_evidence(DB, sid)
            service.simulate_session(DB, sid, 'RESET')
            for destination in (sid, self.session(key)['session_id']):
                service.import_cloud_evidence(DB, destination, **exported)
                self.assertEqual(self.check(destination, key), before)
        sid = self.session(cloud.IDS[5], 'cloud_failed_dependency')['session_id']
        service.simulate_session(DB, sid, 'RECOVER')
        exported = service.export_cloud_evidence(DB, sid)
        destination = self.session(cloud.IDS[5])['session_id']
        service.import_cloud_evidence(DB, destination, **exported)
        self.assertEqual(self.check(destination, cloud.IDS[5]), ((('0',),), 'PASS'))
        # Old JSON and CSV cannot borrow a receiver's selected batch/as-of.
        legacy = json.loads(exported['content']); legacy.pop('batch_no'); legacy.pop('steps')
        service.import_cloud_evidence(DB, destination, 'legacy.json', 'json', json.dumps(legacy))
        evidence = service.inspect_session(DB, destination)['cloud_evidence']
        self.assertIsNone(evidence['batch_no']); self.assertEqual(evidence['evidence_status'], 'NOT_VERIFIED')
        csv = (ROOT/'examples/cloud-snapshots-v1.csv').read_text()
        service.import_cloud_evidence(DB, destination, 'data.csv', 'csv', csv)
        evidence = service.inspect_session(DB, destination)['cloud_evidence']
        self.assertIsNone(evidence['batch_no']); self.assertIsNone(evidence['as_of'])
        self.assertEqual(self.check(destination, cloud.IDS[5])[1], 'NOT_VERIFIED')

    def test_export_after_many_replays_includes_every_referenced_run_and_is_importable(self):
        sid = self.session(cloud.IDS[4])['session_id']
        service.simulate_session(DB, sid, 'RESET')
        for _ in range(2): service.simulate_session(DB, sid, 'NEXT')
        destination = self.session(cloud.IDS[4])['session_id']
        for replay in range(1, 99):
            service.simulate_session(DB, sid, 'REPLAY')
            if replay not in (21, 98): continue
            path = '/api/sessions/'+str(sid)+'/evidence-export?language=ENG'
            self.assertEqual(self.b.get(path).status_code, 404)
            response = self.a.get(path)
            self.assertEqual(response.status_code, 200, response.text)
            exported = response.json(); data = json.loads(exported['content'])
            run_ids = {r['run_id'] for r in data['runs']}
            self.assertEqual(len(run_ids), replay+3)
            references = {r['run_id'] for rows in data['datasets'].values() for r in rows}
            references.update(r['run_id'] for name in ('activities','manifest','references','steps') for r in data[name])
            self.assertTrue(references <= run_ids)
            self.assertIn('run-1', run_ids)
            imported = self.a.post('/api/sessions/'+str(destination)+'/evidence-import', json=exported)
            self.assertEqual(imported.status_code, 200, imported.text)
            self.assertEqual(self.check(destination, cloud.IDS[4]), ((('0',),), 'PASS'))
        self.assertEqual(len(data['runs']), cloud.contracts.MAX_RUNS)
        self.assertEqual(len(data['steps']), cloud.contracts.MAX_STEPS)

    def test_provider_future_clock_does_not_hide_new_qa_or_reuse_old_checks(self):
        sid = self.session(cloud.IDS[0])['session_id']
        exported = service.export_cloud_evidence(DB, sid)
        data = json.loads(exported['content'])
        for run in data['runs']:
            run['started_at'] = '2099-01-01T00:00:00Z'
            run['ended_at'] = '2099-01-01T01:00:00Z'
        service.import_cloud_evidence(DB, sid, 'future.json', 'json', json.dumps(data))
        self.assertEqual(self.check(sid, cloud.IDS[0])[1], 'PASS')
        before = service.inspect_session(DB, sid)['cloud_evidence']['mutation_revision']
        service.import_cloud_evidence(DB, sid, 'future.json', 'json', json.dumps(data))
        evidence = service.inspect_session(DB, sid)['cloud_evidence']
        self.assertNotEqual(evidence['mutation_revision'], before)
        self.assertEqual(evidence['quality_status'], 'NOT_RUN')
        self.assertEqual(self.check(sid, cloud.IDS[0])[1], 'PASS')
        service.simulate_session(DB, sid, 'RESET')
        self.assertEqual(service.inspect_session(DB, sid)['cloud_evidence']['quality_status'], 'NOT_RUN')
        self.assertEqual(self.check(sid, cloud.IDS[0])[1], 'PASS')
        service.simulate_session(DB, sid, 'RUN')
        self.assertEqual(service.inspect_session(DB, sid)['cloud_evidence']['quality_status'], 'NOT_RUN')
        self.assertEqual(self.check(sid, cloud.IDS[0])[1], 'PASS')

    def test_timestamp_overflow_api_is_bilingual_atomic_validation_error(self):
        sid = self.session(cloud.IDS[0])['session_id']
        before = service.inspect_session(DB, sid)['cloud_evidence']
        sample = json.loads((ROOT/'examples/cloud-evidence-v1.json').read_text())
        for language, expected in (('ENG','Invalid evidence timestamp'), ('VIE','Timestamp evidence không hợp lệ.')):
            for timestamp in ('0001-01-01T00:00:00+23:59','9999-12-31T23:59:59-23:59'):
                for field in ('as_of','started_at','updated_at','snapshot_at','observed_at'):
                    data = json.loads(json.dumps(sample))
                    row = data if field=='as_of' else data['runs'][0] if field=='started_at' else data['datasets']['source'][0] if field=='updated_at' else data['manifest'][0] if field=='snapshot_at' else data['references'][0]
                    row[field] = timestamp
                    response = self.a.post('/api/sessions/'+str(sid)+'/evidence-import?language='+language,
                        json={'filename':'overflow.json','file_format':'json','content':json.dumps(data)})
                    self.assertEqual(response.status_code, 422, response.text)
                    self.assertEqual(response.json()['error'], {'code':'EVIDENCE_INVALID','detail':expected})
                    self.assertEqual(service.inspect_session(DB, sid)['cloud_evidence'], before)

    def test_independent_counts_all_clean_and_fault_fixtures(self):
        counts={'cloud_orphan_run':1,'cloud_dependency_missing':1,'cloud_unknown_run':2,
                'cloud_schema_type':1,'cloud_schema_missing':1,'cloud_schema_extra':1,
                'cloud_layer_swap':2,'cloud_layer_amount':1,'cloud_layer_duplicate':1,
                'cloud_copy_swap':2,'cloud_copy_missing':2,'cloud_copy_metrics':1,'cloud_copy_unknown':1,
                'cloud_skip_late':1,'cloud_replay_duplicate':1,'cloud_boundary_skip':1,
                'cloud_failed_dependency':3,'cloud_partial_publish':1,'cloud_checkpoint':1,
                'cloud_partition_missing':1,'cloud_partition_extra':1,'cloud_file_duplicate':2,
                'cloud_reference_stale':1,'cloud_reference_missing':1,'cloud_reference_null':1,'cloud_reference_future':1}
        for key in cloud.IDS:
            session=self.session(key);schema=self.schema(session['session_id'])
            for variant in ('cloud_clean','cloud_shifted','cloud_zero','cloud_sla_boundary',*cloud.SCENARIOS[key],*(cloud.SHIFTED_PREFIX+v for v in cloud.SCENARIOS[key])):
                with self.subTest(key=key,variant=variant):
                    result=run_sql(DB,schema,cloud.SOLUTIONS[key],variant)
                    self.assertEqual(result.status,'SUCCESS',result)
                    self.assertEqual(violation_count(result),counts.get(variant.removeprefix(cloud.SHIFTED_PREFIX),0))
                    self.assertEqual(cloud.expected_count(variant),counts.get(variant.removeprefix(cloud.SHIFTED_PREFIX),0))

    def test_submission_accepts_real_checks_rejects_constants_and_retains_workspace(self):
        for key in cloud.IDS:
            s=self.session(key,cloud.SCENARIOS[key][0]);sid=s['session_id']
            before=service.inspect_session(DB,sid)['cloud_evidence']
            self.assertEqual(service.submit_solution(DB,sid,'SELECT 0 AS violation_count','Constant')['status'],'FAIL')
            self.assertEqual(service.submit_solution(DB,sid,'SELECT nope FROM cloud_target','Syntax')['status'],'ERROR')
            self.assertEqual(service.submit_solution(DB,sid,cloud.SOLUTIONS[key],'Actual evidence')['status'],'PASS')
            after=service.inspect_session(DB,sid)['cloud_evidence']
            self.assertEqual(before,after)

    def test_replay_late_arrival_boundary_and_recovery_are_persisted(self):
        s=self.session(cloud.IDS[4]);sid=s['session_id']
        service.simulate_session(DB,sid,'RESET')
        first=service.simulate_session(DB,sid,'NEXT')['cloud_evidence']
        self.assertEqual(first['batch_no'],1)
        second=service.simulate_session(DB,sid,'NEXT')['cloud_evidence']
        self.assertEqual([r['amount'] for r in second['datasets']['target'][:2]],[cloud.Decimal('9.99'),cloud.Decimal('7.77')])
        replay=service.simulate_session(DB,sid,'REPLAY')['cloud_evidence']
        self.assertEqual(len(replay['datasets']['target']),4)
        third=service.simulate_session(DB,sid,'NEXT')['cloud_evidence']
        self.assertNotIn(cloud.Decimal('8.88'),[r['amount'] for r in third['datasets']['target']])
        self.assertEqual(violation_count(run_sql(DB,self.schema(sid),cloud.SOLUTIONS[cloud.IDS[4]])),0)
        for scenario in ('cloud_failed_dependency','cloud_partial_publish'):
            failed=self.session(cloud.IDS[5],scenario);sid=failed['session_id']
            for _ in range(2):
                recovered=service.simulate_session(DB,sid,'RECOVER')['cloud_evidence']
                self.assertEqual(recovered['execution_status'],'SUCCESS')
                self.assertEqual(len(recovered['datasets']['target']),4)
                self.assertEqual(violation_count(run_sql(DB,self.schema(sid),cloud.SOLUTIONS[cloud.IDS[5]])),0)
            self.assertGreaterEqual(len(recovered['runs']),3)

    def test_import_provenance_exact_data_retention_unknown_and_atomic_failure(self):
        s=self.session(cloud.IDS[0]);sid=s['session_id']
        sample=(ROOT/'examples/cloud-evidence-v1.json').read_text()
        service.query_session(DB,sid,'SELECT 0 AS violation_count')
        imported=service.import_cloud_evidence(DB,sid,'evidence.json','json',sample)['cloud_evidence']
        self.assertEqual(imported['provenance'],'IMPORTED');self.assertEqual(imported['quality_status'],'NOT_RUN')
        self.assertEqual(imported['runs'][0]['raw_evidence']['execution_status'],'Succeeded')
        self.assertEqual(imported['datasets']['target'][0]['amount'],cloud.Decimal('1.01'))
        with self.assertRaises(ValueError):service.import_cloud_evidence(DB,sid,'bad.json','json','{"version":99}')
        self.assertEqual(service.inspect_session(DB,sid)['cloud_evidence'],imported)
        csv=(ROOT/'examples/cloud-snapshots-v1.csv').read_text()
        service.import_cloud_evidence(DB,sid,'data.csv','csv',csv)
        minimal=json.dumps({'version':1,'provider':'Fabric','as_of':cloud.AS_OF.isoformat(),'runs':[{'run_id':'r'}]})
        unknown=service.import_cloud_evidence(DB,sid,'unknown.json','json',minimal)['cloud_evidence']
        self.assertEqual(unknown['execution_status'],'UNKNOWN');self.assertEqual(unknown['evidence_status'],'NOT_VERIFIED')
        self.assertEqual(unknown['imports'][-1]['run_ids'],['r'])
        service.query_session(DB,sid,'SELECT 0 AS violation_count')
        self.assertEqual(service.inspect_session(DB,sid)['cloud_evidence']['quality_status'],'NOT_VERIFIED')
        reset=service.simulate_session(DB,sid,'RESET')['cloud_evidence']
        self.assertEqual(len(reset['imports']),3);self.assertEqual(reset['provenance'],'SIMULATED')
        with connect(DB) as c:
            stored=cloud.execute(c,self.schema(sid),'SELECT raw_content,sha256 FROM {s}.cloud_imports ORDER BY captured_at').fetchall()
            self.assertEqual(stored[0][0],sample)

    def test_import_limit_ownership_csrf_closed_sessions_and_migration(self):
        s=self.session(cloud.IDS[0]);sid=str(s['session_id']);path='/api/sessions/'+sid
        payload={'filename':'evidence.json','file_format':'json','content':(ROOT/'examples/cloud-evidence-v1.json').read_text()}
        self.assertEqual(self.b.post(path+'/evidence-import',json=payload).status_code,404)
        self.assertEqual(self.a.post(path+'/evidence-import',json=payload,headers={'X-CSRF-Token':''}).status_code,403)
        self.assertEqual(self.a.post(path+'/evidence-import',json={**payload,'path':'D:/other'}).status_code,422)
        for _ in range(8):self.assertEqual(self.a.post(path+'/evidence-import',json=payload).status_code,200)
        self.assertEqual(self.a.post(path+'/evidence-import',json=payload).status_code,422)
        initialize_database(DB)
        self.assertEqual(len(self.a.get(path).json()['cloud_evidence']['imports']),8)
        self.assertEqual(self.a.post(path+'/reveal',json={}).status_code,200)
        self.assertEqual(self.a.post(path+'/evidence-import',json=payload).status_code,409)
        challenge=self.session(cloud.IDS[0],mode='CHALLENGE');path='/api/sessions/'+str(challenge['session_id'])
        self.assertNotIn('solution_sql',challenge);self.assertNotIn('scenario_id',challenge)
        self.assertEqual(self.a.post(path+'/evidence-import',json=payload).status_code,409)
        self.assertEqual(self.a.post(path+'/simulation',json={'action':'RUN'}).status_code,409)

    def test_sql_remains_select_only_bounded_and_isolated(self):
        first=self.session(cloud.IDS[0]);second=self.session(cloud.IDS[1])
        schema=self.schema(first['session_id']);other=self.schema(second['session_id'])
        for query in ('DELETE FROM cloud_target','CREATE TABLE evil(x int)',f'SELECT * FROM {other}.cloud_source','SELECT * FROM metadata.accounts'):
            self.assertEqual(run_sql(DB,schema,query).status,'ERROR',query)
        result=run_sql(DB,schema,'SELECT generate_series(1,200) AS x')
        self.assertEqual(len(result.rows),100);self.assertTrue(result.truncated)
        timed=run_sql(DB,schema,'SELECT pg_sleep(1)',limits=QueryLimits(timeout_ms=100,watchdog_ms=250))
        self.assertEqual(timed.status,'ERROR')
        self.assertEqual(len(service.inspect_session(DB,first['session_id'])['cloud_evidence']['datasets']['target']),4)
