"""Pydantic schemas for the Vision Kled admin API."""

from __future__ import annotations

from pydantic import BaseModel, Field


class LeadIn(BaseModel):
    """Payload used to create or update a lead from the admin UI."""

    name: str = ""
    phone: str = ""
    business_type: str = ""
    profession: str = ""
    has_website: str = ""
    how_found: str = ""
    country: str = ""
    language: str = ""
    product: str = "portfolio"
    status: str = "new"
    source: str = "manual"
    notes: str = ""
    consent_opt_in: bool = True


class ChatIn(BaseModel):
    """One WhatsApp-style message from the admin simulator."""

    message: str = Field(min_length=1, max_length=4000)
    force_demo: bool = False


class SubscribeIn(BaseModel):
    """Manual subscription after the client agrees offline."""

    plan: str = "portfolio_monthly"
    price_usd: str = "12"


class ChangeIn(BaseModel):
    """Support request the client would send after becoming a subscriber."""

    request: str = Field(min_length=1, max_length=4000)
