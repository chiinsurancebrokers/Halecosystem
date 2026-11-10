"""Send-for-signature: a broker uploads ANY PDF (e.g. an insurer's own application form), marks the signature box,
and the client signs it from a one-time link on their phone. The signature image is stamped into that exact PDF.

Design
  * The link token is 256-bit random and only its SHA-256 is stored; the raw token exists only in the returned link.
  * One use, expiry (default 7 days), revocable. Signing is an atomic status flip, so a double submit cannot sign twice.
  * The original and the signed document are both kept with their SHA-256, plus an audit trail (time, hashed IP, user agent,
    consent text shown). The signed PDF also gets a small visible footer line with time and document hash.
  * Staff-only creation. Clients (and external assistants) can never create or read requests.

Legal note: this produces a SIMPLE electronic signature (drawn image + audit trail). Whether a given insurer accepts it on its
own form must be confirmed with that insurer; it is not a qualified electronic signature.
"""
from __future__ import annotations

import hashlib
import hmac
import secrets
import sqlite3
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from .i18n import Lang
from .scopes import Principal

try:  # PyMuPDF; optional dependency: pip install halecosystem[signing]
    import pymupdf as fitz  # type: ignore
except ImportError:  # pragma: no cover
    import fitz  # type: ignore

MAX_SIGNATURE_BYTES = 300_000
MAX_PDF_BYTES = 25 * 1024 * 1024

CONSENT = {
    "el": "Έχω διαβάσει το έγγραφο και συμφωνώ να το υπογράψω ηλεκτρονικά.",
    "en": "I have read the document and agree to sign it electronically.",
}


class SigningError(Exception):
    """Client-safe error (bad token, expired, already signed, invalid input)."""


def _sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


_SCHEMA = """
CREATE TABLE IF NOT EXISTS sign_requests(
  id TEXT PRIMARY KEY, token_hash TEXT UNIQUE NOT NULL, status TEXT NOT NULL,
  title TEXT NOT NULL, signer_name TEXT NOT NULL, lang TEXT NOT NULL,
  page INTEGER NOT NULL, x0 REAL, y0 REAL, x1 REAL, y1 REAL,
  original BLOB NOT NULL, original_sha TEXT NOT NULL, signed BLOB, signed_sha TEXT,
  created_by TEXT NOT NULL, created_at REAL NOT NULL, expires_at REAL NOT NULL,
  signed_at REAL, ip_hash TEXT, user_agent TEXT, consent_text TEXT);
CREATE TABLE IF NOT EXISTS sign_events(
  seq INTEGER PRIMARY KEY AUTOINCREMENT, ts REAL NOT NULL, request_id TEXT NOT NULL, event TEXT NOT NULL, detail TEXT);
"""


@dataclass
class SigningView:
    id: str
    title: str
    signer_name: str
    lang: str
    page: int
    page_count: int
    expires_at: float


