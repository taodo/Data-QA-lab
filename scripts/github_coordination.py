"""Bounded GitHub-only coordination. No domain API, AI, shell or app imports."""
from __future__ import annotations

import copy
import hashlib
import json
import os
import re
import sys
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import HTTPRedirectHandler, Request, build_opener

REPOSITORY = 'taodo/Data-QA-lab'
REPOSITORY_ID = 1401920710
PROTOCOL = 'qa-coordination/v1'
WORKFLOW = '.github/workflows/coordination.yml'
TARGETS = {37: ('banking', 'taodo/MiniBanking'), 38: ('automation', 'taodo/Automation-QA-Lab')}
BOT = ('github-actions[bot]', 41898282)
MARKER = '<!-- qa-coordination/v1 -->\n```json\n'
MAX_BODY = 8000
MAX_REVISION = 8
MAX_ROUNDS = 3
MAX_REQUESTS = 10
MAX_COMMENT_PAGES = 5
MAX_RUN_PAGES = 10
MAX_AGE = timedelta(hours=24)
STATES = {'AWAITING_REVIEW', 'REVIEW_POSTED', 'NEEDS_CHANGES', 'BLOCKED',
          'AWAITING_HUMAN_APPROVAL', 'CLOSED'}
CORRELATION = r'c1-(?:37|38)-[1-9][0-9]{0,18}'
LOGIN = r'[A-Za-z0-9][A-Za-z0-9-]{0,38}'


class Rejected(Exception):
    """A static safe reason; never carries event text or API response bodies."""


class ApiFailure(Exception):
    pass


def integer(value):
    return type(value) is int and 0 < value < 2**63


def timestamp(value):
    if not isinstance(value, str) or not re.fullmatch(r'\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ', value):
        raise Rejected('INVALID_TIMESTAMP')
    try:
        return datetime.fromisoformat(value.replace('Z', '+00:00'))
    except ValueError as error:
        raise Rejected('INVALID_TIMESTAMP') from error


def digest(body):
    return hashlib.sha256(body.encode('utf-8')).hexdigest()


def no_duplicate_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('duplicate JSON key')
        result[key] = value
    return result


def decode_json(data):
    return json.loads(data, object_pairs_hook=no_duplicate_keys)


@dataclass(frozen=True)
class Command:
    verb: str
    target: str = ''
    correlation: str = ''
    revision: int = 0
    outcome: str = ''
    decision: str = ''


def parse_command(body):
    if not isinstance(body, str) or len(body.encode('utf-8')) > MAX_BODY:
        raise Rejected('INVALID_BODY')
    normalized = body.replace('\r\n', '\n')
    line, separator, notes = normalized.rstrip('\n').partition('\n\n')
    # Exactly one unindented command at the start. Notes are never interpreted.
    if '\r' in normalized or '\n' in line or (separator and re.search(r'^/coord\b', notes, re.M)):
        raise Rejected('AMBIGUOUS_COMMAND')
    match = re.fullmatch(r'/coord request target=(banking|automation) type=review', line, re.ASCII)
    if match:
        return Command('request', target=match[1])
    match = re.fullmatch(rf'/coord review id=({CORRELATION}) revision=([1-8]) outcome=(review-posted|needs-changes|blocked)', line, re.ASCII)
    if match:
        return Command('review', correlation=match[1], revision=int(match[2]), outcome=match[3].replace('-', '_').upper())
    match = re.fullmatch(rf'/coord (resume|handoff) id=({CORRELATION}) revision=([1-8])', line, re.ASCII)
    if match:
        return Command(match[1], correlation=match[2], revision=int(match[3]))
    match = re.fullmatch(rf'/coord close id=({CORRELATION}) revision=([1-8]) decision=(acknowledged|cancelled)', line, re.ASCII)
    if match:
        return Command('close', correlation=match[1], revision=int(match[2]), decision=match[3])
    raise Rejected('NO_VALID_COMMAND')


