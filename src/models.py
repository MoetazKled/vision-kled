"""Persistence models for leads, conversations, demos, and subscriptions."""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base


class Lead(Base):
    """A potential or converted client, entered manually by the admin."""

    __tablename__ = "leads"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), default="")
    phone: Mapped[str] = mapped_column(String(40), default="")
    business_type: Mapped[str] = mapped_column(String(200), default="")
    profession: Mapped[str] = mapped_column(String(200), default="")
    has_website: Mapped[str] = mapped_column(String(40), default="")
    how_found: Mapped[str] = mapped_column(Text, default="")
    country: Mapped[str] = mapped_column(String(80), default="")
    language: Mapped[str] = mapped_column(String(20), default="ar")
    product: Mapped[str] = mapped_column(String(40), default="portfolio")
    status: Mapped[str] = mapped_column(String(40), default="new")
    source: Mapped[str] = mapped_column(String(40), default="manual")
    country_code: Mapped[str] = mapped_column(String(8), default="")
    consent_opt_in: Mapped[bool] = mapped_column(Boolean, default=True)
    opted_out: Mapped[bool] = mapped_column(Boolean, default=False)
    notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    conversations: Mapped[list["Conversation"]] = relationship(back_populates="lead")
    demos: Mapped[list["DemoSite"]] = relationship(back_populates="lead")


class Conversation(Base):
    """A chat thread with a lead (Chainlit session mapped here)."""

    __tablename__ = "conversations"

    id: Mapped[int] = mapped_column(primary_key=True)
    lead_id: Mapped[int | None] = mapped_column(ForeignKey("leads.id"), nullable=True)
    session_id: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    phase: Mapped[str] = mapped_column(String(40), default="outreach")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    lead: Mapped[Lead | None] = relationship(back_populates="conversations")
    messages: Mapped[list["Message"]] = relationship(
        back_populates="conversation",
        order_by="Message.id",
    )


class Message(Base):
    """One turn in a conversation, persisted so the agent has memory."""

    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(primary_key=True)
    conversation_id: Mapped[int] = mapped_column(ForeignKey("conversations.id"))
    role: Mapped[str] = mapped_column(String(20))
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    conversation: Mapped[Conversation] = relationship(back_populates="messages")


class DemoSite(Base):
    """A generated demo website for a lead."""

    __tablename__ = "demo_sites"

    id: Mapped[int] = mapped_column(primary_key=True)
    lead_id: Mapped[int] = mapped_column(ForeignKey("leads.id"))
    slug: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    template: Mapped[str] = mapped_column(String(40), default="portfolio")
    url: Mapped[str] = mapped_column(String(300))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    lead: Mapped[Lead] = relationship(back_populates="demos")


class ChangeRequest(Base):
    """A post-sale update request handled by the support agent (Phase 0: logged)."""

    __tablename__ = "change_requests"

    id: Mapped[int] = mapped_column(primary_key=True)
    lead_id: Mapped[int] = mapped_column(ForeignKey("leads.id"))
    request_text: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(40), default="logged")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class Subscription(Base):
    """Manual subscription record — payment stays offline in Phase 0."""

    __tablename__ = "subscriptions"

    id: Mapped[int] = mapped_column(primary_key=True)
    lead_id: Mapped[int] = mapped_column(ForeignKey("leads.id"))
    plan: Mapped[str] = mapped_column(String(80), default="portfolio_monthly")
    price_usd: Mapped[str] = mapped_column(String(20), default="12")
    status: Mapped[str] = mapped_column(String(40), default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
