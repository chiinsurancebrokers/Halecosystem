# Halecosystem: context for any Claude session

## Mission
Make Hal the first bilingual (Greek/English) agentic insurance ecosystem in Greece, serving BOTH the client and the
broker/agent, matching and surpassing what Allstate has announced. Owner: Chris Iatropoulos, Ashlar Assurance.

## What Allstate has announced (Insurance Journal, Chad Hemenway, 6 Nov 2026; plus a Greek trade article)
- A consumer Personal Agentic Assistant (PAA) is due early 2027, in development for over a year; the CEO, Tom Wilson, says the
  base technology exists and the algorithms are being tested (said on the Q3 earnings call with analysts).
- It runs on ALLIE (Allstate Large Language Intelligent Ecosystem). Ask Allstate, a customer-service agent, is already live.
- It acts for the customer, not just answers. It will also work with consumers' existing PAAs (Muse was named).
- Stated aim: fewer clicks, reach people who do not want to call an agent or use the website, and give context on a customer's
  coverage needs. Wilson: "marketing to machines and people", with a protection-expert PAA of its own.
- Context: personal-lines new business is up 125% over 2019, split roughly evenly between exclusive agents, independent agents
  and direct-to-consumer. Q3 net income fell about 45% on catastrophe losses.
- Privacy, cybersecurity and regulators: the CEO said they will work these out as they go. Market speed is called unclear.
Treat the above as announced intent only. Do not claim details of the product that are not public.

## Where Hal can be stronger (design stance)
- Regulation, privacy and security are built in from day one, not retrofitted (see below).
- Independent broker across carriers, with a licensed human approving every action, versus a single-carrier assistant.
- Greek-first plus English; Greek market context (public health system is a real option).
- Interoperable: expose Hal to customers' own assistants through MCP (hal_gateway/mcp_server.py), the counterpart of Allstate
  working with other PAAs.
- Fewer clicks for clients too: the assistant prepares, the broker approves in one step.

## Non-negotiables (enforced in code and tests, see README)
Prices only from official tables; writes are proposals approved by licensed staff; client-bound principals only reach their own
data; audit log; fairness footer on every quote; no urgency or scare copy. Full wording: the anthropic-skills:hal-fairness-rules skill.

## Working rules
- Fixes to other repos (portal, ashlar-hal-3, Ashlar-Proposal-Studio) go on a branch with a PR. Never push to their main or
  redeploy Railway/Netlify without the owner's approval. Never read or print secret values.
- Real client data must never enter git. Use synthetic data.
- Read STATUS.md first; it lists what is done, next and open findings.
