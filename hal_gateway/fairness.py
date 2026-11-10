"""Mechanical guard for the HAL fairness rules (no scare tactics, no invented prices, mandatory disclaimers).
Run on every customer-facing text the gateway returns."""
from __future__ import annotations

import re

from .i18n import Lang, t

# Rule 5: no urgency / scare. Patterns are deliberately simple and bilingual.
_URGENCY = [
    r"\bonly\s+\d+\s+(spots?|places?)\s+left\b",
    r"\bprices?\s+(are\s+)?going\s+up\s+(next|this)\s+week\b",
    r"\blast\s+chance\b",
    r"\bact\s+now\b",
    r"\bhurry\b",
    r"μόνο\s+\d+\s+θέσεις?",
    r"τελευταία\s+ευκαιρία",
    r"τελευταίες\s+θέσεις",
    r"οι\s+τιμές\s+ανεβαίνουν\s+(την\s+επόμενη|αυτή)\s+εβδομάδα",
    r"βιαστείτε",
]
# Rule 3/9: never imply public care is worse.
_DISPARAGE = [r"public\s+hospitals?\s+(are|is)\s+(bad|unsafe|dangerous)", r"τα\s+δημόσια\s+νοσοκομεία\s+είναι\s+(κακά|επικίνδυνα)"]
# Rule 4: never promise pre-existing conditions are covered.
_PROMISE = [r"covers?\s+all\s+pre-?existing", r"καλύπτει\s+όλες\s+τις\s+προϋπάρχουσες"]


class FairnessViolation(ValueError):
    pass


def violations(text: str) -> list[str]:
    found = []
    for group, pats in (("urgency", _URGENCY), ("disparage_public", _DISPARAGE), ("preexisting_promise", _PROMISE)):
        for p in pats:
            if re.search(p, text, flags=re.IGNORECASE):
                found.append(group)
                break
    return found


def check(text: str) -> str:
    bad = violations(text)
    if bad:
        raise FairnessViolation(f"text violates fairness rules: {', '.join(bad)}")
    return text


def with_quote_footer(text: str, lang: Lang) -> str:
    """Rules 1, 2, 10: every quote output carries the broker-review line and the wording-prevails line."""
    return "\n\n".join([check(text), t("premium_from_tables", lang), t("broker_review", lang), t("wording_prevails", lang)])
