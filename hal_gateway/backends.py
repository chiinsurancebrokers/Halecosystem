"""Ports to the existing systems. The gateway never talks to a database or a carrier directly:
  - PolicyBackend  -> portal (Postgres, source of truth for clients/policies)
  - QuoteBackend   -> ashlar-hal-3 deterministic engine (the ONLY source of prices)
  - ProposalBackend-> Ashlar Proposal Studio (prefill handoff)
Adapters for the live services go in hal_gateway/adapters/ ; InMemory* fakes are for tests and demos."""
from __future__ import annotations

from typing import Any, Protocol

from .scopes import Principal, Role


class PolicyBackend(Protocol):
    def can_access_client(self, principal: Principal, client_id: int) -> bool: ...
    def policies_of(self, client_id: int) -> list[dict[str, Any]]: ...
    def create_ticket(self, client_id: int, subject: str, body: str, source: str) -> dict[str, Any]: ...
    def queue_renewal_email(self, client_id: int, policy_id: int, lang: str) -> dict[str, Any]: ...


class QuoteBackend(Protocol):
    def quote(self, facts: dict[str, Any]) -> dict[str, Any]:
        """Returns {"plans":[{"plan_key","insurer","annual_premium_eur","source_table"}], "excluded":[...]} .
        Premiums MUST come from official rate tables. An empty plans list is a valid, honest answer."""


class ProposalBackend(Protocol):
    def prefill(self, client_id: int, facts: dict[str, Any]) -> dict[str, Any]: ...


class InMemoryPolicyBackend:
    def __init__(self, policies: dict[int, list[dict[str, Any]]], agent_books: dict[str, set[int]]) -> None:
        self.policies, self.agent_books = policies, agent_books
        self.tickets: list[dict[str, Any]] = []
        self.emails: list[dict[str, Any]] = []

    def can_access_client(self, principal: Principal, client_id: int) -> bool:
        if principal.role is Role.BACKOFFICE:
            return True
        if principal.role is Role.AGENT:
            if principal.agent_code is None:  # head-office agent sees everything (matches portal HalScope)
                return True
            return client_id in self.agent_books.get(principal.agent_code, set())
        return principal.client_id == client_id

    def policies_of(self, client_id: int) -> list[dict[str, Any]]:
        return list(self.policies.get(client_id, []))

    def create_ticket(self, client_id: int, subject: str, body: str, source: str) -> dict[str, Any]:
        t = {"id": len(self.tickets) + 1, "client_id": client_id, "subject": subject, "body": body, "source": source}
        self.tickets.append(t)
        return t

    def queue_renewal_email(self, client_id: int, policy_id: int, lang: str) -> dict[str, Any]:
        e = {"client_id": client_id, "policy_id": policy_id, "lang": lang, "status": "queued"}
        self.emails.append(e)
        return e


class InMemoryQuoteBackend:
    def __init__(self, table: dict[tuple[str, int], float]) -> None:
        self.table = table  # (insurer, age) -> annual premium from an "official" table

    def quote(self, facts: dict[str, Any]) -> dict[str, Any]:
        age = int(facts["age"])
        plans = [{"plan_key": f"{ins}:{age}", "insurer": ins, "annual_premium_eur": prem, "source_table": "official-2026"}
                 for (ins, a), prem in self.table.items() if a == age]
        return {"plans": plans, "excluded": []}  # never interpolates between ages (rule 1)


class InMemoryProposalBackend:
    def __init__(self) -> None:
        self.prefills: list[dict[str, Any]] = []

    def prefill(self, client_id: int, facts: dict[str, Any]) -> dict[str, Any]:
        self.prefills.append({"client_id": client_id, "facts": facts})
        return {"status": "prefilled", "case_reference": f"CASE-{len(self.prefills)}"}
