# STATUS (2026-11-10)

## Done
- `hal_gateway`: roles/principals, tool registry (5 tools), propose->approve->execute with audit log (SQLite reference),
  EL/EN strings, fairness guard, MCP server with hashed-token auth, in-memory backends. 19 tests.
- Security audit of `portal` -> PR https://github.com/chiinsurancebrokers/portal/pull/3 (not deployed).
- Security audit of Ashlar-Proposal-Studio -> PR https://github.com/chiinsurancebrokers/Ashlar-Proposal-Studio/pull/18 (job API was open when ASHLAR_INTERNAL_API_KEY unset; set it on BOTH api and web services before deploy).
- Audited with no blocking findings: ashlar-hal-3 (fail-closed admin/followup tokens, allowlisted document proxy, 5-try DOB lockout, host allowlist) and Offer-Builder (DB-enforced lockout, no secrets in repo).
- Railway: hal, portal and proposal-studio projects all report SUCCESS deployments (read-only check).

## Next (in order)
1. Adapters in `hal_gateway/adapters/`: portal (Postgres, read + ticket/email queue), ashlar-hal-3 `/quotes` API, Proposal Studio prefill.
2. Broker console: pending-proposals inbox in the portal (approve / reject with reason), client-side status view.
3. Wire portal client chat (`/client/hal/chat`) and agent chat to `Gateway.call` instead of read-only tools.
4. Deploy the MCP server as a Railway service; token issuing screen for clients ("connect my assistant").
5. Second insurer with verified rates; renewal/claims-intake tools; document request tool.

## Open findings not fixed (need a decision)
- Portal: no CSRF tokens; new users get a shared default password; `client_required` only checks login, not role.
- Portal PR needs env vars set before deploy: `SECRET_KEY`, `HAL_STATS_KEY` (Streamlit HAL callers must send it).
- PRIVACY: the PUBLIC repo Ashlar-Proposal-Studio contains a real family's names and health-plan prices (HANDOFF.md + 4 test/code files). Make the repo private (git history keeps the data otherwise) and replace with synthetic data.
- ashlar-hal-3 CORS is `*` (no credentials, acceptable) and its rate limiter is per-instance memory (move to Redis if scaled out).
- 'hal the brain' production deployment is dated 2026-06-14 while ashlar-hal-3 was last pushed 2026-11-07: confirm which service serves hal.ashlarassurance.com.
- Not audited: Netlify sites, Railway logs/variables (values deliberately not read), the 3 Streamlit apps other than Proposal Studio/Offer-Builder.

## Out of scope for now
Payments, binding cover online, claims automation, mobile apps.
