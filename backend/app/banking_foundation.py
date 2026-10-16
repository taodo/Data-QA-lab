"""U5-F inert platform banking registry. No signer, transport, or public routes.

Only authenticated platform sessions may create a binding; no bank SQLite,
actor token, bank password, or mTLS address is accessible from this module.
"""
from __future__ import annotations

import hashlib
import json
import re
import secrets
from dataclasses import dataclass
from uuid import UUID, uuid4

CAPABILITY = "OFF"
CONTRACT = "BIC-1.1-producer-baseline"
MAX_MONEY = 2**63 - 1
_MONEY = re.compile(r"[1-9][0-9]*\Z")
_IDENT = re.compile(r"[A-Za-z0-9._:-]{1,128}\Z")
_HEX32 = re.compile(r"[0-9a-f]{32}\Z")

class BankingDenied(ValueError):
    """Fail-closed banking foundation (not an HTTP error mapping)."""


def money_to_domain(value: str, *, limit: int = MAX_MONEY) -> int:
    if type(value) is not str or len(value) > 19 or not _MONEY.fullmatch(value):
        raise BankingDenied("Invalid canonical money")
    amount = int(value)
    if type(limit) is not int or not 1 <= limit <= MAX_MONEY or amount > limit:
        raise BankingDenied("Out of range money")
    return amount


def canonical_request(attributes: dict) -> tuple[str, str]:
    """Exact B2 Request serialization, strict wire fields, no floats/bools."""
    keys = {"handle","epoch","actor","authorization_revision","binding_ref",
            "request_id","operation","operation_id","payload","key","recovery"}
    if type(attributes) is not dict or set(attributes) != keys:
        raise BankingDenied("Invalid frozen request")
    for key in ("handle","epoch","actor","binding_ref","request_id","operation","operation_id"):
        if type(attributes[key]) is not str or not _IDENT.fullmatch(attributes[key]):
            raise BankingDenied("Invalid request identity")
    if not _HEX32.fullmatch(attributes["handle"]) or not _HEX32.fullmatch(attributes["epoch"]):
        raise BankingDenied("Invalid private context")
    if type(attributes["authorization_revision"]) is not int or attributes["authorization_revision"] <= 0:
        raise BankingDenied("Invalid authorization revision")
    if type(attributes["recovery"]) is not bool or attributes["recovery"]:
        raise BankingDenied("New acceptance cannot be a recovery")
    if type(attributes["key"]) is not str or not _IDENT.fullmatch(attributes["key"]):
        raise BankingDenied("Invalid bank key")
    if attributes["operation"] != "transfers.create":
        raise BankingDenied("Not an accepted write operation")
    payload = attributes["payload"]
    if type(payload) is not dict or set(payload) != {"from_account","to_account","amount"}:
        raise BankingDenied("Invalid transfer payload")
    if any(type(payload[k]) is not str or not _IDENT.fullmatch(payload[k])
           for k in ("from_account", "to_account")):
        raise BankingDenied("Invalid account")
    if payload["from_account"] == payload["to_account"]:
        raise BankingDenied("Self transfer forbidden")
    if type(payload["amount"]) is not int or not 1 <= payload["amount"] <= MAX_MONEY:
        raise BankingDenied("Invalid numeric payload")
    # Python B2: json.dumps(..., sort_keys=True, separators=(',', ':'),
    # ensure_ascii=True, allow_nan=False). UTF-8 of this representation is ASCII.
    wire = json.dumps(attributes, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True, allow_nan=False)
    return wire, hashlib.sha256(wire.encode("utf-8")).hexdigest()


def parse_json_exact(raw: bytes) -> dict:
    def unique(pairs):
        value = {}
        for k, v in pairs:
            if k in value:
                raise BankingDenied("Duplicate JSON key")
            value[k] = v
        return value
    def invalid(_):
        raise BankingDenied("Non-integer JSON")
    if type(raw) is not bytes or len(raw) > 8192:
        raise BankingDenied("Invalid bounded payload")
    try:
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=unique,
                           parse_float=invalid, parse_constant=invalid)
    except (UnicodeError, ValueError, TypeError) as exc:
        raise BankingDenied("Invalid JSON") from exc
    if type(value) is not dict:
        raise BankingDenied("Expected object")
    return value


