# ruff: noqa
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.models import Gemini
from google.genai import types
from pydantic import BaseModel, Field, ValidationError, field_validator

_DISCOUNT_STORE = {
    "WELCOME50": {"discount_percent": 50, "redeemed_by": None},
    "SUMMER20": {"discount_percent": 20, "redeemed_by": None},
}


class DiscountRedemptionRequest(BaseModel):
    """Validated input for discount redemption tool calls."""

    discount_code: str = Field(min_length=1, max_length=32)
    user_id: str = Field(min_length=1, max_length=64)

    @field_validator("discount_code", "user_id", mode="before")
    @classmethod
    def strip_text(cls, value: str) -> str:
        if not isinstance(value, str):
            raise ValueError("Value must be a string.")
        return value.strip()

    @field_validator("discount_code")
    @classmethod
    def normalize_discount_code(cls, value: str) -> str:
        return value.upper()

    @field_validator("user_id")
    @classmethod
    def reject_guest_user(cls, value: str) -> str:
        if value.startswith("guest_"):
            raise ValueError(
                "A registered user ID is required to redeem a discount code."
            )
        return value


def _validation_error_response(error: ValidationError) -> dict:
    fields = {issue["loc"][0] for issue in error.errors()}
    if "user_id" in fields:
        return {
            "status": "error",
            "message": "A registered user ID is required to redeem a discount code.",
        }
    return {
        "status": "error",
        "message": "A discount code is required.",
    }


def redeem_discount_code(discount_code: str, user_id: str) -> dict:
    """Redeems a single-use discount code for a registered retail user.

    Args:
        discount_code: The discount code the customer wants to redeem.
        user_id: The registered retail customer user ID redeeming the code.

    Returns:
        A dictionary describing whether the discount code was redeemed.
    """
    try:
        request = DiscountRedemptionRequest(
            discount_code=discount_code,
            user_id=user_id,
        )
    except ValidationError as error:
        return _validation_error_response(error)

    discount = _DISCOUNT_STORE.get(request.discount_code)

    if discount is None:
        return {
            "status": "error",
            "code": request.discount_code,
            "message": "Discount code is invalid.",
        }

    if discount["redeemed_by"] is not None:
        return {
            "status": "error",
            "code": request.discount_code,
            "message": "Discount code has already been redeemed.",
            "redeemed_by": discount["redeemed_by"],
        }

    discount["redeemed_by"] = request.user_id
    return {
        "status": "success",
        "code": request.discount_code,
        "discount_percent": discount["discount_percent"],
        "message": f"Discount code {request.discount_code} redeemed successfully.",
        "redeemed_by": request.user_id,
    }


def _create_model() -> Gemini:
    return Gemini(
        model="gemini-2.5-flash",
        retry_options=types.HttpRetryOptions(attempts=3),
    )


discount_agent = Agent(
    name="discount_agent",
    model=_create_model(),
    description="Redeems discount codes for registered retail users.",
    instruction=(
        "You are the Discount Agent for a retail shopping assistant. Handle only "
        "discount-code redemption. Ask for the registered user ID if it is missing, "
        "then call redeem_discount_code. Never claim a discount was redeemed unless "
        "the tool returns success. Discount codes are single-use."
    ),
    tools=[redeem_discount_code],
)

faq_agent = Agent(
    name="faq_agent",
    model=_create_model(),
    description="Answers general retail store policy and shopping FAQ questions.",
    instruction=(
        "You are the FAQ Agent for a retail shopping assistant. Answer general "
        "questions about shopping, returns, shipping, sizing, and store policies. "
        "Keep answers practical and avoid making up exact policies that are not "
        "provided; say when the customer should check the official store policy."
    ),
)


root_agent = Agent(
    name="shopping_manager_agent",
    model=_create_model(),
    description="Manager agent that routes retail shopping requests to specialists.",
    instruction=(
        "You are the Shopping Manager Agent for a retail store. Help customers "
        "with ordinary product and gift questions yourself. Route discount-code "
        "redemption to the Discount Agent and general store-policy questions to "
        "the FAQ Agent. For discount requests, ensure the customer provides a "
        "registered user ID and let the Discount Agent use the tool. Never claim "
        "a discount code was redeemed unless the tool returns success. Keep "
        "responses concise and customer-friendly."
    ),
    sub_agents=[discount_agent, faq_agent],
)

app = App(
    root_agent=root_agent,
    name="app",
)
