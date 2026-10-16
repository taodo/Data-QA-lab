"""Non-deployable U5-F fake private consumer: no HTTP, TLS, signing or bank writes.

Pure deterministic fixture contract checker. Never import in production module.
Its results are *untrusted simulations*, never financial proof or assessment.
"""
from __future__ import annotations
from dataclasses import dataclass
import json
from backend.app.banking_foundation import BankingDenied, canonical_request, money_to_domain

EXPECTED_FIELDS = frozenset({"iss","aud","sub","service_id","jti","iat","nbf","exp",
 "context_ref","context_epoch","actor_id","authorization_revision",
 "binding_ref","scope","request_id","request_digest","operation","operation_id"})
JOSE_HEADER = {"alg":"ES256","typ":"banking+jwt","kid":"current"}


def check_fixture_grant(header: dict, claims: dict, request: dict, *,
                        source_issuer="https://platform.example.invalid",
                        audience="minibanking-private", service="data-qa-lab-u5") -> None:
    """Structural fake: NOT cryptographic verification. Used for negative matrices."""
    if type(header) is not dict or header != JOSE_HEADER:
        raise BankingDenied("Fixture JOSE header mismatch")
    if type(claims) is not dict or set(claims) != EXPECTED_FIELDS:
        raise BankingDenied("Fixture grant claims mismatch")
    if any(type(claims[x]) is not str for x in
           ("iss","aud","sub","service_id","jti","context_ref","context_epoch",
            "actor_id","binding_ref","scope","request_id","request_digest","operation","operation_id")):
        raise BankingDenied("Fixture wrong grant type")
    if ((claims["iss"],claims["aud"],claims["sub"],claims["service_id"]) !=
        (source_issuer,audience,service,service)):
        raise BankingDenied("Wrong pinned service identity")
    if claims["scope"] != "dispatch":
        raise BankingDenied("Wrong scope")
    if any(type(claims[n]) is not int for n in
           ("iat","nbf","exp","authorization_revision")):
        raise BankingDenied("Wrong integer claim")
    if not (0 < claims["exp"]-claims["iat"] <= 30 and
            claims["nbf"] == claims["iat"] and
            claims["authorization_revision"] > 0):
        raise BankingDenied("Invalid grant lifetime/revision")
    _, digest = canonical_request(request)
    expected={"context_ref":"handle","context_epoch":"epoch","actor_id":"actor",
              "authorization_revision":"authorization_revision","binding_ref":"binding_ref",
              "request_id":"request_id","operation":"operation","operation_id":"operation_id"}
    if any(claims[k] != request[v] for k,v in expected.items()):
        raise BankingDenied("Fixture request identity mismatch")
    if claims["request_digest"] != digest:
        raise BankingDenied("Fixture tampered body or digest")


def interpret_producer(outer: int | None, envelope: dict | None, *,
                       submitted: bool, previous: str = "INCONCLUSIVE") -> tuple[str,str]:
    """(execution, outcome), always preserves prior uncertainty conservatively."""
    if previous not in {"INCONCLUSIVE","MATCHING_COMMIT","NO_COMMIT_PROVEN"}:
        raise BankingDenied("Unrecognized prior outcome")
    if type(submitted) is not bool or type(outer) not in (int,type(None)):
        raise BankingDenied("Malformed fake transport")
    if not submitted:
        if outer is not None or envelope is not None:
            raise BankingDenied("Response before SUBMIT is impossible")
        return "NOT_RUN","INCONCLUSIVE"
    if outer is None:
        if envelope is not None:
            raise BankingDenied("Untrusted response without HTTP status")
        return "UNKNOWN",previous if previous=="MATCHING_COMMIT" else "INCONCLUSIVE"
    if outer in (202,401,403,422,429,500,503,504):
        # A subsequent HTTP error must never erase previous UNKNOWN/commit.
        return "UNKNOWN",previous if previous=="MATCHING_COMMIT" else "INCONCLUSIVE"
    if outer != 200:
        raise BankingDenied("Unknown private producer status")
    if type(envelope) is not dict or set(envelope) != {"response","stored"}:
        raise BankingDenied("Malformed private envelope")
    if type(envelope["stored"]) is not bool or type(envelope["response"]) is not dict:
        raise BankingDenied("Malformed private stored receipt")
    response=envelope["response"]
    if set(response) != {"status","body"} or type(response["status"]) is not int or type(response["body"]) is not dict:
        raise BankingDenied("Malformed nested bank response")
    status=response["status"]
    if status in (200,201):
        body=response["body"]
        fields={"transfer_id","from_account","to_account","amount","currency","status","created_at"}
        if set(body)!=fields or body["status"]!="SUCCESS" or body["currency"]!="VND":
            raise BankingDenied("Malformed transfer receipt")
        if any(type(body[k]) is not str or not body[k] for k in
               ("transfer_id","from_account","to_account","created_at")):
            raise BankingDenied("Invalid nested transfer identity")
        if type(body["amount"]) is not int or not 1 <= body["amount"] <= 2**63-1:
            raise BankingDenied("Unsafe bank amount")
        # A producer receipt is an observation, NOT independent SQL evidence.
        return "OBSERVED","INCONCLUSIVE"
    if status in (404,409,422,503):
        if set(response["body"])!={"error"} or type(response["body"]["error"]) is not dict:
            raise BankingDenied("Malformed bank error")
        err=response["body"]["error"]
        if type(err.get("code")) is not str or not err["code"]:
            raise BankingDenied("Invalid error code")
        return "UNKNOWN" if status==503 else "OBSERVED","INCONCLUSIVE"
    raise BankingDenied("Unexpected nested bank status")


@dataclass
class FakeU5Consumer:
    """Bounded fake state machine; no producer transport or side effects."""
    accepted: bool = False
    submitted: bool = False
    outcome: str = "INCONCLUSIVE"
    execution: str = "NOT_RUN"
    dispatches: int = 0
    frozen_identity: str | None = None

    def accept(self, request: dict):
        wire,_=canonical_request(request)
        if self.accepted and self.frozen_identity != wire:
            raise BankingDenied("Immutable acceptance conflict")
        self.accepted=True
        self.frozen_identity=wire

    def submit(self):
        if not self.accepted:
            raise BankingDenied("SUBMIT requires durable ACCEPT")
        if not self.submitted:
            self.submitted=True
            self.dispatches+=1

    def observe(self, http: int | None, envelope: dict | None):
        execution,outcome=interpret_producer(http,envelope,submitted=self.submitted,previous=self.outcome)
        self.execution,self.outcome=execution,outcome
        return execution,outcome
