"""Deterministic protocol/API failure tests. No credentials or live API calls."""
import copy
import json
import unittest
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError, URLError

from scripts import github_coordination as c

NOW = datetime(2026, 10, 12, 12, tzinfo=UTC)
STAMP = '2026-10-12T11:59:00Z'
ROOT = Path(__file__).resolve().parents[2]


def event(body='/coord request target=banking type=review', *, issue=37, comment_id=100, login='alice', user_id=123):
    user = {'id':user_id, 'login':login, 'type':'User'}
    return {'action':'created', 'repository':{'id':c.REPOSITORY_ID,'full_name':c.REPOSITORY},
            'issue':{'number':issue,'state':'open','locked':False}, 'sender':user.copy(),
            'comment':{'id':comment_id,'body':body,'user':user,'created_at':STAMP,'updated_at':STAMP,
                       'issue_url':f'https://api.github.com/repos/{c.REPOSITORY}/issues/{issue}'}}


class FakeGitHub(c.GitHub):
    """Exercise the actual I/O adapter methods against a deterministic REST store."""
    def __init__(self):
        self.rows = {}
        self.runs = []
        self.calls = []
        self.writes = []
        self.fail = None
        self.after_write_loss = False
        self.hook = None
        self.issue_state = 'open'
        self.pr_issue = False
        self.role = 'write'
        self.live_repo = {'id':c.REPOSITORY_ID,'full_name':c.REPOSITORY,'default_branch':'main'}

    def add_event(self, value, run_id, attempt):
        self.rows.setdefault(value['comment']['id'], copy.deepcopy(value['comment']))
        self.runs.append({'id':run_id,'event':'issue_comment','path':c.WORKFLOW,
                          'display_title':f"C1 issue {value['issue']['number']} comment {value['comment']['id']}",
                          'run_attempt':attempt,'repository':{'id':c.REPOSITORY_ID},'conclusion':None})

    def call(self, method, suffix='', payload=None, query=None):
        self.calls.append((method,suffix,copy.deepcopy(payload),query))
        if self.hook:
            self.hook(method,suffix,payload,query)
        if self.fail == (method,suffix):
            raise c.ApiFailure('READ_FAILED' if method=='GET' else 'WRITE_UNCERTAIN_DO_NOT_RETRY')
        if method=='GET':
            if suffix=='':return copy.deepcopy(self.live_repo)
            if suffix in ('/issues/37','/issues/38'):
                result={'number':int(suffix.rsplit('/',1)[1]),'state':self.issue_state,'locked':False}
                if self.pr_issue:result['pull_request']={}
                return result
            if suffix.startswith('/issues/comments/'):
                row=self.rows.get(int(suffix.rsplit('/',1)[1]))
                if row is None:raise c.ApiFailure('READ_FAILED')
                return copy.deepcopy(row)
            if suffix.startswith('/collaborators/'):
                login=suffix.split('/')[2]
                user=next(row['user'] for row in self.rows.values() if row['user']['login']==login)
                return {'permission':self.role,'user':user.copy()}
            if suffix.endswith('/comments'):
                issue=int(suffix.split('/')[2]);rows=[row for row in self.rows.values()
                    if row['issue_url'].endswith('/'+str(issue))]
                offset=(query['page']-1)*100
                return copy.deepcopy(rows[offset:offset+100])
            if suffix.startswith('/actions/runs/'):
                return copy.deepcopy(next(r for r in self.runs if r['id']==int(suffix.rsplit('/',1)[1])))
            if suffix=='/actions/workflows/coordination.yml/runs':
                offset=(query['page']-1)*100
                return {'workflow_runs':copy.deepcopy(self.runs[offset:offset+100])}
        if method=='POST':
            issue=int(suffix.split('/')[2]);row_id=10000+len(self.writes)
            self.rows[row_id]={'id':row_id,'body':payload['body'],'user':{'id':c.BOT[1],'login':c.BOT[0],'type':'Bot'},
                               'issue_url':f'https://api.github.com/repos/{c.REPOSITORY}/issues/{issue}',
                               'created_at':STAMP,'updated_at':STAMP}
        elif method=='PATCH':
            row_id=int(suffix.rsplit('/',1)[1]);self.rows[row_id]['body']=payload['body']
        else:raise AssertionError((method,suffix))
        self.writes.append((method,suffix,copy.deepcopy(payload)))
        if self.after_write_loss:raise c.ApiFailure('WRITE_UNCERTAIN_DO_NOT_RETRY')
        return copy.deepcopy(self.rows[row_id])

    def ledger(self):
        return c.read_ledger(next(row for row in reversed(list(self.rows.values())) if row['user']['type']=='Bot'))


