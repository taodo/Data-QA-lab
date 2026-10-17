"""Offline source compatibility checks, NOT signed U5-L interoperability.

These pin accepted producer artifacts while the joint live-integration approval
is missing. No signer, transport, database, or test-only authorization fallback.
"""
import copy
import hashlib
import json
from pathlib import Path
import unittest

from backend.app import banking_foundation as foundation

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"


def fixture(name):
    return json.loads((FIXTURES / name).read_bytes())


class BankingU5LOfflinePreflightTests(unittest.TestCase):
    def test_exact_accepted_producer_blobs_and_provenance(self):
        pins = fixture("banking_u5l_source_pins.json")
        self.assertEqual(pins["producer_repository"], "taodo/MiniBanking")
        self.assertEqual(pins["accepted_merge"],
                         "970c5fa24092c08c4477b12ad40d45fc8e067b8b")
        self.assertEqual(pins["platform_base"],
                         "d48e9bf501c831502d90f5894e5d1b5531d0a2c5")
        self.assertEqual(pins["status"],
                         "OFFLINE_ONLY__LIVE_INTEROP_BLOCKED_PENDING_JOINT_APPROVAL")
        self.assertEqual(len(pins["fixtures"]), 2)
        for record in pins["fixtures"]:
            with self.subTest(path=record["upstream_path"]):
                self.assertEqual(hashlib.sha256(
                    (FIXTURES / record["fixture"]).read_bytes()).hexdigest(),
                    record["sha256"])

    def test_b4_acceptance_does_not_change_b3_canonical_bytes(self):
        producer = fixture("banking_u5l_b3_accepted.json")
        self.assertEqual(producer, fixture("banking_b3_producer_v1.json"))
        request = {key: value for key, value in producer["request"].items()
                   if key != "digest"}
        canonical, digest = foundation.canonical_request(request)
        self.assertEqual(canonical, producer["canonical_json"])
        self.assertEqual(digest, producer["sha256"])
        self.assertEqual(digest, producer["dispatch_claims"]["request_digest"])
        b4 = fixture("banking_u5l_b4_accepted_v2.json")
        self.assertFalse(b4["predecessor"]["wire_changed"])
        self.assertEqual(b4["predecessor"]["joint_design_alias"], foundation.CONTRACT)

    def test_lossless_money_and_frozen_digest_counterexamples(self):
        producer = fixture("banking_u5l_b3_accepted.json")
        original = {key: value for key, value in producer["request"].items()
                    if key != "digest"}
        for amount in (2**53 - 1, 2**53 + 1, 2**63 - 1):
            request = copy.deepcopy(original)
            request["payload"]["amount"] = foundation.money_to_domain(str(amount))
            encoded, digest = foundation.canonical_request(request)
            self.assertIn('"amount":' + str(amount), encoded)
            self.assertNotEqual(digest, producer["sha256"])
            self.assertEqual(json.loads(encoded)["payload"]["amount"], amount)
        for amount in (True, 1000.0, "1000", 2**63):
            request = copy.deepcopy(original)
            request["payload"]["amount"] = amount
            with self.subTest(amount=amount), self.assertRaises(foundation.BankingDenied):
                foundation.canonical_request(request)
        for changed in ({"actor": "bob"}, {"binding_ref": "another-session"},
                        {"request_id": "another-attempt"}, {"key": "another-key"}):
            self.assertNotEqual(foundation.canonical_request(
                {**original, **changed})[1], producer["sha256"])
        self.assertEqual(foundation.canonical_request(original)[1], producer["sha256"])

    def test_v2_outer_inner_error_matrix_is_not_legacy_fake_matrix(self):
        producer = fixture("banking_u5l_b4_accepted_v2.json")
        actual = {(row["outer"], row["inner"])
                  for row in producer["private_http_status_matrix"]}
        self.assertEqual(actual, {
            (200, 201), (200, 200), (200, 409), (200, 404), (200, 422),
            (200, 401), (200, 500), (200, 503),
            (202, None), (400, None), (403, None), (404, None),
            (503, None), (None, None),
        })
        self.assertEqual(set(producer["not_emitted_by_current_producer"]),
                         {"outer401", "outer422", "outer429"})
        # These are source-document checks, not an exercised HTTP mapper.
        rows = {(row["outer"], row["inner"]): row["meaning"]
                for row in producer["private_http_status_matrix"]}
        self.assertIn("cannot settle an earlier UNKNOWN", rows[200, 409])
        self.assertIn("earlier UNKNOWN preserved", rows[200, 401])
        self.assertIn("timeout does not cancel writer", rows[202, None])
        self.assertIn("never infer no historic commit", rows[503, None])

    def test_v2_sql_match_is_not_authenticated_receipt_or_platform_grade(self):
        producer = fixture("banking_u5l_b4_accepted_v2.json")
        evidence = producer["evidence_schema"]
        self.assertEqual(evidence["schema"], "minibanking-b4-sql-evidence-v2")
        self.assertEqual(evidence["source"], "independent_sqlite_read_only")
        self.assertEqual(evidence["signed_receipt"], "NOT_VERIFIED")
        self.assertEqual(evidence["assessment"], "NOT_ASSESSED")
        self.assertEqual(evidence["outcomes"],
                         ["SQL_MATCH_FOR_DECLARED_OBSERVATIONS", "INCONCLUSIVE"])
        self.assertEqual(evidence["absence"], "INCONCLUSIVE_NEVER_NO_COMMIT")
        self.assertEqual(evidence["import_trust"],
                         "UNTRUSTED_IMPORTED_EVIDENCE_NOT_A_PLATFORM_GRADE")
        self.assertEqual(producer["gates"]["U5_L_interop"], "BLOCKED_ISSUE_51")
        self.assertEqual(foundation.CAPABILITY, "OFF")


if __name__ == "__main__":
    unittest.main()
