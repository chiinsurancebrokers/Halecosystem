import pytest

from hal_gateway import (ActionStore, Gateway, InMemoryPolicyBackend, InMemoryProposalBackend,
                         InMemoryQuoteBackend, NotAllowed, Principal, Role)
from hal_gateway import fairness
from hal_gateway.i18n import t


@pytest.fixture()
def env():
    pol = InMemoryPolicyBackend(
        policies={1: [{"id": 11, "type": "health"}], 2: [{"id": 22, "type": "travel"}]},
        agent_books={"ca": {1}, "3p": {2}},
    )
    quotes = InMemoryQuoteBackend({("Morgan Price", 40): 1234.5})
    props = InMemoryProposalBackend()
    store = ActionStore(pol)
    gw = Gateway(pol, quotes, props, store)
    return gw, pol, props, store


client1 = Principal(Role.CLIENT, client_id=1, subject="c1@x")
ext1 = Principal(Role.EXTERNAL_AGENT, client_id=1, subject="token-abc")
agent_ca = Principal(Role.AGENT, agent_code="ca", subject="ca@x")
agent_3p = Principal(Role.AGENT, agent_code="3p", subject="3p@x")
office = Principal(Role.BACKOFFICE, subject="bo@x")


def test_client_cannot_read_another_client_even_if_args_say_so(env):
    gw, *_ = env
    out = gw.call(client1, "get_my_policies", {"client_id": 2})
    assert out["policies"] == [{"id": 11, "type": "health"}]


def test_external_agent_is_bound_to_its_client(env):
    gw, *_ = env
    out = gw.call(ext1, "get_my_policies", {"client_id": 2})
    assert [p["id"] for p in out["policies"]] == [11]


def test_staff_only_see_their_book(env):
    gw, *_ = env
    assert gw.call(agent_ca, "get_my_policies", {"client_id": 1})["policies"]
    with pytest.raises(NotAllowed):
        gw.call(agent_ca, "get_my_policies", {"client_id": 2})


def test_writes_do_not_execute_until_broker_approves(env):
    gw, pol, _, store = env
    out = gw.call(client1, "open_ticket", {"subject": "Change address", "body": "new address"}, lang="en")
    assert out["status"] == "pending_broker_approval" and pol.tickets == []
    assert "approve" in out["message"]
    p, msg = store.approve(agent_ca, out["reference"], "en")
    assert p.status == "approved" and len(pol.tickets) == 1 and "Approved" in msg


def test_client_and_external_agent_cannot_approve_own_request(env):
    gw, pol, _, store = env
    ref = gw.call(ext1, "open_ticket", {"subject": "x"})["reference"]
    for who in (client1, ext1):
        with pytest.raises(NotAllowed):
            store.approve(who, ref)
    assert pol.tickets == []


def test_agent_cannot_approve_outside_their_book(env):
    gw, pol, _, store = env
    ref = gw.call(client1, "open_ticket", {"subject": "x"})["reference"]
    with pytest.raises(NotAllowed):
        store.approve(agent_3p, ref)
    assert pol.tickets == []
    assert store.approve(office, ref)[0].status == "approved"


def test_cannot_decide_twice(env):
    gw, _, _, store = env
    ref = gw.call(client1, "open_ticket", {"subject": "x"})["reference"]
    store.reject(agent_ca, ref, "duplicate", "en")
    with pytest.raises(NotAllowed):
        store.approve(agent_ca, ref)


def test_renewal_for_someone_elses_policy_is_refused(env):
    gw, *_ = env
    with pytest.raises(NotAllowed):
        gw.call(client1, "draft_renewal", {"policy_id": 22})


def test_failed_execution_is_not_reported_as_success(env):
    gw, _, _, store = env
    store.handlers["open_ticket"] = lambda p: (_ for _ in ()).throw(RuntimeError("db down"))
    ref = gw.call(client1, "open_ticket", {"subject": "x"})["reference"]
    p, _ = store.approve(agent_ca, ref)
    assert p.status == "failed"


def test_audit_log_records_denials_and_decisions(env):
    gw, _, _, store = env
    with pytest.raises(NotAllowed):
        gw.call(agent_ca, "get_my_policies", {"client_id": 2})
    ref = gw.call(client1, "open_ticket", {"subject": "x"})["reference"]
    store.approve(agent_ca, ref)
    events = [e["event"] for e in store.audit_log()]
    assert "proposed" in events and "approved" in events


def test_quote_uses_only_table_prices_and_carries_footers_in_both_languages(env):
    gw, *_ = env
    for lang in ("en", "el"):
        out = gw.call(client1, "quote_health_travel", {"age": 40, "country": "GR", "coverage_area": "worldwide"}, lang)
        assert "1234.50" in out["text"]
        assert t("broker_review", lang) in out["text"] and t("wording_prevails", lang) in out["text"]


def test_no_price_is_invented_when_profile_not_in_table(env):
    gw, *_ = env
    out = gw.call(client1, "quote_health_travel", {"age": 41}, "en")  # no interpolation from age 40
    assert out["plans"] == [] and "€" not in out["text"].split("\n\n")[0]


def test_travel_quote_says_it_is_not_health_cover(env):
    gw, *_ = env
    out = gw.call(client1, "quote_health_travel", {"age": 40, "kind": "travel"}, "el")
    assert t("travel_not_health", "el") in out["text"]


@pytest.mark.parametrize("text", ["Only 3 spots left!", "Τελευταία ευκαιρία για ασφάλιση", "Prices are going up next week",
                                  "This plan covers all pre-existing conditions"])
def test_fairness_blocks_scare_and_promises(text):
    with pytest.raises(fairness.FairnessViolation):
        fairness.check(text)


def test_tool_list_is_bilingual(env):
    gw, *_ = env
    assert gw.specs(client1, "en")[0]["description"] != gw.specs(client1, "el")[0]["description"]