class CoordinationTests(unittest.TestCase):
    def setUp(self):
        self.api=FakeGitHub();self.next_run=500;self.next_comment=200

    def execute(self, value, *, attempt=1, ref='refs/heads/main', now=NOW):
        self.next_run+=1;run_id=self.next_run
        self.api.add_event(value,run_id,attempt)
        try:
            result=c.coordinate(self.api,value,now=now,run_id=run_id,run_attempt=attempt,
                                event_name='issue_comment',github_ref=ref)
            self.api.runs[-1]['conclusion']='success'
            return result
        except c.Rejected:
            # CLI treats explicit NO_WRITE rejection as a successful safe no-op.
            self.api.runs[-1]['conclusion']='success'
            raise
        except c.ApiFailure:
            self.api.runs[-1]['conclusion']='failure'
            raise

    def start(self,issue=37):
        value=event(f'/coord request target={c.TARGETS[issue][0]} type=review',issue=issue)
        self.assertEqual(self.execute(value),'ACKNOWLEDGED')
        return value

    def update(self,verb,*,outcome='review-posted',decision='acknowledged',comment_id=None):
        ledger=self.api.ledger();body=f"/coord {verb} id={ledger['correlation']} revision={ledger['revision']}"
        if verb=='review':body+=' outcome='+outcome
        if verb=='close':body+=' decision='+decision
        self.next_comment+=1
        return self.execute(event(body,issue=ledger['issue'],comment_id=comment_id or self.next_comment))

    def test_banking_and_automation_acknowledge_correct_same_issue_once(self):
        for issue in (37,38):
            with self.subTest(issue=issue):
                self.api=FakeGitHub();original=self.start(issue)
                ledger=self.api.ledger();self.assertEqual(ledger['state'],'AWAITING_REVIEW')
                self.assertEqual(ledger['target'],c.TARGETS[issue][0])
                self.assertEqual(ledger['correlation'],f'c1-{issue}-100')
                self.assertEqual(self.api.writes[0][1],f'/issues/{issue}/comments')
                self.assertIn(c.TARGETS[issue][1],self.api.writes[0][2]['body'])
                self.assertIn('No separate ChatGPT session',self.api.writes[0][2]['body'])
                self.assertEqual(self.execute(original),'DUPLICATE_NO_WRITE')
                self.assertEqual(len(self.api.writes),1)

    def test_explicit_full_lifecycle_updates_one_comment_without_closing_issue(self):
        self.start();self.update('review');self.update('handoff')
        self.assertEqual(self.api.ledger()['state'],'AWAITING_HUMAN_APPROVAL')
        self.api.role='admin';self.update('close')
        ledger=self.api.ledger();self.assertEqual(ledger['state'],'CLOSED')
        self.assertEqual(ledger['revision'],4)
        self.assertEqual([method for method,_,_ in self.api.writes],['POST','PATCH','PATCH','PATCH'])
        self.assertTrue(all('/issues/comments/' in suffix for method,suffix,_ in self.api.writes if method=='PATCH'))
        self.assertEqual(self.api.issue_state,'open')

    def test_ordinary_prose_and_quoted_or_fenced_commands_have_no_api_side_effects(self):
        for body in ('approved','APPROVE WITH NOTES','text\n/coord request target=banking type=review',
                     '> /coord request target=banking type=review',
                     '```text\n/coord request target=banking type=review\n```',
                     '    /coord request target=banking type=review','\n/coord request target=banking type=review'):
            with self.subTest(body=body):
                self.api=FakeGitHub()
                with self.assertRaises(c.Rejected):self.execute(event(body))
                self.assertEqual(self.api.calls,[])

    def test_grammar_case_order_unknown_target_injections_and_size(self):
        for body in ('/COORD request target=banking type=review','/coord request target=Banking type=review',
                     '/coord request type=review target=banking','/coord request target=unknown type=review',
                     '/coord request target=banking type=review; echo bad','/coord request target=$(whoami) type=review',
                     '/coord request target=banking type=review\nextra',
                     '/coord request target=banking type=review\n\n/coord close id=c1-37-100 revision=1 decision=cancelled',
                     '/coord request target=banking type=review'+'x'*c.MAX_BODY):
            with self.subTest(body=body[:70]):
                with self.assertRaises(c.Rejected):c.parse_command(body)
        self.assertEqual(c.parse_command('/coord request target=banking type=review\r\n\r\nHuman evidence'),c.Command('request',target='banking'))

    def test_event_allowlist_pr_closed_bot_sender_and_repo_spoofing(self):
        mutations=[lambda e:e['issue'].update(number=39), lambda e:e['issue'].update(number=True),
                   lambda e:e['issue'].update(pull_request={}), lambda e:e['issue'].update(state='closed'),
                   lambda e:e['issue'].update(locked=True),lambda e:e['repository'].update(full_name='taodo/MiniBanking'),
                   lambda e:e['repository'].update(id=1), lambda e:e['comment']['user'].update(type='Bot'),
                   lambda e:e['sender'].update(type='Bot'), lambda e:e['sender'].update(id=456),
                   lambda e:e.update(action='edited'),lambda e:e.update(action='deleted'),
                   lambda e:e['comment'].update(id=True),lambda e:e['comment'].update(updated_at='2026-10-12T12:00:00Z')]
        for change in mutations:
            with self.subTest(change=change):
                value=event();change(value);self.api=FakeGitHub()
                with self.assertRaises(c.Rejected):self.execute(value)
                self.assertEqual(self.api.calls,[])
        with self.assertRaises(c.Rejected):self.execute(event('/coord request target=automation type=review'))

    def test_malformed_payloads_fail_before_write(self):
        for value in (None,[],{}, {'action':'created'},event()|{'comment':None},event()|{'repository':[]},
                      event()|{'sender':{'id':123,'type':'User','login':True}}):
            with self.subTest(value=value):
                self.api=FakeGitHub()
                with self.assertRaises(c.Rejected):self.execute(value) if isinstance(value,dict) and value.get('comment') else c.validate_event(value,'issue_comment')
                self.assertEqual(self.api.writes,[])

    def test_fresh_permissions_not_author_association_or_username(self):
        for role in ('read','triage','none'):
            self.api=FakeGitHub();self.api.role=role;value=event();value['comment']['author_association']='OWNER'
            with self.assertRaisesRegex(c.Rejected,'AUTHOR_UNAUTHORIZED'):self.execute(value)
            self.assertEqual(self.api.writes,[])
        self.api=FakeGitHub()
        self.api.hook=lambda method,suffix,payload,query:self.api.rows[100]['user'].update(id=999) if suffix.startswith('/collaborators/') else None
        with self.assertRaisesRegex(c.Rejected,'AUTHOR_UNAUTHORIZED'):self.execute(event())
        self.assertEqual(self.api.writes,[])

    def test_live_issue_and_comment_recheck_closed_deleted_edited_spoofed(self):
        for scenario in ('closed','pr','missing','edited','other-issue'):
            with self.subTest(scenario=scenario):
                self.api=FakeGitHub();value=event();self.api.add_event(value,400,1)
                if scenario=='closed':self.api.issue_state='closed'
                elif scenario=='pr':self.api.pr_issue=True
                elif scenario=='missing':self.api.rows.pop(100)
                elif scenario=='edited':self.api.rows[100]['body']='changed'
                else:self.api.rows[100]['issue_url']='https://api.github.com/repos/taodo/MiniBanking/issues/37'
                with self.assertRaises((c.Rejected,c.ApiFailure)):
                    c.coordinate(self.api,value,now=NOW,run_id=400,run_attempt=1,event_name='issue_comment',github_ref='refs/heads/main')
                self.assertEqual(self.api.writes,[])

    def test_untrusted_execution_ref_and_stale_command(self):
        for ref in ('refs/pull/1/merge','refs/heads/feature/develop','refs/heads/attacker'):
            self.api=FakeGitHub()
            with self.assertRaisesRegex(c.Rejected,'UNTRUSTED_EXECUTION_REF'):self.execute(event(),ref=ref)
        self.api=FakeGitHub();value=event();value['comment']['created_at']=value['comment']['updated_at']='2026-10-10T11:59:00Z'
        with self.assertRaisesRegex(c.Rejected,'STALE_COMMAND'):self.execute(value)

    def test_one_active_request_and_terminal_cycle(self):
        self.start()
        with self.assertRaisesRegex(c.Rejected,'ACTIVE_REQUEST_EXISTS'):self.execute(event(comment_id=101))
        self.api.role='admin';self.update('close',decision='cancelled')
        self.assertEqual(self.execute(event(comment_id=102)),'ACKNOWLEDGED')
        self.assertEqual(sum(c.read_ledger(row)['state']!='CLOSED' for row in self.api.rows.values() if row['user']['type']=='Bot'),1)

    def test_review_verdict_requires_command_not_notes(self):
        self.start()
        with self.assertRaises(c.Rejected):self.execute(event('APPROVED: ready to merge',comment_id=101))
        body='/coord review id=c1-37-100 revision=1 outcome=needs-changes\n\nAPPROVED elsewhere is prose.'
        self.execute(event(body,comment_id=102));self.assertEqual(self.api.ledger()['state'],'NEEDS_CHANGES')

    def test_stale_revision_and_wrong_correlation(self):
        self.start();self.update('review')
        for body in ('/coord handoff id=c1-37-100 revision=1','/coord handoff id=c1-38-100 revision=2',
                     '/coord review id=c1-37-100 revision=2 outcome=blocked'):
            with self.assertRaises(c.Rejected):self.execute(event(body,comment_id=300))
        self.assertEqual(len(self.api.writes),2)

    def test_only_admin_closes_and_acknowledgment_requires_handoff(self):
        self.start()
        with self.assertRaisesRegex(c.Rejected,'TRANSITION_NOT_ALLOWED'):self.update('close')
        self.api.role='admin'
        with self.assertRaisesRegex(c.Rejected,'TRANSITION_NOT_ALLOWED'):self.update('close')
        self.update('review');self.update('handoff');self.api.role='write'
        with self.assertRaisesRegex(c.Rejected,'TRANSITION_NOT_ALLOWED'):self.update('close')

    def test_three_review_rounds_bounded_then_human_cancellation(self):
        self.start()
        for index in range(3):
            self.update('review',outcome='blocked')
            if index<2:self.update('resume')
        self.assertEqual(self.api.ledger()['review_rounds'],3)
        with self.assertRaisesRegex(c.Rejected,'TRANSITION_NOT_ALLOWED'):self.update('resume')
        self.api.role='admin';self.update('close',decision='cancelled')
        self.assertLessEqual(self.api.ledger()['revision'],c.MAX_REVISION)

    def test_human_forged_marker_and_bot_event_never_drive_state(self):
        self.start();body=next(row['body'] for row in self.api.rows.values() if row['user']['type']=='Bot')
        spoof=event(body,comment_id=999)['comment'];self.api.rows[999]=spoof
        self.assertIsNone(c.read_ledger(spoof));self.assertEqual(len(c.scan_ledgers(list(self.api.rows.values()),37)),1)
        bot=event('/coord request target=banking type=review',comment_id=10001)
        bot['comment']['user']={'id':c.BOT[1],'login':c.BOT[0],'type':'Bot'};bot['sender']=bot['comment']['user']
        with self.assertRaises(c.Rejected):self.execute(bot)
        self.assertEqual(len(self.api.writes),1)

    def test_malformed_or_duplicate_trusted_ledgers_fail_closed(self):
        self.start();bot=next(row for row in self.api.rows.values() if row['user']['type']=='Bot')
        bot['body']=c.MARKER+'{}\n```'
        with self.assertRaisesRegex(c.Rejected,'LEDGER_INVALID'):self.execute(event(comment_id=101))
        self.api=FakeGitHub();self.start();bot=next(row for row in self.api.rows.values() if row['user']['type']=='Bot')
        duplicate=copy.deepcopy(bot);duplicate['id']=99999;self.api.rows[99999]=duplicate
        with self.assertRaisesRegex(c.Rejected,'LEDGER_CONFLICT'):self.execute(event(comment_id=101))

    def test_missing_or_edited_accepted_source_allows_admin_cancel_only(self):
        for mode in ('missing','edited'):
            self.api=FakeGitHub();self.start()
            if mode=='missing':self.api.rows.pop(100)
            else:self.api.rows[100]['body']='edited review context'
            with self.assertRaisesRegex(c.Rejected,'PRIOR_SOURCE_CHANGED_CANCEL_ONLY'):self.update('review')
            self.api.role='admin';self.update('close',decision='cancelled')
            self.assertEqual(self.api.ledger()['state'],'CLOSED')

    def test_api_failures_before_write_and_ambiguous_create_are_not_retried(self):
        self.api.fail=('GET','/collaborators/alice/permission')
        with self.assertRaises(c.ApiFailure):self.execute(event())
        self.assertEqual(self.api.writes,[])
        self.api=FakeGitHub();self.api.after_write_loss=True;original=event()
        with self.assertRaisesRegex(c.ApiFailure,'WRITE_UNCERTAIN'):self.execute(original)
        self.assertEqual(len(self.api.writes),1)
        self.api.after_write_loss=False
        self.assertEqual(self.execute(original),'DUPLICATE_NO_WRITE')
        self.assertEqual(len(self.api.writes),1)

    def test_ambiguous_update_recovers_from_durable_processed_id(self):
        self.start();self.api.after_write_loss=True
        value=event('/coord review id=c1-37-100 revision=1 outcome=review-posted',comment_id=200)
        with self.assertRaises(c.ApiFailure):self.execute(value)
        self.assertEqual(self.api.ledger()['revision'],2)
        self.api.after_write_loss=False
        self.assertEqual(self.execute(value),'DUPLICATE_NO_WRITE')
        self.assertEqual(len(self.api.writes),2)

    def test_redelivery_without_receipt_rerun_and_unresolved_failure_block_writes(self):
        self.api.fail=('POST','/issues/37/comments');original=event()
        with self.assertRaises(c.ApiFailure):self.execute(original)
        self.api.fail=None
        with self.assertRaisesRegex(c.Rejected,'REPLAY_WITHOUT_RECEIPT'):self.execute(original,attempt=2)
        with self.assertRaisesRegex(c.Rejected,'PRIOR_DELIVERY_NO_WRITE'):self.execute(original)
        with self.assertRaisesRegex(c.Rejected,'PRIOR_DELIVERY_UNRESOLVED'):self.execute(event(comment_id=101))
        self.assertEqual(self.api.writes,[])

    def test_last_moment_source_and_ledger_races_are_rejected(self):
        self.start();reads=0
        def edit_source(method,suffix,payload,query):
            nonlocal reads
            if method=='GET' and suffix=='/issues/comments/200':
                reads+=1
                if reads==2:self.api.rows[200]['body']='changed after authorization'
        self.api.hook=edit_source
        with self.assertRaisesRegex(c.Rejected,'COMMENT_CHANGED'):self.update('review',comment_id=200)
        self.assertEqual(len(self.api.writes),1)
        self.api.hook=lambda method,suffix,payload,query:self.api.rows[10000].update(updated_at='2026-10-12T12:00:00Z') if suffix=='/issues/comments/10000' else None
        with self.assertRaisesRegex(c.Rejected,'CONCURRENT_LEDGER_CHANGE'):self.update('review',comment_id=201)
        self.assertEqual(len(self.api.writes),1)

    def test_request_and_scan_budgets_are_bounded(self):
        for index in range(c.MAX_REQUESTS):
            self.execute(event(comment_id=100+index));self.api.role='admin';self.update('close',decision='cancelled',comment_id=200+index)
        with self.assertRaisesRegex(c.Rejected,'REQUEST_BUDGET'):self.execute(event(comment_id=999))
        api=FakeGitHub();api.call=lambda *args,**kwargs:[{}]*100
        with self.assertRaisesRegex(c.Rejected,'COMMENT_SCAN_BUDGET'):api.comments(37)

    def test_run_identity_visibility_scan_budget_and_cross_issue_failures(self):
        self.api.add_event(event(),500,1)
        self.api.runs[0]['path']='.github/workflows/attacker.yml'
        with self.assertRaisesRegex(c.Rejected,'INVALID_EXECUTION_RUN'):self.api.check_delivery(37,100,500,1,set(),NOW)
        self.api.runs[0]['path']=c.WORKFLOW
        self.api.runs.append({'id':501,'display_title':'C1 issue 38 comment 9','conclusion':'failure'})
        self.api.check_delivery(37,100,500,1,set(),NOW)
        self.api.runs=self.api.runs[:1]
        original_call=self.api.call
        self.api.call=lambda method,suffix='',**kwargs: {'workflow_runs':[]} if suffix.endswith('/coordination.yml/runs') else original_call(method,suffix,**kwargs)
        with self.assertRaisesRegex(c.Rejected,'EXECUTION_RUN_NOT_VISIBLE'):self.api.check_delivery(37,100,500,1,set(),NOW)

    def test_boolean_ledger_revision_and_invalid_write_receipt_fail_closed(self):
        self.start();ledger=self.api.ledger();ledger['revision']=True
        bot=next(row for row in self.api.rows.values() if row['user']['type']=='Bot')
        bot['body']=c.render(ledger)
        with self.assertRaisesRegex(c.Rejected,'LEDGER_INVALID'):c.read_ledger(bot)
        for receipt in ({}, {'id':1,'body':'wrong','user':{'type':'User'}}, bot):
            with self.assertRaisesRegex(c.ApiFailure,'WRITE_UNCERTAIN'):c.GitHub.verify_write(receipt,bot['body'])

    def test_new_request_race_rechecks_durable_ledger_before_post(self):
        seen=0
        def competing_ack(method,suffix,payload,query):
            nonlocal seen
            if suffix=='/issues/37/comments' and method=='GET':
                seen+=1
                if seen==2:
                    original=event(comment_id=101)['comment'];self.api.rows[101]=original
                    entry={'comment_id':101,'actor_id':123,'actor_login':'alice','permission':'write',
                           'body_sha256':c.digest(original['body']),'line':original['body'],'created_at':STAMP}
                    ledger=c.advance(None,c.parse_command(original['body']),entry,37)
                    self.api.rows[99999]={'id':99999,'body':c.render(ledger),'user':{'id':c.BOT[1],'login':c.BOT[0],'type':'Bot'},
                                         'issue_url':f'https://api.github.com/repos/{c.REPOSITORY}/issues/37','updated_at':STAMP}
        self.api.hook=competing_ack
        with self.assertRaisesRegex(c.Rejected,'CONCURRENT_LEDGER_CHANGE'):self.execute(event())
        self.assertEqual(self.api.writes,[])

    def test_run_scan_cap_and_two_simultaneous_active_ledgers_are_rejected(self):
        self.api.add_event(event(),500,1);original_call=self.api.call
        self.api.call=lambda method,suffix='',**kwargs: {'workflow_runs':[self.api.runs[0]]*100} if suffix.endswith('/coordination.yml/runs') else original_call(method,suffix,**kwargs)
        with self.assertRaisesRegex(c.Rejected,'RUN_SCAN_BUDGET'):self.api.check_delivery(37,100,500,1,set(),NOW)
        self.api=FakeGitHub();self.start();first=next(row for row in self.api.rows.values() if row['user']['type']=='Bot')
        other=copy.deepcopy(first);other['id']=99999;ledger=c.read_ledger(other)
        ledger['events'][0]['comment_id']=101;ledger['request_comment_id']=101;ledger['correlation']='c1-37-101'
        other['body']=c.render(ledger)
        with self.assertRaisesRegex(c.Rejected,'LEDGER_CONFLICT'):c.scan_ledgers([first,other],37)


