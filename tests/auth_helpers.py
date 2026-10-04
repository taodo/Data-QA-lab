"""Real account fixtures for HTTP tests; production dependencies stay intact."""
from uuid import uuid4
from fastapi.testclient import TestClient
from backend.app.api import create_app
PASSWORD = 'test-only-long-passphrase'


def signed_client(db, name=None):
    client = TestClient(create_app(db))
    name = name or 'learner_' + uuid4().hex[:16]
    result = client.post('/api/auth/signup', json={'username':name,'display_name':'Test learner','password':PASSWORD}, headers={'X-DQA-Intent':'1'})
    assert result.status_code == 201, result.text
    state = result.json()
    client.headers.update({'X-CSRF-Token':state['csrf_token'],'X-DQA-Account':state['user']['user_id']})
    return client, state['user']
