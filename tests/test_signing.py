import base64
import io
import time

import pytest

pymupdf = pytest.importorskip("pymupdf")

from hal_gateway import (ActionStore, Gateway, InMemoryPolicyBackend, InMemoryProposalBackend, InMemoryQuoteBackend,
                         NotAllowed, Principal, Role)
from hal_gateway.signing import SigningError, SigningService

staff = Principal(Role.AGENT, agent_code="ca", subject="ca@x")
client = Principal(Role.CLIENT, client_id=1, subject="c1@x")


def make_pdf(pages=3) -> bytes:
    d = pymupdf.open()
    for i in range(pages):
        d.new_page(width=595, height=842).insert_text((72, 72), f"Application page {i + 1}")
    return d.tobytes()


def make_sig() -> bytes:
    pix = pymupdf.Pixmap(pymupdf.csRGB, pymupdf.IRect(0, 0, 120, 40), False)
    pix.clear_with(200)
    return pix.tobytes("png")


@pytest.fixture()
def svc():
    return SigningService(base_url="https://hal.test")


def token_of(link: str) -> str:
    return link.rsplit("/", 1)[1]


def test_full_flow_stamps_signature_on_the_chosen_page(svc):
    pdf = make_pdf()
    req = svc.create(staff, pdf, title="Fire application 40256705", signer_name="J. Margaritis", page=3, rect=(300, 700, 560, 780), lang="el")
    tok = token_of(req["link"])
    assert req["link"].startswith("https://hal.test/s/") and len(tok) >= 40
    v = svc.view(tok)
    assert v.page == 3 and v.page_count == 3
    assert svc.page_png(tok)[:4] == b"\x89PNG"
    out = svc.sign(tok, make_sig(), True, ip="1.2.3.4", user_agent="test")
    signed = svc.signed_pdf(staff, req["id"])
    doc = pymupdf.open(stream=signed, filetype="pdf")
    assert len(doc[2].get_images()) == 1 and len(doc[0].get_images()) == 0
    assert signed != pdf and out["signed_sha256"] == svc.status(staff, req["id"])["signed_sha256"]
    assert svc.status(staff, req["id"])["original_sha256"] == req["document_sha256"]
    assert [e["event"] for e in svc.events(req["id"])] == ["created", "signed"]


def test_link_is_single_use_and_cannot_sign_twice(svc):
    req = svc.create(staff, make_pdf(1), title="t", signer_name="s", page=1, rect=(10, 10, 200, 80))
    tok = token_of(req["link"])
    svc.sign(tok, make_sig(), True)
    with pytest.raises(SigningError):
        svc.sign(tok, make_sig(), True)
    with pytest.raises(SigningError):
        svc.view(tok)


def test_requires_consent_and_valid_image(svc):
    tok = token_of(svc.create(staff, make_pdf(1), title="t", signer_name="s", page=1, rect=(10, 10, 200, 80))["link"])
    with pytest.raises(SigningError):
        svc.sign(tok, make_sig(), False)
    with pytest.raises(SigningError):
        svc.sign(tok, b"not a png", True)
    with pytest.raises(SigningError):
        svc.sign(tok, b"x" * 400_000, True)
    svc.sign(tok, make_sig(), True)  # still pending after the failed attempts


def test_wrong_token_expired_and_revoked(svc):
    with pytest.raises(SigningError):
        svc.view("A" * 43)
    req = svc.create(staff, make_pdf(1), title="t", signer_name="s", page=1, rect=(10, 10, 200, 80), ttl_days=-1)
    with pytest.raises(SigningError):
        svc.view(token_of(req["link"]))
    req2 = svc.create(staff, make_pdf(1), title="t", signer_name="s", page=1, rect=(10, 10, 200, 80))
    svc.revoke(staff, req2["id"])
    with pytest.raises(SigningError):
        svc.sign(token_of(req2["link"]), make_sig(), True)


def test_only_staff_can_create_read_or_revoke(svc):
    for who in (client, Principal(Role.EXTERNAL_AGENT, client_id=1, subject="tok")):
        with pytest.raises(PermissionError):
            svc.create(who, make_pdf(1), title="t", signer_name="s", page=1, rect=(10, 10, 200, 80))
    req = svc.create(staff, make_pdf(1), title="t", signer_name="s", page=1, rect=(10, 10, 200, 80))
    with pytest.raises(PermissionError):
        svc.signed_pdf(client, req["id"])
    with pytest.raises(PermissionError):
        svc.revoke(client, req["id"])


def test_token_is_not_stored_in_clear(svc):
    req = svc.create(staff, make_pdf(1), title="t", signer_name="s", page=1, rect=(10, 10, 200, 80))
    tok = token_of(req["link"])
    dump = "\n".join(svc.db.iterdump())
    assert tok not in dump


def test_rejects_bad_pdf_page_and_box(svc):
    with pytest.raises(SigningError):
        svc.create(staff, b"not a pdf", title="t", signer_name="s", page=1, rect=(1, 1, 2, 2))
    with pytest.raises(SigningError):
        svc.create(staff, make_pdf(1), title="t", signer_name="s", page=2, rect=(10, 10, 200, 80))
    with pytest.raises(SigningError):
        svc.create(staff, make_pdf(1), title="t", signer_name="s", page=1, rect=(10, 10, 900, 80))


def test_gateway_tool_is_staff_only_and_returns_link():
    pol = InMemoryPolicyBackend({1: []}, {"ca": {1}})
    svc = SigningService(base_url="https://hal.test")
    gw = Gateway(pol, InMemoryQuoteBackend({}), InMemoryProposalBackend(), ActionStore(pol), signing=svc)
    args = {"client_id": 1, "pdf_b64": base64.b64encode(make_pdf(2)).decode(), "page": 2, "rect": [300, 700, 560, 780],
            "signer_name": "J. Margaritis", "title": "Application"}
    out = gw.call(staff, "request_signature", args, "el")
    assert out["link"].startswith("https://hal.test/s/")
    with pytest.raises(NotAllowed):
        gw.call(client, "request_signature", args)
    assert "request_signature" not in [t["name"] for t in gw.specs(client)]


def test_http_pages_work_end_to_end(monkeypatch):
    pytest.importorskip("fastapi")
    from fastapi.testclient import TestClient
    from hal_gateway import signing_app

    req = signing_app.service.create(staff, make_pdf(2), title="App", signer_name="J. M.", page=2, rect=(300, 700, 560, 780), lang="en")
    tok = token_of(req["link"])
    c = TestClient(signing_app.app)
    page = c.get(f"/s/{tok}")
    assert page.status_code == 200 and "Sign document" in page.text and page.headers["cache-control"] == "no-store"
    assert c.get(f"/s/{tok}/page.png").status_code == 200 and c.get(f"/s/{tok}/doc.pdf").content.startswith(b"%PDF")
    sig = "data:image/png;base64," + base64.b64encode(make_sig()).decode()
    assert c.post(f"/s/{tok}/sign", json={"signature": sig, "consent": True}).json()["ok"] is True
    assert c.post(f"/s/{tok}/sign", json={"signature": sig, "consent": True}).status_code == 400
    assert c.get(f"/s/{tok}").status_code == 404
    assert c.get("/s/short").status_code == 404
