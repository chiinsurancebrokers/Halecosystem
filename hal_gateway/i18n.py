"""Bilingual (EL/EN) strings. Wording of the fairness lines follows the Ashlar HAL fairness rules."""
from __future__ import annotations

Lang = str  # "el" | "en"

_S: dict[str, dict[str, str]] = {
    "broker_review": {
        "en": "A licensed Ashlar broker reviews every recommendation before anything is placed.",
        "el": "Ένας αδειοδοτημένος broker της Ashlar ελέγχει κάθε πρόταση πριν τοποθετηθεί οτιδήποτε.",
    },
    "wording_prevails": {
        "en": "Benefit summaries are simplified from the insurer's Table of Benefits; the policy wording prevails. "
              "This is not an offer of cover. Final eligibility, terms and premium are confirmed by the insurer "
              "after your application and underwriting.",
        "el": "Οι περιλήψεις παροχών απλοποιούν τον Πίνακα Παροχών του ασφαλιστή· υπερισχύει το κείμενο του "
              "συμβολαίου. Δεν αποτελεί προσφορά κάλυψης. Η τελική επιλεξιμότητα, οι όροι και το ασφάλιστρο "
              "επιβεβαιώνονται από τον ασφαλιστή μετά την αίτηση και την αξιολόγηση κινδύνου.",
    },
    "premium_from_tables": {
        "en": "Premiums come from official rate tables, never invented by AI.",
        "el": "Τα ασφάλιστρα προέρχονται από επίσημους πίνακες τιμολόγησης, ποτέ από εκτίμηση του AI.",
    },
    "action_pending": {
        "en": "I prepared this request. It has not been carried out: your broker must approve it first (reference {ref}).",
        "el": "Ετοίμασα το αίτημα. Δεν έχει εκτελεστεί: πρέπει πρώτα να το εγκρίνει ο broker σας (αριθμός {ref}).",
    },
    "action_approved": {
        "en": "Approved and carried out (reference {ref}).",
        "el": "Εγκρίθηκε και εκτελέστηκε (αριθμός {ref}).",
    },
    "action_rejected": {
        "en": "Not approved (reference {ref}). Reason: {reason}",
        "el": "Δεν εγκρίθηκε (αριθμός {ref}). Αιτιολογία: {reason}",
    },
    "denied": {
        "en": "This action is not available for your role.",
        "el": "Η ενέργεια δεν είναι διαθέσιμη για τον ρόλο σας.",
    },
    "no_verified_price": {
        "en": "I can't show a verified price for this profile. Your broker will quote it personally.",
        "el": "Δεν μπορώ να δείξω επαληθευμένη τιμή για αυτό το προφίλ. Θα την υπολογίσει προσωπικά ο broker σας.",
    },
    "travel_not_health": {
        "en": "Travel insurance covers trips. It is not a substitute for ongoing health cover.",
        "el": "Η ταξιδιωτική ασφάλιση καλύπτει ταξίδια. Δεν αντικαθιστά τη διαρκή ασφάλιση υγείας.",
    },
}


def t(key: str, lang: Lang = "el", **kw: object) -> str:
    entry = _S[key]
    text = entry.get(lang) or entry["en"]
    return text.format(**kw) if kw else text


def normalize_lang(lang: str | None) -> Lang:
    return "en" if (lang or "").lower().startswith("en") else "el"
