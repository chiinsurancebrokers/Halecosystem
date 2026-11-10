# Inventory of copies and what to do with each (2026-11-10)

Basis: repo names and dates, READMEs, Railway/Netlify metadata. Only the rows marked **inspected** were read in code.
"Proposal" is a recommendation, not a decision. Nothing here has been changed, archived or deleted.
Before retiring anything, confirm nothing still calls it (check Railway HTTP logs and the callers listed under "Verify").

## A. Hal engine (health and travel quotes)
| Item | Where | What it is | Proposal | Verify first |
|---|---|---|---|---|
| ashlar-hal-3 | private repo; Railway "Ashlar-aggregator" prod, domain hal.ashlarassurance.com (deployed 7 Nov) | Current Hal, deterministic engine + Claude explainer. **inspected** | **KEEP: canonical** | none |
| adviser-os (+ staging env), test-smtp-caller | Railway "Ashlar-aggregator" | Staging/side services | Keep staging; confirm whether test-smtp-caller can go | what each does |
| ashlar-hal-2 | public repo (Sep) | Previous version, hal-3 README says it was a rebuild after an audit of it | Archive | nothing deployed from it |
| HAL, halrailway | private + public repos (Jun) | Early Streamlit/FastAPI Hal; halrailway is a 374-line public quote API. **halrailway inspected** | Retire after caller check | none |
| "hal the brain" web | Railway, halinsurance.up.railway.app (deployed 14 Jun) | Old Streamlit Hal, probably the caller of portal `/api/hal/stats` | Retire, after repointing any caller to hal-3 | who calls portal `/api/hal/stats` |
| quote prototypes: -ashlar-insurance-quote-engine, chi_quote_engine, quote_creator, chi-quote-demo-app, travel-engine, insurance-comparator, insureai, legacy-shield-calculator | public repos (Oct 2025 - Aug 2026) | Earlier quote tools | Archive; harvest rate tables only if not already in hal-3 | rate tables unique to them |

## B. Proposals and offers
| Item | Where | What it is | Proposal | Verify first |
|---|---|---|---|---|
| Ashlar-Proposal-Studio | public repo (make private); Railway 4 services; pushed 9 Nov | Proposal/analysis service with API, HAL prefill bridge, family-mix. **inspected** | **KEEP: canonical proposal service** | confirm what optimistic-elegance and just-reprieve are (likely worker/web) |
| commercial-proposal | public repo; Railway commercial-api/web/worker (16 Oct) | Diverged older fork of Proposal Studio. **inspected** | Merge into Proposal Studio, or keep only if it serves commercial (non-health) lines; if kept, rename and make private | is it used for commercial lines? who uses commercial-web |
| Offer-Builder | public repo; Railway (offer-builder.up.railway.app) | Professional-indemnity offers for architects/engineers, Supabase login. **inspected** | Keep for now; fold into BrokerOs proposal module later | none |
| policyanalyzer | public repo; Railway 2 services | Policy analysis API called by Proposal Studio. **inspected** | **KEEP** (called via POLICY_ANALYZER_API_URL) | none |

## C. Portal
| Item | Where | What it is | Proposal | Verify first |
|---|---|---|---|---|
| portal (chi_portal_v2) | private repo; Railway portal + Postgres | Agent/client/back-office portal, 85 routes. **inspected** | **KEEP: canonical** (PR #3 pending) | none |
| chi-insurance-portal | public repo (May); Railway "chi insurance portal" (Dec 2025) | Earlier portal | Archive, retire project | no users still log in there; data already in portal DB |
| totikidis-plan-portal, carolinatotikidis | Railway project + private repo | One family's case site | Keep private; retire when the case closes | client consent and retention |
| oiasforum, oias-forum-cigna-guide, cigna-envoy-member-guide | private repo; 2 Railway projects | Cigna member guides/forum | Out of Hal scope; keep as is | none |

## D. Netlify (21 public static sites, no passwords)
| Site | Proposal |
|---|---|
| aitisiasfalisisipyros (home application), astikiefthini (restaurant liability) | Keep; move into BrokerOs form engine (STATUS step 5) |
| chiinsurancebrokers-travelinsurance, -travel-quotation, levantetravelenginquote, chiinsurancebrokers-arrowhellas | Merge into one travel-quote tool (BrokerOs step 4) |
| ashlar-insurance, aineedsanalyzer | Check purpose; likely marketing or early analyzer |
| panteliskourbelas-chiinsurancebrokers, kiraainurse | Named after individuals: inspect content, protect or remove |
| akropolis84 (x5 incl. library variants), tzoker, etfwatcher, admirable-llama-77c098, verdant-kashata-69dab2, dancing-gecko-48d5b0, stirring-beignet-0efef6, myakropolis84 | Not Hal. Review separately |

## E. Not part of the Hal ecosystem
Pet-insurance line (kira*, petainurse*, petquoteengine, petsaihealth, Vet*Bench), astro-forecast, tzoker/kino, smartmoney, evcharger/enerwave, puglia, tektoniko-gala, aicarrentalai, carisnpectpro, stylescan, english-daily-dialogues, EV and lottery apps. Decide separately; excluded from consolidation.

## Order of work
1. Settle A and B decisions (retire halinsurance after repointing callers; decide commercial-proposal).
2. Apply the security PRs (portal #3, Proposal Studio #18, commercial-proposal #1) with env vars first.
3. Then build adapters in hal_gateway against only the canonical services: ashlar-hal-3, Proposal Studio, portal.
