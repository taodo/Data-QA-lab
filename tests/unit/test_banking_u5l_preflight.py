"""Offline source compatibility checks, NOT signed U5-L interoperability.

These pin accepted producer artifacts and an additive future consumer policy.
Amended owner acceptance/security signoff remain pending. No signer, transport,
database, real BFF guard, worker or runtime authorization fallback is implemented.
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



def _future_mutation_example_allowed(case, pins):
    """Test-local acceptance example, NOT authentication or a real BFF guard.

    Session/public_shared/roster are stipulated server-side facts in these
    offline examples. Real authoritative PG/ASGI checks remain NOT RUN.
    """
    return (case.get("session_active") is True
            and case.get("csrf_matches") is True
            and case.get("public_shared") is False
            and case.get("entry_point") == "LOCAL_OWNED"
            and type(case.get("session")) is str and bool(case["session"])
            and case["session"] == case.get("binding_session")
            and case.get("origin") == pins["origin"]
            and case.get("host") == pins["host"]
            and case.get("actor") in case.get("authorized_actors", []))


class BankingU5LCorrectiveSpecificationTests(unittest.TestCase):
    """Executable OFFLINE contract checks; future live acceptance is NOT RUN."""

    def setUp(self):
        self.policy = fixture("banking_u5l_consumer_policy_v1.json")
        self.doc = (FIXTURES.parents[1] / "docs/BANKING_U5L_APPROVAL_CHECKPOINT.md").read_text(
            encoding="utf-8")
        producer = fixture("banking_u5l_b3_accepted.json")
        self.original = {key: value for key, value in producer["request"].items()
                         if key != "digest"}

    def test_consumer_recovery_scope_and_transfer_redispatch_forbidden(self):
        transfer = self.policy["transfer"]
        reconcile = self.policy["reconciliation"]
        self.assertIs(transfer["recovery"], False)
        self.assertEqual(transfer["scope"], "dispatch")
        self.assertEqual(transfer["maximum_initial_dispatches"], 1)
        self.assertEqual(reconcile["scope"], "observe")
        self.assertTrue(reconcile["route"].endswith("/observe-operation"))
        self.assertIs(reconcile["recovery"], False)
        self.assertIs(reconcile["redispatch"], False)
        self.assertIs(reconcile["new_allocation"], False)
        self.assertEqual(reconcile["identity"], "ORIGINAL_FROZEN_REQUEST_UNCHANGED")
        with self.assertRaises(foundation.BankingDenied):
            foundation.canonical_request({**self.original, "recovery": True})
        # Existing fixture checker is transfer-dispatch-only, not a live signer.
        from tests.banking_fake_consumer import check_fixture_grant
        claims = fixture("banking_u5l_b3_accepted.json")["dispatch_claims"]
        for forbidden in ("recover", "observe", "arbitrary"):
            with self.subTest(scope=forbidden), self.assertRaises(foundation.BankingDenied):
                check_fixture_grant({"alg": "ES256", "typ": "banking+jwt", "kid": "current"},
                                    {**claims, "scope": forbidden}, self.original)

    def test_fixed_read_profiles_are_separate_and_use_null_key(self):
        expected = {"accounts.list": [], "accounts.balance": ["account_id"],
                    "accounts.history": ["account_id", "limit", "offset"],
                    "transfers.lookup": ["transfer_id"]}
        self.assertEqual(set(self.policy["reads"]), set(expected))
        for operation, fields in expected.items():
            with self.subTest(operation=operation):
                profile = self.policy["reads"][operation]
                self.assertEqual(profile["payload_fields"], fields)
                self.assertIsNone(profile["key"])
                # Do not broaden the existing transfer-acceptance canonicalizer.
                with self.assertRaises(foundation.BankingDenied):
                    foundation.canonical_request({**self.original, "operation": operation,
                                                  "key": None, "payload": {}})
        history = self.policy["reads"]["accounts.history"]
        self.assertEqual(history["limit"], [1, 100])
        self.assertEqual(history["offset"], [0, 10000])
        self.assertIn("Read IDs are safe ASCII", self.doc)
        self.assertIn("key=null", self.doc)
        self.assertIn("server-owned authorized context roster", self.doc)

    def test_future_bff_contract_denies_enabled_authenticated_shared_demo(self):
        # This exercises the specification predicate, NOT accounts.login or BFF.
        case = {**self.policy["bff_required"], **self.policy["bff_example_pins"],
                "actor": "alice"}
        self.assertTrue(_future_mutation_example_allowed(case, self.policy["bff_example_pins"]))
        self.assertFalse(_future_mutation_example_allowed(
            {**case, "public_shared": True, "demo_enabled": True,
             "browser_public_shared": False}, self.policy["bff_example_pins"]))
        self.assertIn("Actual BFF/PG/ASGI guard", self.doc)

    def test_future_bff_host_origin_session_and_test_client_contract(self):
        case = {**self.policy["bff_required"], **self.policy["bff_example_pins"],
                "actor": "alice"}
        pins = self.policy["bff_example_pins"]
        for example in self.policy["bff_denials"]:
            with self.subTest(example=example["name"]):
                self.assertEqual(example["expect"], "DENY")
                self.assertFalse(_future_mutation_example_allowed(
                    {**case, **example["change"]}, pins))
        # Non-browser ASGI uses exactly the same specified controls.
        self.assertTrue(_future_mutation_example_allowed({**case, "client": "ASGI"}, pins))
        self.assertFalse(_future_mutation_example_allowed(
            {**case, "client": "ASGI", "origin": None, "test_header": True}, pins))
        self.assertIn("No exemption based on User-Agent", self.doc)

    def test_offline_unknown_403_and_inconclusive_never_settle(self):
        from tests.banking_fake_consumer import FakeU5Consumer
        fake = FakeU5Consumer()
        fake.accept(self.original)
        fake.submit()
        self.assertEqual(fake.observe(None, None), ("UNKNOWN", "INCONCLUSIVE"))
        self.assertEqual(fake.observe(403, None), ("UNKNOWN", "INCONCLUSIVE"))
        self.assertEqual(fake.dispatches, 1)
        ambiguity = self.policy["ambiguity_policy"]
        self.assertEqual(ambiguity["phase"], "UNKNOWN_OR_HELD")
        self.assertEqual(ambiguity["outcome"], "INCONCLUSIVE")
        for name in ("successful_observation", "settles_original", "redispatch"):
            self.assertIs(ambiguity[name], False)
        reasons = {case["source_condition"]: case["outer"]
                   for case in self.policy["inconclusive_observations"]}
        for reason in ("REVOKED_BINDING", "UNKNOWN_OPERATION",
                       "OBSERVATION_CAPACITY", "RECEIPT_CAPACITY"):
            self.assertEqual(reasons[reason], 403)
        self.assertEqual(reasons["WRITER_NOT_DRAINED"], 200)
        self.assertIsNone(reasons["TRANSPORT_LOSS"])
        self.assertEqual(ambiguity["assessment"], "NOT_ASSESSED")

    def test_lifecycle_lease_and_outbox_ack_invariant_specification(self):
        self.assertEqual(self.policy["lifecycle_when_possible"], [
            "FENCE_ADMISSION", "PERSIST_DRAIN_ATTEMPT", "DRAIN",
            "PERSIST_OBSERVE_ATTEMPT", "BOUNDED_ORIGINAL_OBSERVE",
            "PERSIST_REVOKE_ATTEMPT", "REVOKE", "VERIFY_CURRENT_ACK_FENCE"])
        self.assertEqual(self.policy["unobservable"],
                         "RETAIN_UNKNOWN_OR_HELD__ESCALATE__REVOKE_WITHOUT_FALSE_SETTLEMENT")
        for invariant in self.policy["lifecycle_requirements"]:
            self.assertIn("**" + invariant + " —", self.doc)
        for requirement in ("SKIP LOCKED", "ever_unknown", "stale SUBMITTING",
                            "pre-I/O attempt", "lease generation", "NOT RUN"):
            self.assertIn(requirement, self.doc)
        self.assertEqual(set(self.policy["ack_correlation"]), {
            "outbox_operation_id", "binding", "context", "epoch", "revision",
            "control_request_identity", "lease_generation"})
        self.assertEqual(self.policy["producer_ack_body"], {"revocation": "ACKNOWLEDGED"})
        self.assertEqual(self.policy["ack_rejections"], ["late", "stale", "duplicate"])
        self.assertIn("does NOT echo outbox identity", self.doc)
        self.assertEqual(self.policy["retention"],
                         "INDEFINITE_UNTIL_AUTHORIZED_DISPOSITION__NO_AUTOMATIC_EVICTION")
        self.assertEqual(self.policy["reconciliation"]["attempts_per_5_minutes"], 3)
        self.assertEqual(self.policy["reconciliation"]["attempts_lifetime"], 10)

    def test_corrective_policy_is_not_runtime_or_human_signoff(self):
        self.assertEqual(self.policy["status"],
                         "SPECIFICATION_ONLY__AMENDMENT_ACCEPTANCE_AND_SECURITY_SIGNOFF_PENDING")
        self.assertIs(self.policy["runtime_executed"], False)
        self.assertEqual(self.policy["producer_merge"],
                         fixture("banking_u5l_source_pins.json")["accepted_merge"])
        self.assertEqual(self.policy["money"],
                         "INTEGER_VND_ONLY__BROWSER_CANONICAL_ASCII_DECIMAL")
        self.assertIn("renewed explicit human acceptance", self.doc)
        self.assertIn("independent human security/operator reviewer", self.doc)
        self.assertIn("NOT a changed producer fixture", self.doc)


if __name__ == "__main__":
    unittest.main()
