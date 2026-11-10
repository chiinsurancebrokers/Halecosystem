# Roadmap and comparison with Allstate

Source for Allstate: a Greek-language trade article (Nov 2026) reporting the CEO's remarks to analysts. It says Allstate is
building a Personal Agentic Assistant (launch expected early 2027) that carries out insurance transactions for customers,
sits on its ALLIE AI ecosystem, can work with customers' own AI assistants, and that privacy, cyber-security and regulation
questions are still open. Nothing else about it is public to us, so the table compares **announced intent**, not a product.

| Capability | Allstate (announced) | Hal today | Hal target |
|---|---|---|---|
| Acts for the customer | Yes (goal) | Read-only chat + forms | Propose -> broker approves -> executes |
| Works with customers' own AI assistants | Yes (stated) | No | MCP server, scoped hashed tokens (built, unwired) |
| Languages | English | EL + EN chat, voice | EL + EN everywhere incl. broker tools |
| Human licensed intermediary in the loop | Not described | Broker reviews all placement | Enforced in code, audited |
| Prices | Not described | Deterministic official tables | Same; no interpolation, ever |
| Data isolation | Open question per CEO | Per-role scope in portal HAL | Server-built principals, tested |
| Insurers | Single carrier (own) | 1 priced (Morgan Price) | Multi-carrier, only once verified |

## Where Hal can be better, honestly
- Independent broker advice across carriers, which a captive carrier cannot offer.
- Auditable human approval on every action.
- Greek-first language and market knowledge (public system as a real option, Rule 3).

## Where Hal is behind
- One priced carrier; no claims or payments; the two Hal systems are not yet joined; no live external-assistant onboarding.

## Phases
1. Foundations (done): gateway, approval, audit, fairness, MCP auth.
2. Join the systems: adapters + broker inbox + portal chat on the gateway.
3. Open the door: MCP service + "connect my assistant" for clients.
4. Breadth: second carrier, renewals, claims intake, documents.
5. Productise: fold into BrokerOs as the multi-tenant layer.
