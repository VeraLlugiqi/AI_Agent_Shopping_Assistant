import pytest
from app.agent import (
    _DISCOUNT_STORE,
    app,
    discount_agent,
    faq_agent,
    redeem_discount_code,
    root_agent,
)


@pytest.fixture(autouse=True)
def reset_store():
    _DISCOUNT_STORE["WELCOME50"]["redeemed_by"] = None
    _DISCOUNT_STORE["SUMMER20"]["redeemed_by"] = None
    yield
    _DISCOUNT_STORE["WELCOME50"]["redeemed_by"] = None
    _DISCOUNT_STORE["SUMMER20"]["redeemed_by"] = None


def test_discount_code_can_only_be_redeemed_once():
    res_one = redeem_discount_code("WELCOME50", "user_123")
    assert res_one["status"] == "success"
    assert _DISCOUNT_STORE["WELCOME50"]["redeemed_by"] == "user_123"

    res_two = redeem_discount_code("WELCOME50", "user_456")
    assert res_two["status"] == "error"
    assert "already been redeemed" in res_two["message"]


def test_discount_redemption_normalizes_valid_input():
    res = redeem_discount_code(" welcome50 ", " user_123 ")
    assert res["status"] == "success"
    assert res["code"] == "WELCOME50"
    assert res["redeemed_by"] == "user_123"


def test_discount_redemption_rejects_invalid_code():
    res = redeem_discount_code("INVALID999", "user_123")
    assert res["status"] == "error"
    assert "invalid" in res["message"].lower()


def test_discount_redemption_rejects_guest_accounts():
    res = redeem_discount_code("SUMMER20", "guest_999")
    assert res["status"] == "error"
    assert "registered user" in res["message"].lower()
    assert _DISCOUNT_STORE["SUMMER20"]["redeemed_by"] is None


def test_root_agent_is_multi_agent_manager():
    sub_agent_names = {agent.name for agent in root_agent.sub_agents}

    assert app.root_agent is root_agent
    assert root_agent.name == "shopping_manager_agent"
    assert sub_agent_names == {
        "discount_agent",
        "faq_agent",
    }
    assert discount_agent in root_agent.sub_agents
    assert faq_agent in root_agent.sub_agents
    assert redeem_discount_code in discount_agent.tools


def test_discount_redemption_requires_user_id():
    res = redeem_discount_code("SUMMER20", "")
    assert res["status"] == "error"
    assert "registered user" in res["message"].lower()
    assert _DISCOUNT_STORE["SUMMER20"]["redeemed_by"] is None
