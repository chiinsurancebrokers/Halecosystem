"""MCP server so a customer's OWN AI assistant (or the broker's) can use Hal - the 'serve machines as well as people' door.

Run:  HAL_TOKENS_FILE=tokens.json python -m hal_gateway.mcp_server      (needs: pip install halecosystem[mcp])

tokens.json maps SHA-256(token) -> principal, so raw tokens are never stored:
  {"<sha256 hex>": {"role": "external_agent", "client_id": 42, "subject": "token:maria-assistant"}}
The assistant sends its token once per session via the HAL_TOKEN environment variable of the MCP client config.
External assistants can only ever read their own client and PROPOSE actions; a broker still approves (see actions.py).
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
from typing import Any

from .scopes import Principal, Role


def load_principals(path: str) -> dict[str, Principal]:
    raw = json.load(open(path, encoding="utf-8"))
    out = {}
    for digest, spec in raw.items():
        p = Principal(Role(spec["role"]), client_id=spec.get("client_id"), agent_code=spec.get("agent_code"), subject=spec.get("subject", ""))
        p.validate()
        out[digest.lower()] = p
    return out


def authenticate(token: str, principals: dict[str, Principal]) -> Principal | None:
    digest = hashlib.sha256(token.encode()).hexdigest()
    for known, principal in principals.items():  # constant-time compare against every entry
        if hmac.compare_digest(known, digest):
            return principal
    return None


def build_server(gateway: Any, principals: dict[str, Principal]):  # pragma: no cover - needs the optional mcp package
    from mcp.server.fastmcp import FastMCP

    who = authenticate(os.environ.get("HAL_TOKEN", ""), principals)
    if who is None:
        raise SystemExit("HAL_TOKEN missing or unknown")
    server = FastMCP("hal")

    for spec in gateway.specs(who, "en"):
        name = spec["name"]

        def make(n: str):
            def tool(arguments: dict[str, Any] | None = None, lang: str = "el") -> dict[str, Any]:
                return gateway.call(who, n, arguments or {}, lang)
            tool.__name__ = n
            tool.__doc__ = spec["description"] + (" Creates a proposal that a licensed broker must approve." if spec["writes"] else "")
            return tool

        server.tool()(make(name))
    return server
