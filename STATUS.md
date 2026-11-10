# STATUS (2026-11-10)

## Done
- `hal_gateway`: roles/principals, tool registry (5 tools), propose->approve->execute with audit log (SQLite reference),
  EL/EN strings, fairness guard, MCP server with hashed-token auth, in-memory backends. 19 tests.
- Security audit of `portal` -> PR https://github.com/chiinsurancebrokers/portal/pull/3 (not deployed).
- Security audit of Ashlar-Proposal-Studio -> PR https://github.com/chiinsurancebrokers/Ashlar-Proposal-Studio/pull/18 (job API was open when ASHLAR_INTERNAL_API_KEY unset; set it on BOTH api and web services before deploy).
- Audited with no blocking findings: ashlar-hal-3 (fail-closed admin/followup tokens, allowlisted document proxy, 5-try DOB lockout, host allowlist) and Offer-Builder (DB-enforced lockout, no secrets in repo).
- Railway: hal, portal and proposal-studio projects all report SUCCESS deployments (read-only check).
- Step-5 audit (Netlify + remaining apps), 2026-11-10:
  - commercial-proposal (public repo, live as commercial-api/web/worker): same fail-open `ASHLAR_INTERNAL_API_KEY` bug -> PR https://github.com/chiinsurancebrokers/commercial-proposal/pull/1 . It is an older diverged FORK of Proposal Studio (15k lines).
  - policyanalyzer API: fail-closed + constant-time, no findings. halrailway: tiny public quote API, no secrets.
  - hal.ashlarassurance.com is served by `ashlar-hal-3` in project **Ashlar-aggregator** (deployed 2026-11-07). `halinsurance.up.railway.app` is the OLD Streamlit HAL in project 'hal the brain' (deployed 2026-06-14): probable caller of portal `/api/hal/stats` (needs HAL_STATS_KEY).
  - Netlify: 21 public static sites, none password-protected, forms disabled. Some are named after individual clients (panteliskourbelas-..., kiraainurse, aitisiasfalisisipyros) and several are unrelated experiments (akropolis84 x5, tzoker, etfwatcher). Contents not inspected.

## Consolidation (consequence of the audit)
The same logic exists in several diverged copies (Proposal Studio vs commercial-proposal; HAL v2/v3, halrailway, hal-the-brain; 3 travel-quote Netlify sites). Every copy needs its own security fixes. Target: ONE quote engine (ashlar-hal-3), ONE proposal service, ONE portal, all behind hal_gateway; retire the rest after confirming nothing calls them.

- Send-for-signature module (signing.py, signing_app.py, `request_signature` tool) with 9 tests; dry-run on a real insurer form placed the
  signature correctly. Not deployed. Needs: persistent storage (Postgres/Supabase instead of SQLite BLOBs), notification email to the broker
  on signing, a broker UI to pick the signature box, and insurer confirmation that e-signature is accepted on their forms.

## Next (in order)
0. Retire or protect legacy copies (see Consolidation); confirm what calls `halinsurance.up.railway.app` first.
1. Adapters in `hal_gateway/adapters/`: portal (Postgres, read + ticket/email queue), ashlar-hal-3 `/quotes` API, Proposal Studio prefill.
2. Broker console: pending-proposals inbox in the portal (approve / reject with reason), client-side status view.
3. Wire portal client chat (`/client/hal/chat`) and agent chat to `Gateway.call` instead of read-only tools.
4. Deploy the MCP server as a Railway service; token issuing screen for clients ("connect my assistant").
5. Second insurer with verified rates; renewal/claims-intake tools; document request tool.

## Open findings not fixed (need a decision)
- Portal: no CSRF tokens; new users get a shared default password; `client_required` only checks login, not role.
- Portal PR needs env vars set before deploy: `SECRET_KEY`, `HAL_STATS_KEY` (Streamlit HAL callers must send it).
- PRIVACY: the PUBLIC repos Ashlar-Proposal-Studio and commercial-proposal contain a real family's names and health-plan prices (HANDOFF.md + 4 test/code files). Make the repo private (git history keeps the data otherwise) and replace with synthetic data.
- ashlar-hal-3 CORS is `*` (no credentials, acceptable) and its rate limiter is per-instance memory (move to Redis if scaled out).
- `commercial-proposal/.mcp.json` exposes a Supabase project ref (not a secret, but identifies the project).
- Not audited: Netlify site contents, Railway logs/variables (values deliberately not read), the adviser-os and test-smtp-caller services.

## Out of scope for now
Payments, binding cover online, claims automation, mobile apps.