def validate_event(event, event_name):
    try:
        if event_name != 'issue_comment' or event['action'] != 'created':
            raise Rejected('EVENT_NOT_ALLOWED')
        repo, issue, comment, sender = (event[k] for k in ('repository', 'issue', 'comment', 'sender'))
        if repo['full_name'] != REPOSITORY or type(repo['id']) is not int or repo['id'] != REPOSITORY_ID:
            raise Rejected('REPOSITORY_NOT_ALLOWED')
        if type(issue['number']) is not int or issue['number'] not in TARGETS or 'pull_request' in issue:
            raise Rejected('ISSUE_NOT_ALLOWED')
        if issue['state'] != 'open' or issue.get('locked') is not False:
            raise Rejected('ISSUE_NOT_OPEN')
        if not integer(comment['id']) or not integer(comment['user']['id']):
            raise Rejected('INVALID_COMMENT')
        author = comment['user']
        if author['type'] != 'User' or sender['type'] != 'User' or not integer(sender['id']) or sender['id'] != author['id']:
            raise Rejected('AUTHOR_NOT_HUMAN')
        if not re.fullmatch(LOGIN, author['login'], re.ASCII) or sender['login'] != author['login']:
            raise Rejected('INVALID_AUTHOR')
        if comment['created_at'] != comment['updated_at']:
            raise Rejected('EDITED_COMMAND')
        timestamp(comment['created_at'])
        command = parse_command(comment['body'])
        if command.verb == 'request' and command.target != TARGETS[issue['number']][0]:
            raise Rejected('TARGET_ISSUE_MISMATCH')
        return issue['number'], comment, command
    except (KeyError, TypeError, AttributeError) as error:
        raise Rejected('MALFORMED_EVENT') from error


def advance(ledger, command, entry, issue):
    """Pure transition reducer. Callers authorize through fresh GitHub metadata."""
    if entry['permission'] not in {'write', 'admin'}:
        raise Rejected('AUTHOR_UNAUTHORIZED')
    if ledger is None:
        if command.verb != 'request' or command.target != TARGETS[issue][0]:
            raise Rejected('NO_ACTIVE_REQUEST')
        return {'protocol': PROTOCOL, 'repository': REPOSITORY, 'issue': issue,
                'target': command.target, 'correlation': f"c1-{issue}-{entry['comment_id']}",
                'request_comment_id': entry['comment_id'], 'state': 'AWAITING_REVIEW',
                'revision': 1, 'review_rounds': 0, 'events': [entry]}
    if command.verb == 'request':
        raise Rejected('ACTIVE_REQUEST_EXISTS')
    if ledger['state'] == 'CLOSED':
        raise Rejected('REQUEST_CLOSED')
    if command.correlation != ledger['correlation'] or command.revision != ledger['revision']:
        raise Rejected('STALE_CORRELATION_OR_REVISION')
    if ledger['revision'] >= MAX_REVISION:
        raise Rejected('TURN_BUDGET_EXHAUSTED')
    result = copy.deepcopy(ledger)
    state = ledger['state']
    if command.verb == 'review' and command.outcome in {'REVIEW_POSTED','NEEDS_CHANGES','BLOCKED'} and state == 'AWAITING_REVIEW' and ledger['review_rounds'] < MAX_ROUNDS:
        result['state'] = command.outcome
        result['review_rounds'] += 1
    elif command.verb == 'resume' and state in {'NEEDS_CHANGES', 'BLOCKED'} and ledger['review_rounds'] < MAX_ROUNDS:
        result['state'] = 'AWAITING_REVIEW'
    elif command.verb == 'handoff' and state == 'REVIEW_POSTED':
        result['state'] = 'AWAITING_HUMAN_APPROVAL'
    elif command.verb == 'close' and entry['permission'] == 'admin' and (
        command.decision == 'cancelled' or state == 'AWAITING_HUMAN_APPROVAL'
    ):
        result['state'] = 'CLOSED'
    else:
        raise Rejected('TRANSITION_NOT_ALLOWED')
    result['revision'] += 1
    result['events'].append(entry)
    return result