def _session(connection, principal: dict):
    """Authoritative active session check, not trust in stale request claims."""
    if type(principal) is not dict or not isinstance(principal.get("token_hash"), str):
        raise BankingDenied("Authenticated session required")
    session = connection.execute(
        """SELECT s.user_id FROM metadata.account_sessions s
           JOIN metadata.accounts a ON a.user_id=s.user_id
           LEFT JOIN metadata.public_demo_accounts p ON p.user_id=a.user_id
           WHERE s.token_hash=%s AND s.expires_at>NOW() AND a.active
             AND (p.user_id IS NULL OR p.enabled)
           FOR UPDATE OF s""", (principal["token_hash"],)).fetchone()
    if not session or str(session[0]) != str(principal.get("user_id")):
        raise BankingDenied("Session expired or foreign")
    return session[0]


def binding_for_session(connection, principal: dict) -> str:
    """Return an existing opaque session binding or create one atomically."""
    owner = _session(connection, principal)
    hash_value = principal["token_hash"]
    row = connection.execute(
        "SELECT binding_ref,state FROM metadata.banking_bindings WHERE session_hash=%s FOR UPDATE",
        (hash_value,)).fetchone()
    if row:
        if row[1] != "ACTIVE":
            raise BankingDenied("Banking session fenced")
        return row[0]
    binding = secrets.token_urlsafe(32)
    connection.execute(
        """INSERT INTO metadata.banking_bindings(binding_ref,session_hash,user_id)
           VALUES (%s,%s,%s)""", (binding, hash_value, owner))
    return binding


def reserve_context(connection, principal: dict, allocation_intent_id: UUID) -> dict:
    if type(allocation_intent_id) is not UUID:
        raise BankingDenied("Invalid allocation intent")
    binding = binding_for_session(connection, principal)
    existing = connection.execute(
        """SELECT context_id,state FROM metadata.banking_contexts
           WHERE binding_ref=%s AND allocation_intent_id=%s FOR UPDATE""",
        (binding,allocation_intent_id)).fetchone()
    if existing:
        return {"context_id":str(existing[0]),"state":existing[1],"created":False}
    row = connection.execute(
        """SELECT COUNT(*), COUNT(*) FILTER (
             WHERE state IN ('RESERVED','ACTIVE','DRAINING','RECOVERY_HOLD'))
           FROM metadata.banking_contexts WHERE binding_ref=%s""",
        (binding,)).fetchone()
    if row[0] >= 100:
        raise BankingDenied("Context retention budget reached")
    if row[1]:
        raise BankingDenied("One live context per session")
    context_id = uuid4()
    connection.execute(
        """INSERT INTO metadata.banking_contexts
           (context_id,binding_ref,allocation_intent_id,state)
           VALUES (%s,%s,%s,'RESERVED')""", (context_id,binding,allocation_intent_id))
    return {"context_id":str(context_id),"state":"RESERVED","created":True}


def attach_private_context(connection, principal: dict, context_id: UUID,
                           *, context_ref: str, epoch: str, revision: int):
    """Operator/test-only data-plane acknowledgement; no network access."""
    if type(context_id) is not UUID or not all(
         type(s) is str and _HEX32.fullmatch(s) for s in (context_ref,epoch)):
        raise BankingDenied("Invalid private context")
    if type(revision) is not int or revision <= 0:
        raise BankingDenied("Invalid epoch revision")
    binding = binding_for_session(connection, principal)
    result = connection.execute(
        """UPDATE metadata.banking_contexts SET
             context_ref=%s,context_epoch=%s,authorization_revision=%s,state='ACTIVE'
           WHERE binding_ref=%s AND context_id=%s AND state='RESERVED'
           RETURNING context_id""",
        (context_ref,epoch,revision,binding,context_id)).fetchone()
    if not result:
        raise BankingDenied("Allocation already consumed or foreign")


