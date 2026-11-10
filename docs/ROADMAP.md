# Roadmap and comparison with Allstate

Sources for Allstate: Insurance Journal (6 Nov 2026, earnings-call remarks by CEO Tom Wilson) and a Greek trade article. Full
summary in `CLAUDE.md`. Allstate's assistant is announced for early 2027, so the table compares **announced intent**, not a
shipped product.

| Capability | Allstate (announced) | Hal today | Hal target |
|---|---|---|---|
| Acts for the customer | Yes (goal) | Read-only chat + forms | Propose -> broker approves -> executes |
| Works with customers' own AI assistants | Yes (stated) | No | MCP server, scoped hashed tokens (built, unwired) |
| Languages | English | EL + EN chat, voice | EL + EN everywhere incl. broker tools |
| Human licensed intermediary in the loop | Not described | Broker reviews all placement | Enforced in code, audited |
| Prices | Not described | Deterministic official tables | Same; no interpolation, ever |
| Data isolation | Open question per CEO | Per-role scope in portal HAL | Server-built principals, tested |
| Insurers | Single carrier (own) | 1 priced (Morgan Price) | Multi-carrier, only once verified |
| Interop with other assistants | Will work with existing PAAs (e.g. Muse) | None | MCP server (built, not wired); test against real assistants |
| Regulation, privacy, cyber | "Figure it out as we go" (CEO) | Fail-closed keys, per-role scope | Designed in; audit log, consent, DPIA before launch |
| Fewer clicks | Stated goal | Multi-step forms | Assistant prefills, broker approves in one step |
| Distribution | Exclusive + independent agents + direct, roughly equal | Independent broker | Broker-led, client self-service, assistant-to-assistant |

## Where Hal can be better, honestly
- Independent broker advice across carriers, which a captive carrier cannot offer.
- Auditable human approval on every action.
- Greek-first language and market knowledge (public system as a real option, Rule 3).

## Where Hal is behind
- One priced carrier; no claims or payments; the two Hal systems are not yet joined; no live external-assistant onboarding.

## Strategic reading of the Allstate news
- The market signal that matters: an insurer now says it is "marketing to machines". Customers' own assistants will shop and
  transact, so Hal must be easy for a machine to use correctly (MCP, structured quotes, clear consent) as well as for people.
- Allstate leans on direct and agent channels; an independent broker's edge is cross-carrier advice a captive cannot give.
- Risk to manage: assistants acting for customers raise authority, consent and liability questions the CEO has deferred. Hal
  should answer them first (scoped tokens, per-action broker approval, audit log) and make that a selling point.

## Phases
1. Foundations (done): gateway, approval, audit, fairness, MCP auth.
2. Join the systems: adapters + broker inbox + portal chat on the gateway.
3. Open the door: MCP service + "connect my assistant" for clients.
4. Breadth: second carrier, renewals, claims intake, documents.
5. Productise: fold into BrokerOs as the multi-tenant layer.