def render(ledger):
    issue, correlation, revision = ledger['issue'], ledger['correlation'], ledger['revision']
    target_repo = TARGETS[issue][1]
    next_actor = {
        'AWAITING_REVIEW': f'{target_repo} human reviewer',
        'REVIEW_POSTED': 'Data QA Lab human maintainer',
        'NEEDS_CHANGES': 'request author / responsible maintainer',
        'BLOCKED': 'request author / maintainer resolving the blocker',
        'AWAITING_HUMAN_APPROVAL': 'repository owner/admin',
        'CLOSED': 'none; coordination cycle closed',
    }[ledger['state']]
    sources = '\n'.join(f"- [Human command {e['comment_id']}](https://github.com/{REPOSITORY}/issues/{issue}#issuecomment-{e['comment_id']})" for e in ledger['events'])
    return (MARKER + json.dumps(ledger, sort_keys=True, separators=(',', ':'), ensure_ascii=True)
            + '\n```\n\n## Coordination status\n'
            + f"Protocol: `{PROTOCOL}` · correlation: `{correlation}` · revision: **{revision}**\n\n"
            + f"Source: `{REPOSITORY}#{issue}` · target: `{target_repo}` (review only)\n\n"
            + f"State: **{ledger['state']}** (initial REQUESTED → AWAITING_REVIEW).\n\n"
            + f"Next responsible reviewer/actor: **{next_actor}**.\n\n"
            + f"Read the Issue specification and linked human evidence; respond using the [protocol](https://github.com/{REPOSITORY}/blob/main/docs/CROSS_REPO_COORDINATION.md). "
            + 'Copy the current correlation/revision; review, resume, handoff and closure require explicit authenticated commands.\n\n'
            + sources + '\n\nGitHub status routing only. No separate ChatGPT session was messaged or awakened. '
            + 'No automated review, approval, domain task, merge or deployment. CLOSED closes this coordination cycle only, never the authoritative Issue or its implementation gates.\n')


def read_ledger(comment):
    user = comment.get('user', {})
    if not integer(user.get('id')) or (user.get('login'), user.get('id')) != BOT or user.get('type') != 'Bot':
        return None  # A human-forged marker has no authority.
    body = comment.get('body', '')
    if not isinstance(body, str) or not body.startswith(MARKER):
        return None
    try:
        if len(body.encode('utf-8')) > 32000:
            raise ValueError()
        ledger = decode_json(body[len(MARKER):].split('\n```', 1)[0])
        expected_keys = {'protocol','repository','issue','target','correlation','request_comment_id','state','revision','review_rounds','events'}
        if set(ledger) != expected_keys or type(ledger['issue']) is not int or ledger['issue'] not in TARGETS:
            raise ValueError()
        if (not integer(ledger['request_comment_id']) or type(ledger['revision']) is not int
            or type(ledger['review_rounds']) is not int or ledger['state'] not in STATES):
            raise ValueError()
        events = ledger['events']
        if not isinstance(events, list) or not 1 <= len(events) <= MAX_REVISION:
            raise ValueError()
        rebuilt = None
        ids = set()
        for entry in events:
            if set(entry) != {'comment_id','actor_id','actor_login','permission','body_sha256','line','created_at'}:
                raise ValueError()
            if not integer(entry['comment_id']) or entry['comment_id'] in ids or not integer(entry['actor_id']):
                raise ValueError()
            if not re.fullmatch(LOGIN, entry['actor_login'], re.ASCII) or not re.fullmatch(r'[a-f0-9]{64}', entry['body_sha256']):
                raise ValueError()
            timestamp(entry['created_at'])
            rebuilt = advance(rebuilt, parse_command(entry['line']), entry, ledger['issue'])
            ids.add(entry['comment_id'])
        if rebuilt != ledger or render(ledger) != body:
            raise ValueError()
        return ledger
    except (ValueError, TypeError, KeyError, IndexError, AttributeError, Rejected) as error:
        raise Rejected('LEDGER_INVALID') from error


