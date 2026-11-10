import hashlib
import json

from hal_gateway.mcp_server import authenticate, load_principals


def test_token_auth_uses_hashes_and_rejects_unknown(tmp_path):
    digest = hashlib.sha256(b"secret-token").hexdigest()
    f = tmp_path / "t.json"
    f.write_text(json.dumps({digest: {"role": "external_agent", "client_id": 7, "subject": "token:maria"}}))
    principals = load_principals(str(f))
    p = authenticate("secret-token", principals)
    assert p and p.client_id == 7 and p.role.value == "external_agent"
    assert authenticate("wrong", principals) is None
    assert authenticate("", principals) is None
