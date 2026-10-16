"""U5-F exact producer request/golden vectors; no HTTP, key or network."""
import hashlib
import json
import unittest
from pathlib import Path

from backend.app import banking_foundation as f

B3 = {
    "handle": "a"*32, "epoch": "b"*32, "actor": "alice",
    "authorization_revision": 1, "binding_ref": "session-1",
    "request_id": "attempt-1", "operation": "transfers.create",
    "operation_id": "intent-1",
    "payload": {"from_account":"A","to_account":"B","amount":1000},
    "key":"bank-key-1", "recovery":False,
}
B3_DIGEST = "c4cde604650d69a4d0496de434c22828efd17cb20a3fbf48e645fb5ac097cb5a"


class BankingFoundationContractTests(unittest.TestCase):
    def test_off_and_golden_exact(self):
        self.assertEqual(f.CAPABILITY,"OFF")
        self.assertEqual(f.CONTRACT,"BIC-1.1-producer-baseline")
        wire, digest = f.canonical_request(B3)
        self.assertEqual(digest, B3_DIGEST)
        self.assertEqual(hashlib.sha256(wire.encode("ascii")).hexdigest(),B3_DIGEST)
        self.assertEqual(wire,json.dumps(B3,sort_keys=True,separators=(",",":"),
                                         ensure_ascii=True,allow_nan=False))

    def test_accepted_domain_source_vectors_not_mislabelled_runtime_proven(self):
        fixture=json.loads((Path(__file__).resolve().parents[1] /
                            "fixtures/banking_b3_producer_v1.json").read_text())
        self.assertEqual(fixture["version"],"BIC-1.1-candidate")
        self.assertEqual(fixture["sha256"],B3_DIGEST)
        self.assertEqual(fixture["canonical_json"],f.canonical_request(B3)[0])
        self.assertEqual(fixture["dispatch_claims"]["request_digest"],B3_DIGEST)
        self.assertEqual(fixture["operation_contract"]["actor_token_endpoint"],
                         "NOT_PRESENT_DOMAIN_INTERNAL_ONLY")
        self.assertEqual(fixture["operation_contract"]["capability"],"OFF")
        self.assertEqual(fixture["control_claims"]["allocate"]["fixture_id"],"synthetic-abc-v1")
        self.assertEqual(fixture["jws_profile"]["grant_max_bytes"],4096)
        self.assertEqual(fixture["jws_profile"]["ttl_max_seconds"],30)
        self.assertNotIn("private_key",fixture)

    def test_decimal_string_exact_s64(self):
        for value in ("1",str(2**53-1),str(2**53+1),str(2**63-1)):
            self.assertEqual(f.money_to_domain(value),int(value))
        for value in (None, True, False, 2**53, 1.0, "0", "-1", "+1",
                      "01","1.0","1e3","1 000","١","",str(2**63),"9"*300):
            with self.subTest(value=value),self.assertRaises(f.BankingDenied):
                f.money_to_domain(value)
        with self.assertRaises(f.BankingDenied):
            f.money_to_domain("2000001", limit=2000000)

    def test_request_canonical_rejects_mutability_and_invalid_amount(self):
        valid = dict(B3)
        for bad in ({"recovery":True},{"authorization_revision":False},
                    {"payload":{**valid["payload"],"amount":True}},
                    {"payload":{**valid["payload"],"amount":2**63}},
                    {"operation":"arbitrary.http"},
                    {"key":None},{"nonce":"extra"}):
            with self.subTest(bad=bad),self.assertRaises(f.BankingDenied):
                f.canonical_request({**valid,**bad})
        changed={**valid,"request_id":"attempt-2"}
        self.assertNotEqual(f.canonical_request(changed)[1],B3_DIGEST)

    def test_strict_json_duplicates_and_numbers(self):
        self.assertEqual(f.parse_json_exact(b'{"x":1,"y":2}'),{"x":1,"y":2})
        for raw in (b'{"x":1,"x":2}',b'{"x":1.0}',b'{"x":NaN}',
                    b'["not-an-object"]',b'{"x":1e9}',b'\xff',b''):
            with self.subTest(raw=raw),self.assertRaises(f.BankingDenied):
                f.parse_json_exact(raw)

    def test_no_transport_signer_or_bank_routes(self):
        from backend.app.api import create_app
        app = create_app("postgresql://nonexistent@127.0.0.1/nonexistent")
        paths={r.path for r in app.routes}
        self.assertFalse(any("/api/integrations/v1/banking" in p for p in paths))
        self.assertFalse(hasattr(f,"private_http_client"))
        self.assertFalse(hasattr(f,"sign_es256"))