class AdapterAndWorkflowTests(unittest.TestCase):
    def test_activation_release_validation_is_scoped_to_exact_branches_and_files(self):
        workflow=c.decode_json((ROOT/c.WORKFLOW).read_text(encoding='utf-8'))
        self.assertEqual(workflow['on']['push'], {
            'branches':['main','feature/develop','feature/c1a-coordination-activation'],
            'paths':[c.WORKFLOW,'scripts/github_coordination.py',
                     'tests/unit/test_github_coordination.py','docs/CROSS_REPO_COORDINATION.md'],
        })
        self.assertEqual(workflow['jobs']['validate']['steps'][1], {
            'run':'python3 -m unittest tests.unit.test_github_coordination -v',
        })
        self.assertEqual(workflow['jobs']['coordinate']['if'].split(' && ')[0],
                         "github.event_name == 'issue_comment'")

    def test_rest_origin_headers_no_redirects_no_retry_and_redacted_errors(self):
        api=c.GitHub('test-token-never-print');requests=[]
        class Response:
            def __enter__(self):return self
            def __exit__(self,*args):pass
            def read(self,limit):return b'{"ok":true}'
        def open_request(request,timeout):requests.append((request,timeout));return Response()
        api.opener.open=open_request
        self.assertEqual(api.call('GET','/issues/37'),{'ok':True})
        self.assertEqual(requests[0][0].full_url,'https://api.github.com/repos/taodo/Data-QA-lab/issues/37')
        self.assertEqual(requests[0][1],10)
        self.assertIsNone(c.NoRedirect().redirect_request(None,None,302,'',{},'https://evil.test'))
        for suffix in ('https://evil.test','/../other?x=1','/issues/37\nInjected'):
            with self.assertRaises(c.ApiFailure):api.call('GET',suffix)
        for method,suffix in (('POST','/issues/39/comments'),('POST','/contents/main.py'),('PATCH','/issues/37')):
            with self.assertRaisesRegex(c.ApiFailure,'INVALID_MUTATION_PATH'):api.call(method,suffix,{'body':'test'})
        for failure in (HTTPError('url',429,'SECRET_BODY',{},None),URLError('SECRET_TOKEN')):
            api.opener.open=lambda *args,**kwargs:(_ for _ in ()).throw(failure)
            with self.assertRaisesRegex(c.ApiFailure,'WRITE_UNCERTAIN_DO_NOT_RETRY') as caught:api.call('POST','/issues/37/comments',{'body':'safe'})
            self.assertNotIn('SECRET',str(caught.exception))

    def test_strict_json_duplicate_keys_and_response_limits(self):
        with self.assertRaises(ValueError):c.decode_json('{"id":1,"id":2}')
        api=c.GitHub('fake')
        class Response:
            def __enter__(self):return self
            def __exit__(self,*args):pass
            def read(self,limit):return b'x'*limit
        api.opener.open=lambda *args,**kwargs:Response()
        with self.assertRaisesRegex(c.ApiFailure,'READ_FAILED'):api.call('GET')

    def test_workflow_security_contract_and_existing_ci_untouched(self):
        text=(ROOT/c.WORKFLOW).read_text(encoding='utf-8');workflow=c.decode_json(text)
        self.assertEqual(set(workflow['on']),{'push','issue_comment'})
        self.assertEqual(workflow['on']['issue_comment'],{'types':['created']})
        self.assertEqual(workflow['permissions'],{'contents':'read'})
        self.assertEqual(workflow['jobs']['validate']['if'],"github.event_name == 'push'")
        self.assertNotIn('permissions',workflow['jobs']['validate'])
        handler=workflow['jobs']['coordinate']
        self.assertEqual(handler['concurrency'],{'group':'c1-coordination-issue-${{ github.event.issue.number }}','cancel-in-progress':False,'queue':'max'})
        self.assertIn('!github.event.issue.pull_request',handler['if'])
        self.assertIn("github.event.issue.number == 37 || github.event.issue.number == 38",handler['if'])
        self.assertIn("startsWith(github.event.comment.body, '/coord ')",handler['if'])
        self.assertEqual(handler['permissions'],{'contents':'read','actions':'read','issues':'write'})
        self.assertEqual(handler['steps'][0]['with'],{'repository':c.REPOSITORY,'ref':'${{ github.sha }}','persist-credentials':False})
        self.assertEqual(handler['steps'][1]['run'],'python3 scripts/github_coordination.py')
        self.assertEqual(handler['steps'][1]['env'],{'GITHUB_TOKEN':'${{ github.token }}'})
        self.assertFalse(workflow['jobs']['validate']['steps'][0]['with']['persist-credentials'])
        self.assertNotIn('env',workflow['jobs']['validate']['steps'][1])
        for executable in ('docker','playwright','pip install','pull_request.head','github.event.comment.body }}','curl'):
            self.assertNotIn(executable,text.lower())
        self.assertRegex(text,r'actions/checkout@[0-9a-f]{40}')
        # No validation/handler workflow code can modify a domain repository.
        self.assertNotIn('"contents": "write"',text)

    def test_main_malformed_event_and_missing_environment_print_no_payload(self):
        with patch.dict('os.environ',{},clear=True),patch('builtins.print') as output:
            self.assertEqual(c.main(),1)
            self.assertEqual(json.loads(output.call_args.args[0])['reason'],'INVALID_INPUT_OR_API_RESPONSE')


if __name__=='__main__':unittest.main()
