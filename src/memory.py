"""Conversation memory helpers used by Chainlit and tests."""

from __future__ import annotations

from sqlalchemy.orm import Session

from src.models import ChangeRequest, Conversation, DemoSite, Lead, Message, Subscription


def get_or_create_conversation(db: Session, session_id: str, lead: Lead | None = None) -> Conversation:
    conversation = db.query(Conversation).filter_by(session_id=session_id).one_or_none()
    if conversation:
        return conversation
    conversation = Conversation(session_id=session_id, lead_id=lead.id if lead else None)
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    return conversation


def save_message(db: Session, conversation_id: int, role: str, content: str) -> Message:
    message = Message(conversation_id=conversation_id, role=role, content=content)
    db.add(message)
    db.commit()
    db.refresh(message)
    return message


def load_history(db: Session, conversation_id: int) -> list[dict[str, str]]:
    rows = (
        db.query(Message)
        .filter_by(conversation_id=conversation_id)
        .order_by(Message.id.asc())
        .all()
    )
    return [{"role": row.role, "content": row.content} for row in rows]


def upsert_lead(db: Session, data: dict) -> Lead:
    lead = None
    if data.get("id"):
        lead = db.query(Lead).filter_by(id=data["id"]).one_or_none()
    if lead is None and data.get("phone"):
        lead = db.query(Lead).filter_by(phone=data["phone"]).one_or_none()
    if lead is None:
        lead = Lead()
        db.add(lead)
    for field in (
        "name",
        "phone",
        "business_type",
        "profession",
        "has_website",
        "how_found",
        "country",
        "language",
        "product",
        "status",
        "source",
        "notes",
    ):
        if data.get(field) not in (None, ""):
            setattr(lead, field, data[field])
    if "consent_opt_in" in data:
        lead.consent_opt_in = bool(data["consent_opt_in"])
    if "opted_out" in data:
        lead.opted_out = bool(data["opted_out"])
    db.commit()
    db.refresh(lead)
    return lead


def lead_to_dict(lead: Lead | None) -> dict:
    if lead is None:
        return {}
    return {
        "id": lead.id,
        "name": lead.name,
        "phone": lead.phone,
        "business_type": lead.business_type,
        "profession": lead.profession,
        "has_website": lead.has_website,
        "how_found": lead.how_found,
        "country": lead.country,
        "language": lead.language,
        "product": lead.product,
        "status": lead.status,
        "source": lead.source,
        "consent_opt_in": lead.consent_opt_in,
        "opted_out": lead.opted_out,
        "notes": lead.notes,
        "created_at": lead.created_at.isoformat() if lead.created_at else None,
    }


def persist_demo(db: Session, lead_id: int, slug: str, url: str, template: str) -> DemoSite:
    """Save or update the generated demo URL for a lead."""
    existing = db.query(DemoSite).filter_by(slug=slug).one_or_none()
    if existing is None:
        existing = DemoSite(lead_id=lead_id, slug=slug, url=url, template=template)
        db.add(existing)
    else:
        existing.url = url
        existing.template = template
        existing.lead_id = lead_id
    db.commit()
    db.refresh(existing)
    return existing


def log_change_request(db: Session, lead_id: int, text: str) -> ChangeRequest:
    """Record a support request. GitHub auto-PR comes in a later phase."""
    row = ChangeRequest(lead_id=lead_id, request_text=text, status="logged")
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def create_subscription(db: Session, lead_id: int, plan: str = "portfolio_monthly") -> Subscription:
    sub = Subscription(lead_id=lead_id, plan=plan, status="pending")
    db.add(sub)
    db.commit()
    db.refresh(sub)
    return sub
