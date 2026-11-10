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

## Send for signature (any PDF)
`hal_gateway/signing.py` + `signing_app.py`: staff upload a PDF (e.g. an insurer's own form), mark the signature box
(page + rectangle in PDF points) and send the client a one-time link. The client signs on a phone page (EL/EN); the signature
image is stamped into that exact page. Token stored hashed, single use, expiry, revocable; originals and signed copies hashed;
audit trail. Gateway tool: `request_signature` (staff only). This is a SIMPLE electronic signature: confirm acceptance with the
insurer for each form. Run the pages: `pip install .[signing] && uvicorn hal_gateway.signing_app:app`
(set HAL_PUBLIC_URL, HAL_SIGN_DB, HAL_AUDIT_SALT; the default DB is in-memory, use a persistent path in production).

## Run the tests
```
pip install pytest && python -m pytest -q
```

## Status
See `STATUS.md`. Roadmap and the comparison with Allstate's announced assistant: `docs/ROADMAP.md`.
