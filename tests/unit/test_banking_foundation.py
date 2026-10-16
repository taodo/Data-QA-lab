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