def scan_ledgers(comments, issue):
    ledgers = []
    ids = set()
    for comment in comments:
        if not isinstance(comment, dict) or not integer(comment.get('id')) or comment['id'] in ids:
            raise Rejected('INVALID_COMMENT_LIST')
        ids.add(comment['id'])
        ledger = read_ledger(comment)
        if ledger:
            if ledger['issue'] != issue or ledger['correlation'] in {l['correlation'] for _, l in ledgers}:
                raise Rejected('LEDGER_CONFLICT')
            ledgers.append((comment, ledger))
    if len(ledgers) > MAX_REQUESTS or sum(l['state'] != 'CLOSED' for _, l in ledgers) > 1:
        raise Rejected('LEDGER_CONFLICT')
    return ledgers


def verify_comment(live, original, issue):
    try:
        if (not integer(live['id']) or not integer(live['user']['id'])
            or live['id'] != original['id'] or live['user']['id'] != original['user']['id']
            or live['user']['login'] != original['user']['login'] or live['user']['type'] != 'User'
            or live['body'] != original['body'] or live['created_at'] != original['created_at']
            or live['updated_at'] != live['created_at']
            or live['issue_url'] != f'https://api.github.com/repos/{REPOSITORY}/issues/{issue}'):
            raise Rejected('COMMENT_CHANGED_OR_SPOOFED')
    except (KeyError, TypeError) as error:
        raise Rejected('INVALID_LIVE_COMMENT') from error


def prior_source_intact(ledger, comments):
    sources = {c['id']: c for c in comments}
    for entry in ledger['events']:
        c = sources.get(entry['comment_id'])
        if not c or c.get('body') is None or c.get('user', {}).get('id') != entry['actor_id']:
            return False
        if c.get('updated_at') != entry['created_at'] or digest(c['body']) != entry['body_sha256']:
            return False
    return True