class SigningService:
    def __init__(self, path: str = ":memory:", audit_secret: str = "", base_url: str = "https://example.invalid") -> None:
        self.db = sqlite3.connect(path, check_same_thread=False)
        self.db.executescript(_SCHEMA)
        self.audit_secret = (audit_secret or secrets.token_hex(16)).encode()
        self.base_url = base_url.rstrip("/")

    # -- staff side --------------------------------------------------------
    def create(self, who: Principal, pdf: bytes, *, title: str, signer_name: str, page: int,
               rect: tuple[float, float, float, float], lang: Lang = "el", ttl_days: float = 7) -> dict[str, Any]:
        if not who.is_staff:
            raise PermissionError("only licensed staff can request signatures")
        if len(pdf) > MAX_PDF_BYTES or not pdf.startswith(b"%PDF"):
            raise SigningError("invalid PDF")
        try:
            doc = fitz.open(stream=pdf, filetype="pdf")
        except Exception as exc:
            raise SigningError("unreadable PDF") from exc
        if not (1 <= page <= doc.page_count):
            raise SigningError("page out of range")
        x0, y0, x1, y1 = rect
        pr = doc[page - 1].rect
        if not (0 <= x0 < x1 <= pr.width and 0 <= y0 < y1 <= pr.height):
            raise SigningError("signature box outside the page")
        rid, token = secrets.token_hex(6), secrets.token_urlsafe(32)
        now = time.time()
        self.db.execute(
            "INSERT INTO sign_requests(id,token_hash,status,title,signer_name,lang,page,x0,y0,x1,y1,original,original_sha,created_by,created_at,expires_at)"
            " VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (rid, _sha(token.encode()), "pending", title[:200], signer_name[:200], lang if lang in CONSENT else "el", page,
             x0, y0, x1, y1, pdf, _sha(pdf), who.subject, now, now + ttl_days * 86400))
        self._event(rid, "created", {"by": who.subject, "page": page})
        return {"id": rid, "link": f"{self.base_url}/s/{token}", "expires_at": now + ttl_days * 86400, "document_sha256": _sha(pdf)}

    def revoke(self, who: Principal, rid: str) -> None:
        if not who.is_staff:
            raise PermissionError("staff only")
        cur = self.db.execute("UPDATE sign_requests SET status='revoked' WHERE id=? AND status='pending'", (rid,))
        self.db.commit()
        if cur.rowcount:
            self._event(rid, "revoked", {"by": who.subject})

    def status(self, who: Principal, rid: str) -> dict[str, Any]:
        if not who.is_staff:
            raise PermissionError("staff only")
        r = self.db.execute("SELECT status,signed_at,original_sha,signed_sha,expires_at FROM sign_requests WHERE id=?", (rid,)).fetchone()
        if not r:
            raise KeyError(rid)
        status = "expired" if r[0] == "pending" and r[4] < time.time() else r[0]
        return {"status": status, "signed_at": r[1], "original_sha256": r[2], "signed_sha256": r[3]}

    def signed_pdf(self, who: Principal, rid: str) -> bytes:
        if not who.is_staff:
            raise PermissionError("staff only")
        r = self.db.execute("SELECT signed FROM sign_requests WHERE id=? AND status='signed'", (rid,)).fetchone()
        if not r:
            raise SigningError("not signed")
        return bytes(r[0])

    def events(self, rid: str) -> list[dict[str, Any]]:
        cur = self.db.execute("SELECT ts,event,detail FROM sign_events WHERE request_id=? ORDER BY seq", (rid,))
        return [{"ts": a, "event": b, "detail": c} for a, b, c in cur]

    # -- client side (token holder) ----------------------------------------
    def _row(self, token: str):
        r = self.db.execute(
            "SELECT id,status,title,signer_name,lang,page,x0,y0,x1,y1,original,expires_at FROM sign_requests WHERE token_hash=?",
            (_sha((token or "").encode()),)).fetchone()
        if not r:
            raise SigningError("invalid link")
        if r[1] == "signed":
            raise SigningError("already signed")
        if r[1] != "pending":
            raise SigningError("link no longer valid")
        if r[11] < time.time():
            raise SigningError("link expired")
        return r

    def view(self, token: str) -> SigningView:
        r = self._row(token)
        n = fitz.open(stream=bytes(r[10]), filetype="pdf").page_count
        return SigningView(r[0], r[2], r[3], r[4], r[5], n, r[11])

    def original_pdf(self, token: str) -> bytes:
        return bytes(self._row(token)[10])

    def page_png(self, token: str, zoom: float = 1.6) -> bytes:
        r = self._row(token)
        page = fitz.open(stream=bytes(r[10]), filetype="pdf")[r[5] - 1]
        return page.get_pixmap(matrix=fitz.Matrix(zoom, zoom)).tobytes("png")

    def sign(self, token: str, signature_png: bytes, consent: bool, *, ip: str = "", user_agent: str = "") -> dict[str, Any]:
        r = self._row(token)
        rid, lang = r[0], r[4]
        if not consent:
            raise SigningError("consent required")
        if not signature_png or len(signature_png) > MAX_SIGNATURE_BYTES:
            raise SigningError("invalid signature image")
        try:
            pix = fitz.Pixmap(signature_png)
            if pix.width < 20 or pix.height < 10:
                raise ValueError
        except Exception as exc:
            raise SigningError("invalid signature image") from exc
        doc = fitz.open(stream=bytes(r[10]), filetype="pdf")
        page = doc[r[5] - 1]
        rect = fitz.Rect(r[6], r[7], r[8], r[9])
        page.insert_image(rect, stream=signature_png, keep_proportion=True)
        stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        osha = _sha(bytes(r[10]))
        page.insert_textbox(fitz.Rect(rect.x0, rect.y1 + 1, rect.x0 + 360, rect.y1 + 12),
                            f"E-signed {stamp} | original sha256 {osha[:16]}", fontsize=6, color=(0.35, 0.35, 0.35))
        out = doc.tobytes(garbage=3, deflate=True)
        ssha = _sha(out)
        # atomic one-time flip: a second submit finds status != 'pending' and signs nothing
        cur = self.db.execute(
            "UPDATE sign_requests SET status='signed', signed=?, signed_sha=?, signed_at=?, ip_hash=?, user_agent=?, consent_text=? "
            "WHERE id=? AND status='pending'",
            (out, ssha, time.time(), hmac.new(self.audit_secret, ip.encode(), "sha256").hexdigest() if ip else None,
             user_agent[:300], CONSENT[lang], rid))
        self.db.commit()
        if cur.rowcount != 1:
            raise SigningError("already signed")
        self._event(rid, "signed", {"signed_sha256": ssha, "original_sha256": osha})
        return {"id": rid, "signed_sha256": ssha}

    def _event(self, rid: str, event: str, detail: dict[str, Any]) -> None:
        import json
        self.db.execute("INSERT INTO sign_events(ts,request_id,event,detail) VALUES(?,?,?,?)", (time.time(), rid, event, json.dumps(detail)))
        self.db.commit()
