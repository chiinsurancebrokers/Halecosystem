"""Propose -> approve -> execute, with an append-only audit log.

Rule 2 of the HAL fairness rules in code: nothing that changes a client's situation is executed because an AI
(or a client, or an external assistant) asked. It is stored as a PENDING proposal; a licensed staff member who
has access to that client approves or rejects it; only then does the handler run.
"""
from __future__ import annotations

import json
import sqlite3
import time
import uuid
from dataclasses import dataclass
from typing import Any, Callable, Protocol

from .i18n import Lang, t
from .scopes import Principal, Role

PENDING, APPROVED, REJECTED, FAILED = "pending", "approved", "rejected", "failed"


class AccessChecker(Protocol):
    def can_access_client(self, principal: Principal, client_id: int) -> bool: ...


class NotAllowed(PermissionError):
    pass


@dataclass
class Proposal:
    id: str
    action: str
    client_id: int
    payload: dict[str, Any]
    status: str
    proposed_by: str
    proposed_role: str
    decided_by: str | None = None
    reason: str | None = None
    result: dict[str, Any] | None = None


_SCHEMA = """
CREATE TABLE IF NOT EXISTS proposals(
  id TEXT PRIMARY KEY, action TEXT NOT NULL, client_id INTEGER NOT NULL, payload TEXT NOT NULL,
  status TEXT NOT NULL, proposed_by TEXT NOT NULL, proposed_role TEXT NOT NULL,
  decided_by TEXT, reason TEXT, result TEXT, created_at REAL NOT NULL, decided_at REAL);
CREATE TABLE IF NOT EXISTS audit_log(
  seq INTEGER PRIMARY KEY AUTOINCREMENT, ts REAL NOT NULL, actor TEXT NOT NULL, role TEXT NOT NULL,
  event TEXT NOT NULL, proposal_id TEXT, detail TEXT);
"""


class ActionStore:
    """SQLite for the reference implementation; the same two tables port directly to Postgres."""

    def __init__(self, access: AccessChecker, path: str = ":memory:") -> None:
        self.db = sqlite3.connect(path, check_same_thread=False)
        self.db.executescript(_SCHEMA)
        self.access = access
        self.handlers: dict[str, Callable[[Proposal], dict[str, Any]]] = {}

    # -- audit -------------------------------------------------------------
    def _audit(self, p: Principal, event: str, proposal_id: str | None, detail: Any = None) -> None:
        self.db.execute(
            "INSERT INTO audit_log(ts,actor,role,event,proposal_id,detail) VALUES(?,?,?,?,?,?)",
            (time.time(), p.subject, p.role.value, event, proposal_id, json.dumps(detail, ensure_ascii=False, default=str)),
        )
        self.db.commit()

    def audit_log(self) -> list[dict[str, Any]]:
        cur = self.db.execute("SELECT seq,ts,actor,role,event,proposal_id,detail FROM audit_log ORDER BY seq")
        return [dict(zip(("seq", "ts", "actor", "role", "event", "proposal_id", "detail"), r)) for r in cur]

    # -- lifecycle ---------------------------------------------------------
    def propose(self, who: Principal, action: str, client_id: int, payload: dict[str, Any]) -> Proposal:
        who.validate()
        if who.role in (Role.CLIENT, Role.EXTERNAL_AGENT) and who.client_id != client_id:
            self._audit(who, "denied_propose", None, {"action": action, "client_id": client_id})
            raise NotAllowed("cannot act for another client")
        if who.is_staff and not self.access.can_access_client(who, client_id):
            self._audit(who, "denied_propose", None, {"action": action, "client_id": client_id})
            raise NotAllowed("client is outside your book")
        pid = uuid.uuid4().hex[:12]
        self.db.execute(
            "INSERT INTO proposals(id,action,client_id,payload,status,proposed_by,proposed_role,created_at) VALUES(?,?,?,?,?,?,?,?)",
            (pid, action, client_id, json.dumps(payload, ensure_ascii=False, default=str), PENDING, who.subject, who.role.value, time.time()),
        )
        self.db.commit()
        self._audit(who, "proposed", pid, {"action": action, "client_id": client_id})
        return self.get(pid)

    def get(self, pid: str) -> Proposal:
        r = self.db.execute(
            "SELECT id,action,client_id,payload,status,proposed_by,proposed_role,decided_by,reason,result FROM proposals WHERE id=?",
            (pid,),
        ).fetchone()
        if not r:
            raise KeyError(pid)
        return Proposal(r[0], r[1], r[2], json.loads(r[3]), r[4], r[5], r[6], r[7], r[8], json.loads(r[9]) if r[9] else None)

    def pending_for(self, who: Principal) -> list[Proposal]:
        if not who.is_staff:
            raise NotAllowed("staff only")
        rows = self.db.execute("SELECT id FROM proposals WHERE status=? ORDER BY created_at", (PENDING,)).fetchall()
        return [p for p in (self.get(r[0]) for r in rows) if self.access.can_access_client(who, p.client_id)]

    def _decide_guard(self, who: Principal, p: Proposal) -> None:
        if not who.is_staff:
            self._audit(who, "denied_decide", p.id)
            raise NotAllowed("only licensed staff can approve or reject")
        if p.status != PENDING:
            raise NotAllowed(f"proposal already {p.status}")
        if not self.access.can_access_client(who, p.client_id):
            self._audit(who, "denied_decide", p.id)
            raise NotAllowed("client is outside your book")

    def approve(self, who: Principal, pid: str, lang: Lang = "el") -> tuple[Proposal, str]:
        p = self.get(pid)
        self._decide_guard(who, p)
        handler = self.handlers.get(p.action)
        status, result = APPROVED, None
        try:
            if handler is None:
                raise LookupError(f"no handler for {p.action}")
            result = handler(p)
        except Exception as exc:  # execution failure must not look like success
            status, result = FAILED, {"error": str(exc)}
        self.db.execute(
            "UPDATE proposals SET status=?, decided_by=?, result=?, decided_at=? WHERE id=?",
            (status, who.subject, json.dumps(result, ensure_ascii=False, default=str), time.time(), pid),
        )
        self.db.commit()
        self._audit(who, status, pid, result)
        return self.get(pid), t("action_approved", lang, ref=pid) if status == APPROVED else str(result)

    def reject(self, who: Principal, pid: str, reason: str, lang: Lang = "el") -> tuple[Proposal, str]:
        p = self.get(pid)
        self._decide_guard(who, p)
        self.db.execute("UPDATE proposals SET status=?, decided_by=?, reason=?, decided_at=? WHERE id=?",
                        (REJECTED, who.subject, reason, time.time(), pid))
        self.db.commit()
        self._audit(who, REJECTED, pid, {"reason": reason})
        return self.get(pid), t("action_rejected", lang, ref=pid, reason=reason)