def coordinate(api, event, *, now, run_id, run_attempt, event_name, github_ref):
    issue, original, command = validate_event(event, event_name)
    repo = api.repository()
    if repo.get('id') != REPOSITORY_ID or repo.get('full_name') != REPOSITORY:
        raise Rejected('LIVE_REPOSITORY_MISMATCH')
    if github_ref != 'refs/heads/'+repo.get('default_branch', ''):
        raise Rejected('UNTRUSTED_EXECUTION_REF')
    api.check_issue(issue)
    verify_comment(api.comment(original['id']), original, issue)
    permission = api.permission(original['user']['login'])
    if (permission.get('permission') not in {'write','admin'}
        or not integer(permission.get('user', {}).get('id'))
        or permission.get('user', {}).get('id') != original['user']['id']
        or permission['user'].get('login') != original['user']['login']):
        raise Rejected('AUTHOR_UNAUTHORIZED')
    comments = api.comments(issue)
    ledgers = scan_ledgers(comments, issue)
    processed = {e['comment_id'] for _, l in ledgers for e in l['events']}
    if original['id'] in processed:
        return 'DUPLICATE_NO_WRITE'
    age = now - timestamp(original['created_at'])
    if age < timedelta(0) or age > MAX_AGE:
        raise Rejected('STALE_COMMAND')
    active = [(c,l) for c,l in ledgers if l['state'] != 'CLOSED']
    current_comment, current = active[0] if active else (None, None)
    if command.verb == 'request':
        if active:
            raise Rejected('ACTIVE_REQUEST_EXISTS')
        if len(ledgers) >= MAX_REQUESTS:
            raise Rejected('REQUEST_BUDGET_EXHAUSTED')
    elif current is None:
        raise Rejected('NO_ACTIVE_REQUEST')
    if ledgers and timestamp(original['created_at']) < max(timestamp(l['events'][-1]['created_at']) for _,l in ledgers):
        raise Rejected('STALE_COMMAND_ORDER')
    if current and not prior_source_intact(current, comments) and not (
        command.verb == 'close' and command.decision == 'cancelled' and permission['permission'] == 'admin'
    ):
        raise Rejected('PRIOR_SOURCE_CHANGED_CANCEL_ONLY')
    entry = {'comment_id':original['id'], 'actor_id':original['user']['id'],
             'actor_login':original['user']['login'], 'permission':permission['permission'],
             'body_sha256':digest(original['body']),
             'line':original['body'].replace('\r\n','\n').rstrip('\n').partition('\n\n')[0],
             'created_at':original['created_at']}
    updated = advance(current, command, entry, issue)
    # GitHub run metadata is durable before the job starts: never reattempt an
    # unacknowledged write for the same event, even if the response was lost.
    api.check_delivery(issue, original['id'], run_id, run_attempt, processed, now)
    api.check_issue(issue)
    verify_comment(api.comment(original['id']), original, issue)
    if current_comment:
        live = api.comment(current_comment['id'])
        if live.get('body') != current_comment['body'] or live.get('updated_at') != current_comment.get('updated_at'):
            raise Rejected('CONCURRENT_LEDGER_CHANGE')
        api.update(current_comment['id'], render(updated))
        return 'UPDATED'
    latest = scan_ledgers(api.comments(issue), issue)
    if [(c['id'],c['body']) for c,_ in latest] != [(c['id'],c['body']) for c,_ in ledgers]:
        raise Rejected('CONCURRENT_LEDGER_CHANGE')
    api.create(issue, render(updated))
    return 'ACKNOWLEDGED'


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class GitHub:
    """Fixed GitHub origin/repository, finite reads, one attempt per mutation."""
    def __init__(self, token):
        self.token = token
        self.opener = build_opener(NoRedirect())

    def call(self, method, suffix='', payload=None, query=None):
        if method not in {'GET','POST','PATCH'} or not re.fullmatch(r'[A-Za-z0-9_./{}-]*', suffix):
            raise ApiFailure('INVALID_API_PATH')
        if method == 'POST' and not re.fullmatch(r'/issues/(?:37|38)/comments', suffix):
            raise ApiFailure('INVALID_MUTATION_PATH')
        if method == 'PATCH' and not re.fullmatch(r'/issues/comments/[1-9][0-9]{0,18}', suffix):
            raise ApiFailure('INVALID_MUTATION_PATH')
        url = f'https://api.github.com/repos/{REPOSITORY}'+suffix
        if query:
            url += '?'+urlencode(query)
        headers = {'Authorization':'Bearer '+self.token, 'Accept':'application/vnd.github+json',
                   'X-GitHub-Api-Version':'2022-11-28', 'User-Agent':'data-qa-coordination-v1'}
        data = json.dumps(payload).encode('utf-8') if payload is not None else None
        if data is not None:
            headers['Content-Type'] = 'application/json'
        try:
            with self.opener.open(Request(url, data=data, headers=headers, method=method), timeout=10) as response:
                raw = response.read(2*1024*1024+1)
                if len(raw) > 2*1024*1024:
                    raise ValueError()
                return decode_json(raw)
        except (HTTPError, URLError, OSError, ValueError, RecursionError) as error:
            if isinstance(error, HTTPError):
                error.close()
            # Never print tokens, URLs derived from payload, or upstream bodies.
            reason = 'READ_FAILED' if method == 'GET' else 'WRITE_UNCERTAIN_DO_NOT_RETRY'
            raise ApiFailure(reason) from error

    def repository(self):return self.call('GET')
    def comment(self, comment_id):return self.call('GET', f'/issues/comments/{comment_id}')
    def permission(self, login):return self.call('GET', f'/collaborators/{quote(login, safe="")}/permission')

    def check_issue(self, issue):
        value = self.call('GET', f'/issues/{issue}')
        if type(value.get('number')) is not int or value.get('number') != issue or value.get('state') != 'open' or value.get('locked') is not False or 'pull_request' in value:
            raise Rejected('ISSUE_NOT_OPEN')

    def comments(self, issue):
        result = []
        for page in range(1, MAX_COMMENT_PAGES+1):
            batch = self.call('GET', f'/issues/{issue}/comments', query={'per_page':100,'page':page})
            if not isinstance(batch, list):raise ApiFailure('INVALID_COMMENT_RESPONSE')
            result.extend(batch)
            if len(batch) < 100:return result
        raise Rejected('COMMENT_SCAN_BUDGET_EXHAUSTED')

    def check_delivery(self, issue, comment_id, run_id, attempt, processed, now):
        if not integer(run_id) or type(attempt) is not int or attempt != 1:
            raise Rejected('REPLAY_WITHOUT_RECEIPT_NO_WRITE')
        title = f'C1 issue {issue} comment {comment_id}'
        current = self.call('GET', f'/actions/runs/{run_id}')
        if (not integer(current.get('id')) or current.get('id') != run_id or current.get('event') != 'issue_comment'
            or current.get('path') != WORKFLOW or current.get('display_title') != title
            or type(current.get('run_attempt')) is not int or current.get('run_attempt') != 1
            or type(current.get('repository', {}).get('id')) is not int
            or current.get('repository', {}).get('id') != REPOSITORY_ID):
            raise Rejected('INVALID_EXECUTION_RUN')
        seen = False
        since = (now-MAX_AGE).strftime('%Y-%m-%dT%H:%M:%SZ')
        for page in range(1, MAX_RUN_PAGES+1):
            response = self.call('GET', '/actions/workflows/coordination.yml/runs', query={
                'event':'issue_comment','created':'>='+since,'per_page':100,'page':page})
            runs = response.get('workflow_runs')
            if not isinstance(runs, list):raise ApiFailure('INVALID_RUN_RESPONSE')
            for run in runs:
                if run.get('id') == run_id:
                    seen = True
                    continue
                if run.get('display_title') == title:
                    raise Rejected('PRIOR_DELIVERY_NO_WRITE')
                match = re.fullmatch(rf'C1 issue {issue} comment ([1-9][0-9]{{0,18}})', run.get('display_title', ''))
                if match and int(match[1]) not in processed and run.get('conclusion') in {'failure','cancelled','timed_out','action_required'}:
                    raise Rejected('PRIOR_DELIVERY_UNRESOLVED_OPERATOR_REQUIRED')
            if len(runs) < 100:
                if not seen:raise Rejected('EXECUTION_RUN_NOT_VISIBLE')
                return
        raise Rejected('RUN_SCAN_BUDGET_EXHAUSTED')

    @staticmethod
    def verify_write(value, body, comment_id=None):
        try:
            valid = (isinstance(value, dict) and integer(value.get('id'))
                     and (comment_id is None or value['id'] == comment_id)
                     and value.get('body') == body and read_ledger(value) is not None)
        except Rejected:
            valid = False
        if not valid:
            raise ApiFailure('WRITE_UNCERTAIN_DO_NOT_RETRY')

    def create(self, issue, body):
        self.verify_write(self.call('POST', f'/issues/{issue}/comments', {'body':body}), body)

    def update(self, comment_id, body):
        self.verify_write(self.call('PATCH', f'/issues/comments/{comment_id}', {'body':body}), body, comment_id)


