"""Principals and roles. Every call into the gateway is made by a Principal that the
SERVER built from a verified session/token - never from request payloads."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Role(str, Enum):
    CLIENT = "client"                  # a policyholder in the portal
    AGENT = "agent"                    # licensed broker/agent, sees own book only
    BACKOFFICE = "backoffice"          # sees whole book, can approve
    EXTERNAL_AGENT = "external_agent"  # a customer's own AI assistant acting on delegated, scoped consent


STAFF = {Role.AGENT, Role.BACKOFFICE}


@dataclass(frozen=True)
class Principal:
    role: Role
    client_id: int | None = None      # CLIENT and EXTERNAL_AGENT: the one client they act for
    agent_code: str | None = None     # AGENT: book filter. None for BACKOFFICE.
    subject: str = ""                 # user email / token id, for the audit log

    @property
    def is_staff(self) -> bool:
        return self.role in STAFF

    def validate(self) -> None:
        if self.role in (Role.CLIENT, Role.EXTERNAL_AGENT) and self.client_id is None:
            raise ValueError("client-bound principal requires client_id")