def accept_intent(connection, principal: dict, *, context_id: UUID,
                  client_intent_id: UUID, actor: str, from_account: str,
                  to_account: str, amount: str, limit: int = MAX_MONEY) -> dict:
    if type(context_id) is not UUID or type(client_intent_id) is not UUID:
        raise BankingDenied("Invalid intent UUID")
    if any(type(k) is not str or not _IDENT.fullmatch(k)
           for k in (actor,from_account,to_account)):
        raise BankingDenied("Invalid actor or account")
    domain_amount = money_to_domain(amount,limit=limit)
    binding = binding_for_session(connection, principal)
    ctx = connection.execute(
        """SELECT context_ref,context_epoch,authorization_revision,state
           FROM metadata.banking_contexts WHERE context_id=%s AND binding_ref=%s FOR UPDATE""",
        (context_id,binding)).fetchone()
    if not ctx or ctx[3] != "ACTIVE" or ctx[0] is None or ctx[1] is None:
        raise BankingDenied("Context not provisioned")
    prior = connection.execute(
        """SELECT operation_id,frozen_request,phase FROM metadata.banking_operations
           WHERE binding_ref=%s AND client_intent_id=%s FOR UPDATE""",
        (binding,client_intent_id)).fetchone()
    if prior:
        saved=prior[1]
        payload=saved["payload"]
        if (saved["actor"] != actor or payload["from_account"] != from_account or
                payload["to_account"] != to_account or payload["amount"] != domain_amount or
                saved["handle"] != ctx[0] or saved["epoch"] != ctx[1]):
            raise BankingDenied("Immutable acceptance conflict")
        return {"operation_id":str(prior[0]),"phase":prior[2],"created":False}
    count=connection.execute(
        """SELECT COUNT(*) FROM metadata.banking_operations
           WHERE binding_ref=%s""",(binding,)).fetchone()[0]
    if count>=100:
        raise BankingDenied("Intent capacity reached; no eviction")
    operation_id=uuid4()
    request_id="attempt-"+secrets.token_hex(16)
    key="bank-"+secrets.token_hex(16)
    frozen={"handle":ctx[0],"epoch":ctx[1],"actor":actor,
            "authorization_revision":ctx[2],"binding_ref":binding,
            "request_id":request_id,"operation":"transfers.create",
            "operation_id":str(operation_id),"payload":{
                "from_account":from_account,"to_account":to_account,"amount":domain_amount},
            "key":key,"recovery":False}
    _,digest=canonical_request(frozen)
    connection.execute(
        """INSERT INTO metadata.banking_operations
           (operation_id,binding_ref,context_id,client_intent_id,actor_id,
            request_id,idempotency_key,producer_context_ref,producer_context_epoch,
            authorization_revision,frozen_request,request_digest)
           VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
        (operation_id,binding,context_id,client_intent_id,actor,request_id,key,
         ctx[0],ctx[1],ctx[2],json.dumps(frozen),digest))
    return {"operation_id":str(operation_id),"phase":"ACCEPTED","created":True}


def submit_intent(connection, principal: dict, *, operation_id: UUID) -> dict:
    """Commit SUBMITTING before any future transport. Never sends a request."""
    if type(operation_id) is not UUID:
        raise BankingDenied("Invalid operation ID")
    binding=binding_for_session(connection,principal)
    row=connection.execute(
        """SELECT phase,request_digest FROM metadata.banking_operations
           WHERE binding_ref=%s AND operation_id=%s FOR UPDATE""",
        (binding,operation_id)).fetchone()
    if not row:
        raise BankingDenied("Foreign operation")
    if row[0] != "ACCEPTED":
        return {"operation_id":str(operation_id),"phase":row[0],"created":False}
    connection.execute(
        """UPDATE metadata.banking_operations
           SET phase='SUBMITTING',submitted_at=NOW()
           WHERE operation_id=%s AND phase='ACCEPTED'""",(operation_id,))
    connection.execute(
        """INSERT INTO metadata.banking_attempts
           (attempt_id,operation_id,attempt_number,state) VALUES (%s,%s,1,'SUBMITTING')""",
        (uuid4(),operation_id))
    return {"operation_id":str(operation_id),"phase":"SUBMITTING","created":True}


def mark_uncertain(connection, principal: dict, *, operation_id: UUID) -> None:
    """A missing producer response cannot clear previously uncertain execution."""
    binding=binding_for_session(connection,principal)
    row=connection.execute(
        """UPDATE metadata.banking_operations SET phase='UNKNOWN',outcome='INCONCLUSIVE'
           WHERE operation_id=%s AND binding_ref=%s
             AND phase IN ('SUBMITTING','UNKNOWN') RETURNING operation_id""",
        (operation_id,binding)).fetchone()
    if not row:
        raise BankingDenied("Operation not in submitted uncertainty window")
    connection.execute(
        """UPDATE metadata.banking_attempts SET state='UNKNOWN'
           WHERE operation_id=%s AND state='SUBMITTING'""",(operation_id,))


def fence_session(connection, session_hash: str) -> None:
    """Operator/session lifecycle fence preserves UNKNOWN and queues revocation."""
    if type(session_hash) is not str or len(session_hash)!=64:
        raise BankingDenied("Invalid session identity")
    rows=connection.execute(
        """UPDATE metadata.banking_bindings SET state='FENCED'
           WHERE session_hash=%s AND state='ACTIVE' RETURNING binding_ref""",
        (session_hash,)).fetchall()
    for (binding,) in rows:
        # A persisted submit may have reached the private producer even if
        # logout/expiry interrupts its response. Never settle it as failed.
        connection.execute(
            """UPDATE metadata.banking_operations
               SET phase='UNKNOWN',outcome='INCONCLUSIVE'
               WHERE binding_ref=%s AND phase='SUBMITTING'""",(binding,))
        connection.execute(
            """UPDATE metadata.banking_attempts SET state='UNKNOWN'
               WHERE operation_id IN
                 (SELECT operation_id FROM metadata.banking_operations
                  WHERE binding_ref=%s AND phase='UNKNOWN')
                 AND state='SUBMITTING'""",(binding,))
        contexts=connection.execute(
            """SELECT context_id FROM metadata.banking_contexts
               WHERE binding_ref=%s AND state IN ('RESERVED','ACTIVE','DRAINING','RECOVERY_HOLD')""",
            (binding,)).fetchall()
        for (context_id,) in contexts:
            connection.execute(
                """INSERT INTO metadata.banking_revocation_outbox
                   (revocation_id,binding_ref,context_id) VALUES (%s,%s,%s)""",
                (uuid4(),binding,context_id))
        connection.execute(
            """UPDATE metadata.banking_contexts SET state='RECOVERY_HOLD'
               WHERE binding_ref=%s AND state IN ('RESERVED','ACTIVE','DRAINING')""",
            (binding,))



def fence_orphaned_bindings(connection) -> int:
    """Operator-only/scheduled maintenance for expired or deleted sessions.

    No network, deletion or operator key use. Must run periodically before
    revocation delivery is considered fresh; foundation alone has no scheduler.
    """
    rows=connection.execute(
        """SELECT b.session_hash FROM metadata.banking_bindings b
           LEFT JOIN metadata.account_sessions s
             ON s.token_hash=b.session_hash
           LEFT JOIN metadata.accounts a ON a.user_id=b.user_id
           LEFT JOIN metadata.public_demo_accounts p ON p.user_id=b.user_id
           WHERE b.state='ACTIVE' AND
             (s.token_hash IS NULL OR s.expires_at<=NOW() OR NOT a.active
              OR (p.user_id IS NOT NULL AND NOT p.enabled))
           ORDER BY b.created_at,b.binding_ref
           FOR UPDATE OF b""").fetchall()
    for (session_hash,) in rows:
        fence_session(connection,session_hash)
    return len(rows)