def main():
    try:
        raw = Path(os.environ['GITHUB_EVENT_PATH']).read_bytes()
        if len(raw) > 1024*1024:raise Rejected('EVENT_TOO_LARGE')
        event = decode_json(raw)
        token = os.environ.get('GITHUB_TOKEN', '')
        if not token:raise ApiFailure('TOKEN_MISSING')
        result = coordinate(GitHub(token), event, now=datetime.now(UTC),
                            run_id=int(os.environ['GITHUB_RUN_ID']),
                            run_attempt=int(os.environ['GITHUB_RUN_ATTEMPT']),
                            event_name=os.environ['GITHUB_EVENT_NAME'], github_ref=os.environ['GITHUB_REF'])
        print(json.dumps({'result':result,'protocol':PROTOCOL}))
        return 0
    except Rejected as error:
        print(json.dumps({'result':'NO_WRITE','reason':str(error),'protocol':PROTOCOL}))
        return 0
    except ApiFailure as error:
        print(json.dumps({'result':'FAIL_CLOSED','reason':str(error),'protocol':PROTOCOL}))
        return 1
    except (KeyError, TypeError, ValueError, AttributeError, RecursionError):
        print(json.dumps({'result':'FAIL_CLOSED','reason':'INVALID_INPUT_OR_API_RESPONSE','protocol':PROTOCOL}))
        return 1


if __name__ == '__main__':
    sys.exit(main())
