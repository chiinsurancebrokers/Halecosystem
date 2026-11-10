# STATUS (2026-11-10)

## Done
- `hal_gateway`: roles/principals, tool registry (5 tools), propose->approve->execute with audit log (SQLite reference),
  EL/EN strings, fairness guard, MCP server with hashed-token auth, in-memory backends. 19 tests.
- Security audit of `portal` -> PR https://github.com/chiinsurancebrokers/portal/pull/3 (not deployed).

## Next (in order)
1. Adapters in `hal_gateway/adapters/`: portal (Postgres, read + ticket/email queue), ashlar-hal-3 `/quotes` API, Proposal Studio prefill.
2. Broker console: pending-proposals inbox in the portal (approve / reject with reason), client-side status view.
3. Wire portal client chat (`/client/hal/chat`) and agent chat to `Gateway.call` instead of read-only tools.
4. Deploy the MCP server as a Railway service; token issuing screen for clients ("connect my assistant").
5. Second insurer with verified rates; renewal/claims-intake tools; document request tool.

## Open findings not fixed (need a decision)
- Portal: no CSRF tokens; new users get a shared default password; `client_required` only checks login, not role.
- Portal PR needs env vars set before deploy: `SECRET_KEY`, `HAL_STATS_KEY` (Streamlit HAL callers must send it).
- Not yet audited: Ashlar-Proposal-Studio, Offer-Builder, ashlar-hal-3 (CORS `*`, follow-up runner secret), Railway/Netlify logs.

## Out of scope for now
Payments, binding cover online, claims automation, mobile apps.
