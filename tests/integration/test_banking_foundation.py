"""U5-F PostgreSQL isolation, durable ACCEPT/SUBMIT and restart invariants.

Runs only with DATA_QA_TEST_DATABASE_URL. Creates a throwaway database and
never touches the learner/demo DB; no private bank network or signer calls.
"""
import os
import unittest
from uuid import UUID, uuid4

from fastapi.testclient import TestClient
from psycopg import sql
from psycopg.conninfo import make_conninfo

from backend.app import accounts, banking_foundation as bf
from backend.app.api import create_app
from backend.app.persistence.database import connect, initialize_database, transaction
from tests.auth_helpers import signed_client, PASSWORD

DB=os.getenv("DATA_QA_TEST_DATABASE_URL")


@unittest.skipUnless(DB,"Isolated PostgreSQL test database required")
class BankingFoundationPostgresTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.name="u5_foundation_"+uuid4().hex
        cls.db=make_conninfo(DB,dbname=cls.name)
        with connect(DB) as admin:
            admin.autocommit=True
            admin.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(cls.name)))
        initialize_database(cls.db)
        initialize_database(cls.db) # additive, idempotent migration

    @classmethod
    def tearDownClass(cls):
        with connect(DB) as admin:
            admin.autocommit=True
            admin.execute(sql.SQL("DROP DATABASE {} WITH (FORCE)").format(sql.Identifier(cls.name)))

    def setUp(self):
        # This entire database is disposable. Isolate quota/time-window state
        # between tests without ever touching account or Data track tables.
        with transaction(self.db) as tx:
            for table in ("banking_observations","banking_attempts",
                          "banking_revocation_outbox","banking_operations",
                          "banking_contexts","banking_bindings"):
                tx.execute("DELETE FROM metadata."+table)
        self.a,self.user=signed_client(self.db)
        self.session_a=accounts.token_hash(self.a.cookies.get(accounts.COOKIE))
        self.principal_a={"user_id":self.user["user_id"],"token_hash":self.session_a}

    def test_session_unique_binding_and_orphan_hold_persists_logout(self):
        other=TestClient(create_app(self.db))
        response=other.post("/api/auth/login",json={"username":self.user["username"],
                            "password":PASSWORD},headers={"X-DQA-Intent":"1"})
        self.assertEqual(response.status_code,200,response.text)
        p2={"user_id":self.user["user_id"],
            "token_hash":accounts.token_hash(other.cookies.get(accounts.COOKIE))}
        with transaction(self.db) as tx:
            one=bf.binding_for_session(tx,self.principal_a)
            two=bf.binding_for_session(tx,p2)
            self.assertNotEqual(one,two)
            self.assertEqual(one,bf.binding_for_session(tx,self.principal_a))
            a=bf.reserve_context(tx,self.principal_a,uuid4())
            b=bf.reserve_context(tx,p2,uuid4())
            self.assertNotEqual(a["context_id"],b["context_id"])
            self.assertFalse(bf.reserve_context(tx,self.principal_a,
                tx.execute("SELECT allocation_intent_id FROM metadata.banking_contexts WHERE context_id=%s",
                           (UUID(a["context_id"]),)).fetchone()[0])["created"])
        self.assertEqual(self.a.post("/api/auth/logout").status_code,200)
        with transaction(self.db) as tx:
            with self.assertRaises(bf.BankingDenied):
                bf.binding_for_session(tx,self.principal_a)
            # accounts.logout must already have atomically queued the
            # revocation before deleting its session row.
            held=tx.execute("SELECT state FROM metadata.banking_contexts WHERE context_id=%s",
                            (UUID(a["context_id"]),)).fetchone()[0]
            self.assertEqual(held,"RECOVERY_HOLD")
            self.assertEqual(tx.execute(
                "SELECT count(*) FROM metadata.banking_revocation_outbox WHERE binding_ref=%s",
                (one,)).fetchone()[0],1)
            self.assertEqual(tx.execute("SELECT state FROM metadata.banking_bindings WHERE binding_ref=%s",
                                        (two,)).fetchone()[0],"ACTIVE")

    def test_frozen_accept_submit_duplicate_conflict_and_unknown(self):
        intent=uuid4()
        with transaction(self.db) as tx:
            reserved=bf.reserve_context(tx,self.principal_a,uuid4())
            bf.attach_private_context(tx,self.principal_a,UUID(reserved["context_id"]),
                                      context_ref="a"*32,epoch="b"*32,revision=1,
                                      authorized_actors=("alice",))
            with self.assertRaises(bf.BankingDenied):
                bf.accept_intent(tx,self.principal_a,
                     context_id=UUID(reserved["context_id"]),client_intent_id=uuid4(),
                     actor="bob",from_account="A",to_account="B",amount="1000")
            accepted=bf.accept_intent(tx,self.principal_a,
                 context_id=UUID(reserved["context_id"]),client_intent_id=intent,
                 actor="alice",from_account="A",to_account="B",amount="1000")
            duplicate=bf.accept_intent(tx,self.principal_a,
                 context_id=UUID(reserved["context_id"]),client_intent_id=intent,
                 actor="alice",from_account="A",to_account="B",amount="1000")
            self.assertTrue(accepted["created"])
            self.assertEqual(duplicate["operation_id"],accepted["operation_id"])
            self.assertFalse(duplicate["created"])
            with self.assertRaises(bf.BankingDenied):
                bf.accept_intent(tx,self.principal_a,
                    context_id=UUID(reserved["context_id"]),client_intent_id=intent,
                    actor="alice",from_account="A",to_account="B",amount="1001")
        # Separate PG transaction proves ACCEPT persisted before SUBMIT.
        with transaction(self.db) as tx:
            row=tx.execute("SELECT phase,frozen_request,request_digest FROM metadata.banking_operations "
                           "WHERE operation_id=%s",(UUID(accepted["operation_id"]),)).fetchone()
            self.assertEqual(row[0],"ACCEPTED")
            _,digest=bf.canonical_request(row[1])
            self.assertEqual(row[2],digest)
            started=bf.submit_intent(tx,self.principal_a,
                                     operation_id=UUID(accepted["operation_id"]))
            self.assertEqual(started["phase"],"SUBMITTING")
            self.assertTrue(started["created"])
        with transaction(self.db) as tx:
            repeated=bf.submit_intent(tx,self.principal_a,
                                      operation_id=UUID(accepted["operation_id"]))
            self.assertFalse(repeated["created"])
            self.assertEqual(repeated["phase"],"SUBMITTING")
            bf.mark_uncertain(tx,self.principal_a,
                              operation_id=UUID(accepted["operation_id"]))
        with transaction(self.db) as tx:
            same=bf.submit_intent(tx,self.principal_a,
                                  operation_id=UUID(accepted["operation_id"]))
            self.assertEqual(same["phase"],"UNKNOWN")
            self.assertEqual(tx.execute(
                "SELECT count(*) FROM metadata.banking_attempts WHERE operation_id=%s",
                (UUID(accepted["operation_id"]),)).fetchone()[0],1)
            self.assertEqual(tx.execute(
                "SELECT outcome FROM metadata.banking_operations WHERE operation_id=%s",
                (UUID(accepted["operation_id"]),)).fetchone()[0],"INCONCLUSIVE")
            bf.fence_session(tx,self.session_a)
            self.assertEqual(tx.execute(
                "SELECT phase FROM metadata.banking_operations WHERE operation_id=%s",
                (UUID(accepted["operation_id"]),)).fetchone()[0],"UNKNOWN")

    def test_same_owner_other_session_cannot_read_or_submit(self):
        with transaction(self.db) as tx:
            ctx=bf.reserve_context(tx,self.principal_a,uuid4())
            bf.attach_private_context(tx,self.principal_a,UUID(ctx["context_id"]),
                                      context_ref="a"*32,epoch="b"*32,revision=1,
                                      authorized_actors=("alice",))
            op=bf.accept_intent(tx,self.principal_a,context_id=UUID(ctx["context_id"]),
                                client_intent_id=uuid4(),actor="alice",
                                from_account="A",to_account="B",amount="1000")
        other=TestClient(create_app(self.db))
        self.assertEqual(other.post("/api/auth/login",json={
            "username":self.user["username"],"password":PASSWORD
        },headers={"X-DQA-Intent":"1"}).status_code,200)
        another={"user_id":self.user["user_id"],
            "token_hash":accounts.token_hash(other.cookies.get(accounts.COOKIE))}
        with transaction(self.db) as tx:
            with self.assertRaises(bf.BankingDenied):
                bf.submit_intent(tx,another,operation_id=UUID(op["operation_id"]))
        with transaction(self.db) as tx:
            tx.execute("UPDATE metadata.account_sessions SET expires_at=NOW()-interval '1 second'"
                       " WHERE token_hash=%s",(self.session_a,))
        with transaction(self.db) as tx:
            with self.assertRaises(bf.BankingDenied):
                bf.submit_intent(tx,self.principal_a,operation_id=UUID(op["operation_id"]))

    def test_unprovisioned_and_conflicting_context_deny(self):
        with transaction(self.db) as tx:
            ctx=bf.reserve_context(tx,self.principal_a,uuid4())
            with self.assertRaises(bf.BankingDenied):
                bf.accept_intent(tx,self.principal_a,context_id=UUID(ctx["context_id"]),
                                 client_intent_id=uuid4(),actor="alice",
                                 from_account="A",to_account="B",amount="1")
            with self.assertRaises(bf.BankingDenied):
                bf.reserve_context(tx,self.principal_a,uuid4())


    def test_session_expiry_sweep_queues_revocation_without_deleting_unknown(self):
        with transaction(self.db) as tx:
            ctx=bf.reserve_context(tx,self.principal_a,uuid4())
            bf.attach_private_context(tx,self.principal_a,UUID(ctx["context_id"]),
                                      context_ref="a"*32,epoch="b"*32,revision=1,
                                      authorized_actors=("alice",))
            accepted=bf.accept_intent(tx,self.principal_a,
                      context_id=UUID(ctx["context_id"]),client_intent_id=uuid4(),
                      actor="alice",from_account="A",to_account="B",amount="1")
            bf.submit_intent(tx,self.principal_a,
                             operation_id=UUID(accepted["operation_id"]))
        with transaction(self.db) as tx:
            tx.execute("UPDATE metadata.account_sessions SET expires_at=NOW()-interval '1 second'"
                       " WHERE token_hash=%s",(self.session_a,))
            self.assertGreaterEqual(bf.fence_orphaned_bindings(tx),1)
        with transaction(self.db) as tx:
            self.assertEqual(tx.execute(
                "SELECT phase,outcome FROM metadata.banking_operations WHERE operation_id=%s",
                (UUID(accepted["operation_id"]),)).fetchone(),("UNKNOWN","INCONCLUSIVE"))
            self.assertEqual(tx.execute(
                "SELECT count(*) FROM metadata.banking_revocation_outbox "
                "WHERE context_id=%s AND status='PENDING'",
                (UUID(ctx["context_id"]),)).fetchone()[0],1)
            self.assertEqual(bf.fence_orphaned_bindings(tx),0)

    def test_f2_allocation_quota_session_and_user_windows(self):
        # All rows are disposable. Retained contexts still consume per-user quota.
        first_intent=uuid4()
        with transaction(self.db) as tx:
            result=bf.reserve_context(tx,self.principal_a,first_intent)
            self.assertEqual(bf.reserve_context(tx,self.principal_a,first_intent)
                             ["context_id"],result["context_id"])
            tx.execute("UPDATE metadata.banking_contexts SET state='RETAINED' WHERE context_id=%s",
                       (UUID(result["context_id"]),))
            with self.assertRaisesRegex(bf.BankingDenied,"Allocation rate"):
                bf.reserve_context(tx,self.principal_a,uuid4())
        # Another authenticated session for same user remains separately bound.
        second=TestClient(create_app(self.db))
        self.assertEqual(second.post("/api/auth/login",json={
            "username":self.user["username"],"password":PASSWORD
        },headers={"X-DQA-Intent":"1"}).status_code,200)
        p2={"user_id":self.user["user_id"],
            "token_hash":accounts.token_hash(second.cookies.get(accounts.COOKIE))}
        with transaction(self.db) as tx:
            result=bf.reserve_context(tx,p2,uuid4())
            tx.execute("UPDATE metadata.banking_contexts SET state='RETAINED' WHERE context_id=%s",
                       (UUID(result["context_id"]),))
        # Per-user / 10-minute window rejects third allocation even with new session.
        third=TestClient(create_app(self.db))
        self.assertEqual(third.post("/api/auth/login",json={
            "username":self.user["username"],"password":PASSWORD
        },headers={"X-DQA-Intent":"1"}).status_code,200)
        p3={"user_id":self.user["user_id"],
            "token_hash":accounts.token_hash(third.cookies.get(accounts.COOKIE))}
        with transaction(self.db) as tx:
            with self.assertRaisesRegex(bf.BankingDenied,"Allocation rate"):
                bf.reserve_context(tx,p3,uuid4())
            self.assertEqual(tx.execute(
                "SELECT count(*) FROM metadata.banking_contexts c "
                "JOIN metadata.banking_bindings b USING(binding_ref) WHERE b.user_id=%s",
                (self.user["user_id"],)).fetchone()[0],2)

    def test_f2_submit_rate_limit_does_not_mutate_unknown(self):
        with transaction(self.db) as tx:
            ctx=bf.reserve_context(tx,self.principal_a,uuid4())
            bf.attach_private_context(tx,self.principal_a,UUID(ctx["context_id"]),
                                      context_ref="a"*32,epoch="b"*32,revision=1,
                                      authorized_actors=("alice",))
            ops=[]
            for n in range(7):
                op=bf.accept_intent(tx,self.principal_a,
                    context_id=UUID(ctx["context_id"]),client_intent_id=uuid4(),
                    actor="alice",from_account="A",to_account="B",amount=str(n+1))
                ops.append(UUID(op["operation_id"]))
            for op in ops[:6]:
                self.assertTrue(bf.submit_intent(tx,self.principal_a,
                              operation_id=op)["created"])
            bf.mark_uncertain(tx,self.principal_a,operation_id=ops[0])
            with self.assertRaisesRegex(bf.BankingDenied,"Submit rate"):
                bf.submit_intent(tx,self.principal_a,operation_id=ops[6])
        with transaction(self.db) as tx:
            self.assertEqual(tx.execute(
                "SELECT phase FROM metadata.banking_operations WHERE operation_id=%s",
                (ops[0],)).fetchone()[0],"UNKNOWN")
            self.assertEqual(tx.execute(
                "SELECT phase FROM metadata.banking_operations WHERE operation_id=%s",
                (ops[6],)).fetchone()[0],"ACCEPTED")
            self.assertEqual(tx.execute(
                "SELECT count(*) FROM metadata.banking_attempts WHERE operation_id=ANY(%s)",
                (ops,)).fetchone()[0],6)
