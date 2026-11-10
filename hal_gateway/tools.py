"""Tool registry. One definition serves the web chat, the client portal, the broker console and the MCP server.

Security rules enforced here, not in prompts:
  * client-bound principals (CLIENT, EXTERNAL_AGENT): client_id is taken from the Principal; any client_id in the
    arguments is ignored, so a model or a forged payload cannot reach another client's data.
  * WRITE tools never execute. They create a PENDING proposal for a licensed broker (actions.ActionStore).
  * quote output always passes the fairness footer; empty price list => honest 'no verified price' message.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from . import fairness
from .actions import ActionStore, NotAllowed
from .backends import PolicyBackend, ProposalBackend, QuoteBackend
from .i18n import Lang, normalize_lang, t
from .scopes import Principal, Role

ALL = set(Role)
CLIENT_SIDE = {Role.CLIENT, Role.EXTERNAL_AGENT}
STAFF_ONLY = {Role.AGENT, Role.BACKOFFICE}


@dataclass
class Tool:
    name: str
    description: dict[str, str]  # {"en":..., "el":...}
    roles: set[Role]
    writes: bool
    run: Callable[[Principal, dict[str, Any], Lang], dict[str, Any]]


class Gateway:
    def __init__(self, policies: PolicyBackend, quotes: QuoteBackend, proposals: ProposalBackend, store: ActionStore) -> None:
        self.policies, self.quotes, self.proposals, self.store = policies, quotes, proposals, store
        self.tools: dict[str, Tool] = {}
        self._register()
        # approved write actions are executed by these handlers, and only after staff approval
        store.handlers.update({
            "open_ticket": lambda p: self.policies.create_ticket(p.client_id, p.payload["subject"], p.payload["body"], p.proposed_role),
            "draft_renewal": lambda p: self.policies.queue_renewal_email(p.client_id, int(p.payload["policy_id"]), p.payload.get("lang", "el")),
            "prepare_proposal": lambda p: self.proposals.prefill(p.client_id, p.payload["facts"]),
        })

    # -- helpers -----------------------------------------------------------
    def _client_id(self, who: Principal, args: dict[str, Any]) -> int:
        if who.role in CLIENT_SIDE:
            return int(who.client_id)  # type: ignore[arg-type]  - arguments are ignored on purpose
        if "client_id" not in args:
            raise ValueError("client_id required")
        cid = int(args["client_id"])
        if not self.policies.can_access_client(who, cid):
            raise NotAllowed("client is outside your book")
        return cid

    def _propose(self, who: Principal, action: str, args: dict[str, Any], payload: dict[str, Any], lang: Lang) -> dict[str, Any]:
        cid = self._client_id(who, args)
        prop = self.store.propose(who, action, cid, payload)
        return {"status": "pending_broker_approval", "reference": prop.id, "message": t("action_pending", lang, ref=prop.id)}

    # -- registry ----------------------------------------------------------
    def _add(self, name: str, en: str, el: str, roles: set[Role], writes: bool, run: Callable[..., dict[str, Any]]) -> None:
        self.tools[name] = Tool(name, {"en": en, "el": el}, roles, writes, run)

    def _register(self) -> None:
        def get_my_policies(who: Principal, args: dict[str, Any], lang: Lang) -> dict[str, Any]:
            return {"policies": self.policies.policies_of(self._client_id(who, args))}

        def quote_health_travel(who: Principal, args: dict[str, Any], lang: Lang) -> dict[str, Any]:
            facts = {k: args[k] for k in ("age", "country", "coverage_area", "kind") if k in args}
            kind = facts.get("kind", "health")
            res = self.quotes.quote(facts)
            plans = res.get("plans", [])
            if not plans:
                text = t("no_verified_price", lang)
            else:
                lines = [f"- {p['insurer']}: €{p['annual_premium_eur']:.2f}/yr ({p['source_table']})" for p in plans]
                text = "\n".join(lines)
            if kind == "travel":
                text += "\n\n" + t("travel_not_health", lang)
            return {"plans": plans, "excluded": res.get("excluded", []), "text": fairness.with_quote_footer(text, lang)}

        def open_ticket(who: Principal, args: dict[str, Any], lang: Lang) -> dict[str, Any]:
            return self._propose(who, "open_ticket", args, {"subject": str(args["subject"])[:200], "body": str(args.get("body", ""))[:4000]}, lang)

        def draft_renewal(who: Principal, args: dict[str, Any], lang: Lang) -> dict[str, Any]:
            cid = self._client_id(who, args)
            pid = int(args["policy_id"])
            if pid not in {int(p["id"]) for p in self.policies.policies_of(cid)}:
                raise NotAllowed("policy does not belong to this client")
            return self._propose(who, "draft_renewal", args, {"policy_id": pid, "lang": lang}, lang)

        def prepare_proposal(who: Principal, args: dict[str, Any], lang: Lang) -> dict[str, Any]:
            return self._propose(who, "prepare_proposal", args, {"facts": dict(args.get("facts", {}))}, lang)

        self._add("get_my_policies", "List the policies of the client.", "Λίστα συμβολαίων του πελάτη.", ALL, False, get_my_policies)
        self._add("quote_health_travel", "Indicative shortlist from official rate tables.", "Ενδεικτική λίστα από επίσημους πίνακες τιμών.", ALL, False, quote_health_travel)
        self._add("open_ticket", "Ask the broker for a change or help (needs broker approval).", "Αίτημα προς τον broker (απαιτεί έγκριση).", ALL, True, open_ticket)
        self._add("draft_renewal", "Prepare a renewal email for a policy (needs broker approval).", "Ετοιμασία email ανανέωσης (απαιτεί έγκριση).", ALL, True, draft_renewal)
        self._add("prepare_proposal", "Prefill a proposal case in Proposal Studio (needs broker approval).", "Προσυμπλήρωση πρότασης στο Proposal Studio (απαιτεί έγκριση).", ALL, True, prepare_proposal)

    def specs(self, who: Principal, lang: str = "el") -> list[dict[str, Any]]:
        lang = normalize_lang(lang)
        return [{"name": x.name, "description": x.description[lang], "writes": x.writes}
                for x in self.tools.values() if who.role in x.roles]

    def call(self, who: Principal, name: str, args: dict[str, Any] | None = None, lang: str = "el") -> dict[str, Any]:
        who.validate()
        lang = normalize_lang(lang)
        tool = self.tools.get(name)
        if tool is None or who.role not in tool.roles:
            self.store._audit(who, "denied_tool", None, {"tool": name})
            raise NotAllowed(t("denied", lang))
        out = tool.run(who, args or {}, lang)
        self.store._audit(who, "tool_call", None, {"tool": name, "writes": tool.writes})
        return out
