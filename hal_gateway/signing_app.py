"""Public signing pages (mobile first, EL/EN). Run:  uvicorn hal_gateway.signing_app:app
Needs: pip install halecosystem[signing]   (fastapi, uvicorn, pymupdf)
The broker creates requests through SigningService / the `request_signature` gateway tool; the client only ever sees /s/<token>."""
from __future__ import annotations

import base64
import html
import os
import re

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, Response

from .i18n import normalize_lang
from .signing import CONSENT, SigningError, SigningService

service = SigningService(path=os.getenv("HAL_SIGN_DB", ":memory:"), audit_secret=os.getenv("HAL_AUDIT_SALT", ""),
                         base_url=os.getenv("HAL_PUBLIC_URL", "http://localhost:8000"))
app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)

_HEADERS = {"Cache-Control": "no-store", "X-Robots-Tag": "noindex", "Referrer-Policy": "no-referrer",
            "X-Content-Type-Options": "nosniff", "X-Frame-Options": "DENY",
            "Content-Security-Policy": "default-src 'self'; img-src 'self' data:; style-src 'unsafe-inline'; script-src 'unsafe-inline'"}

_T = {
    "el": dict(h="Υπογραφή εγγράφου", sub="Υπογράψτε μέσα στο πλαίσιο με το δάχτυλο ή το ποντίκι.", clear="Καθαρισμός", btn="Υπογραφή",
               full="Άνοιγμα ολόκληρου του εγγράφου", done="Η υπογραφή καταχωρήθηκε. Ο broker σας θα ενημερωθεί.",
               need="Σχεδιάστε την υπογραφή σας και τσεκάρετε τη συγκατάθεση.", err="Δεν ήταν δυνατή η υπογραφή.",
               bad="Ο σύνδεσμος δεν είναι έγκυρος, έχει λήξει ή το έγγραφο έχει ήδη υπογραφεί. Επικοινωνήστε με τον broker σας.",
               note="Ηλεκτρονική υπογραφή. Η αποδοχή από τον ασφαλιστή επιβεβαιώνεται χωριστά."),
    "en": dict(h="Sign document", sub="Sign inside the box with your finger or mouse.", clear="Clear", btn="Sign",
               full="Open the full document", done="Your signature was recorded. Your broker will be notified.",
               need="Draw your signature and tick the consent box.", err="Signing failed.",
               bad="This link is invalid, expired or the document is already signed. Please contact your broker.",
               note="Electronic signature. Acceptance by the insurer is confirmed separately."),
}

_PAGE = """<!doctype html><html lang="{lang}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{h}</title><style>body{{font:16px system-ui;margin:0;padding:16px;max-width:640px;margin:auto}}img.pg{{width:100%;border:1px solid #ccc}}
canvas{{width:100%;height:180px;border:2px dashed #888;border-radius:8px;touch-action:none;background:#fff}}button{{font:inherit;padding:12px 18px;border-radius:8px;border:0;margin:6px 6px 6px 0}}
#go{{background:#1C3F5E;color:#fff}}label{{display:block;margin:12px 0}}small{{color:#555}}</style></head><body>
<h2>{h}</h2><p><b>{title}</b><br>{signer}</p><img class="pg" src="/s/{token}/page.png" alt=""><p><a href="/s/{token}/doc.pdf" target="_blank">{full}</a></p>
<p>{sub}</p><canvas id="c" width="900" height="360"></canvas><div><button id="clr">{clear}</button></div>
<label><input type="checkbox" id="ok"> {consent}</label><button id="go">{btn}</button><p id="msg" role="status"></p><small>{note}</small>
<script>
const c=document.getElementById('c'),x=c.getContext('2d');x.lineWidth=5;x.lineCap='round';x.strokeStyle='#111';let d=false,ink=false;
function p(e){{const r=c.getBoundingClientRect();return[(e.clientX-r.left)*c.width/r.width,(e.clientY-r.top)*c.height/r.height]}}
c.onpointerdown=e=>{{d=true;ink=true;const[a,b]=p(e);x.beginPath();x.moveTo(a,b);c.setPointerCapture(e.pointerId)}};
c.onpointermove=e=>{{if(!d)return;const[a,b]=p(e);x.lineTo(a,b);x.stroke()}};c.onpointerup=()=>d=false;
document.getElementById('clr').onclick=()=>{{x.clearRect(0,0,c.width,c.height);ink=false}};
document.getElementById('go').onclick=async()=>{{const m=document.getElementById('msg');
if(!ink||!document.getElementById('ok').checked){{m.textContent={need};return}}
const r=await fetch('/s/{token}/sign',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{signature:c.toDataURL('image/png'),consent:true}})}});
m.textContent=r.ok?{done}:{err};if(r.ok)document.getElementById('go').disabled=true}};
</script></body></html>"""

_TOKEN = re.compile(r"^[A-Za-z0-9_-]{20,80}$")


def _json_str(s: str) -> str:
    import json
    return json.dumps(s)


@app.get("/s/{token}", response_class=HTMLResponse)
def sign_page(token: str, lang: str | None = None):
    try:
        if not _TOKEN.match(token):
            raise SigningError("invalid link")
        v = service.view(token)
    except SigningError:
        return HTMLResponse(f"<p style='font:16px system-ui;padding:16px'>{html.escape(_T[normalize_lang(lang)]['bad'])}</p>", status_code=404, headers=_HEADERS)
    lg = normalize_lang(lang or v.lang)
    t = _T[lg]
    body = _PAGE.format(lang=lg, h=t["h"], title=html.escape(v.title), signer=html.escape(v.signer_name), token=token, full=t["full"],
                        sub=t["sub"], clear=t["clear"], consent=html.escape(CONSENT[lg]), btn=t["btn"], note=t["note"],
                        need=_json_str(t["need"]), done=_json_str(t["done"]), err=_json_str(t["err"]))
    return HTMLResponse(body, headers=_HEADERS)


def _guard(token: str) -> str:
    if not _TOKEN.match(token):
        raise HTTPException(404)
    return token


@app.get("/s/{token}/page.png")
def page_png(token: str):
    try:
        return Response(service.page_png(_guard(token)), media_type="image/png", headers=_HEADERS)
    except SigningError:
        raise HTTPException(404)


@app.get("/s/{token}/doc.pdf")
def doc_pdf(token: str):
    try:
        return Response(service.original_pdf(_guard(token)), media_type="application/pdf",
                        headers={**_HEADERS, "Content-Disposition": 'inline; filename="document.pdf"'})
    except SigningError:
        raise HTTPException(404)


@app.post("/s/{token}/sign")
async def do_sign(token: str, request: Request):
    _guard(token)
    try:
        data = await request.json()
        m = re.match(r"^data:image/png;base64,([A-Za-z0-9+/=]+)$", str(data.get("signature", "")))
        if not m:
            raise SigningError("invalid signature image")
        png = base64.b64decode(m.group(1), validate=True)
        ip = (request.headers.get("x-forwarded-for", "").split(",")[-1].strip() or (request.client.host if request.client else ""))
        out = service.sign(token, png, bool(data.get("consent")), ip=ip, user_agent=request.headers.get("user-agent", ""))
        return JSONResponse({"ok": True, "id": out["id"]}, headers=_HEADERS)
    except SigningError as exc:
        return JSONResponse({"ok": False, "error": str(exc)}, status_code=400, headers=_HEADERS)
    except Exception:
        return JSONResponse({"ok": False, "error": "bad request"}, status_code=400, headers=_HEADERS)
