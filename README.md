# Halecosystem

Bilingual (Greek / English) agentic layer for Ashlar Assurance. One gateway serves **clients**, **brokers/agents**,
**back office** and a customer's **own AI assistant** (via MCP). Hal prepares and explains; a licensed broker approves.

```
client chat | broker console | back office | external assistant (MCP)
                        \         |          /
                       hal_gateway  (roles, tools, propose -> approve, audit, fairness guard, EL/EN)
                        /          |           \
        portal (Postgres)   ashlar-hal-3 engine   Proposal Studio
        clients/policies    official rate tables  proposal prefill
```

## Principles (enforced in code and tests, not in prompts)
1. Prices only from the deterministic engine / official tables. An empty result is an honest answer. No interpolation.
2. Writes never execute directly: they become PENDING proposals; staff with access to that client approve or reject.
3. Client-bound principals (client, external assistant) can only ever touch their own client, whatever arguments say.
4. Every denial, proposal and decision is in an append-only audit log.
5. Every customer-facing quote carries the broker-review and wording-prevails lines in the user's language.
6. No urgency or scare copy; travel is never presented as health cover.

## Run the tests
```
pip install pytest && python -m pytest -q
```

## Status
See `STATUS.md`. Roadmap and the comparison with Allstate's announced assistant: `docs/ROADMAP.md`.