class FakeProducerContractTests(unittest.TestCase):
    def setUp(self):
        from tests.banking_fake_consumer import FakeU5Consumer
        self.fixture=json.loads((Path(__file__).resolve().parents[1] /
                "fixtures/banking_b3_producer_v1.json").read_text())
        self.request={k:v for k,v in self.fixture["request"].items() if k!="digest"}
        self.claims=self.fixture["dispatch_claims"]
        self.header={"alg":"ES256","typ":"banking+jwt","kid":"current"}

    def test_golden_claim_matrix_and_negative_identity(self):
        from tests.banking_fake_consumer import check_fixture_grant
        check_fixture_grant(self.header,self.claims,self.request)
        for claim, wrong in (("iss","untrusted"),("aud","wrong"),("sub","wrong"),
                             ("service_id","wrong"),("scope","observe"),
                             ("actor_id","bob"),("context_epoch","0"*32),
                             ("authorization_revision",2),("request_id","different"),
                             ("request_digest","0"*64),("exp",self.claims["iat"]+31)):
            with self.subTest(claim=claim),self.assertRaises(f.BankingDenied):
                check_fixture_grant(self.header,{**self.claims,claim:wrong},self.request)
        for extra in ({"jku":"https://evil.invalid/key"},{"alg":"none"},{"kid":"untrusted"}):
            with self.subTest(extra=extra),self.assertRaises(f.BankingDenied):
                check_fixture_grant({**self.header,**extra},self.claims,self.request)
        tampered={**self.request,"payload":{**self.request["payload"],"amount":1001}}
        with self.assertRaises(f.BankingDenied):
            check_fixture_grant(self.header,self.claims,tampered)

    def test_response_matrix_and_secret_safe_failure(self):
        from tests.banking_fake_consumer import interpret_producer
        transfer={"transfer_id":"tx1","from_account":"A","to_account":"B",
                  "amount":1000,"currency":"VND","status":"SUCCESS",
                  "created_at":"2026-10-16T00:00:00+00:00"}
        for code in (201,200):
            self.assertEqual(interpret_producer(200,{"stored":False,
              "response":{"status":code,"body":transfer}},submitted=True),
              ("OBSERVED","INCONCLUSIVE"))
        for code in (404,409,422):
            self.assertEqual(interpret_producer(200,{"stored":False,
              "response":{"status":code,"body":{"error":{"code":"rejected"}}}},
              submitted=True),("OBSERVED","INCONCLUSIVE"))
        for status in (None,202,401,403,422,429,500,503,504):
            self.assertEqual(interpret_producer(status,None,submitted=True),
                             ("UNKNOWN","INCONCLUSIVE"))
        self.assertEqual(interpret_producer(None,None,submitted=False),
                         ("NOT_RUN","INCONCLUSIVE"))
        with self.assertRaises(f.BankingDenied):
            interpret_producer(200,{"stored":False,"response":{"status":201,
                "body":{**transfer,"amount":2**63}}},submitted=True)
        with self.assertRaises(f.BankingDenied):
            interpret_producer(200,{"stored":False,"response":{"status":201,
                "body":{**transfer,"amount":"1000"}}},submitted=True)
        with self.assertRaises(f.BankingDenied):
            interpret_producer(200,{"stored":False,"response":{"status":201,
                "body":{**transfer,"unexpected_secret":"key"}}},submitted=True)

    def test_fake_crash_windows_original_identity_only(self):
        from tests.banking_fake_consumer import FakeU5Consumer
        sim=FakeU5Consumer()
        self.assertEqual(sim.observe(None,None),("NOT_RUN","INCONCLUSIVE"))
        with self.assertRaises(f.BankingDenied):
            sim.submit()
        sim.accept(self.request)
        sim.accept(self.request)
        with self.assertRaises(f.BankingDenied):
            sim.accept({**self.request,"payload":{**self.request["payload"],"amount":1001}})
        sim.submit()
        sim.submit()
        self.assertEqual(sim.dispatches,1)
        self.assertEqual(sim.observe(None,None),("UNKNOWN","INCONCLUSIVE"))
        self.assertEqual(sim.observe(409,None),("UNKNOWN","INCONCLUSIVE"))
        self.assertEqual(sim.observe(503,None),("UNKNOWN","INCONCLUSIVE"))
        self.assertEqual(sim.dispatches,1)
