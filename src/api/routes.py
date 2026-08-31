"""REST API for the super-admin dashboard and the WhatsApp simulator."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.database import get_db
from src.graph.graph import run_turn
from src.intent import is_opt_out, wants_subscription
from src.language import detect_language
from src.memory import (
    create_subscription,
    get_or_create_conversation,
    lead_to_dict,
    load_history,
    log_change_request,
    persist_demo,
    save_message,
    upsert_lead,
)
from src.models import ChangeRequest, DemoSite, Lead, Subscription
from src.products import PRODUCTS
from src.api.schemas import ChangeIn, ChatIn, LeadIn, SubscribeIn

logger = logging.getLogger("visionkled")
router = APIRouter(prefix="/api")


def _lead_or_404(db: Session, lead_id: int) -> Lead:
    lead = db.query(Lead).filter_by(id=lead_id).one_or_none()
    if lead is None:
        raise HTTPException(status_code=404, detail="العميل غير موجود")
    return lead


@router.get("/health")
def health() -> dict[str, str]:
    """Liveness probe used by Docker and the admin banner."""
    return {"status": "ok", "product": "vision-kled"}


@router.get("/stats")
def stats(db: Session = Depends(get_db)) -> dict[str, int]:
    """Dashboard counters for the super admin."""
    return {
        "leads": db.query(Lead).count(),
        "demos": db.query(DemoSite).count(),
        "subscriptions": db.query(Subscription).count(),
        "opted_out": db.query(Lead).filter_by(opted_out=True).count(),
    }


@router.get("/products")
def list_products() -> list[dict[str, str]]:
    """Catalog that the orchestrator can attach to a lead."""
    return PRODUCTS


@router.get("/leads")
def list_leads(db: Session = Depends(get_db)) -> list[dict]:
    rows = db.query(Lead).order_by(Lead.id.desc()).all()
    return [lead_to_dict(row) for row in rows]


@router.post("/leads")
def create_lead(payload: LeadIn, db: Session = Depends(get_db)) -> dict:
    """Manual lead injection — the only discovery source in Phase 0."""
    data = payload.model_dump()
    if not data.get("language") and data.get("phone"):
        data["language"] = detect_language(data["phone"], fallback="ar")
    lead = upsert_lead(db, data)
    logger.info("Lead created id=%s phone=%s", lead.id, lead.phone)
    return lead_to_dict(lead)


@router.get("/leads/{lead_id}")
def get_lead(lead_id: int, db: Session = Depends(get_db)) -> dict:
    lead = _lead_or_404(db, lead_id)
    conversation = get_or_create_conversation(db, f"lead-{lead.id}", lead)
    demos = db.query(DemoSite).filter_by(lead_id=lead.id).all()
    return {
        "lead": lead_to_dict(lead),
        "history": load_history(db, conversation.id),
        "phase": conversation.phase,
        "demos": [
            {"slug": d.slug, "url": d.url, "template": d.template} for d in demos
        ],
    }


@router.patch("/leads/{lead_id}")
def update_lead(lead_id: int, payload: LeadIn, db: Session = Depends(get_db)) -> dict:
    lead = _lead_or_404(db, lead_id)
    data = payload.model_dump()
    data["id"] = lead.id
    return lead_to_dict(upsert_lead(db, data))


@router.delete("/leads/{lead_id}")
def delete_lead(lead_id: int, db: Session = Depends(get_db)) -> dict[str, bool]:
    """Remove a lead and its conversation so the admin list stays usable."""
    from src.models import Conversation, Message

    lead = _lead_or_404(db, lead_id)
    for conv in db.query(Conversation).filter_by(lead_id=lead.id).all():
        db.query(Message).filter_by(conversation_id=conv.id).delete()
        db.delete(conv)
    db.query(DemoSite).filter_by(lead_id=lead.id).delete()
    db.query(Subscription).filter_by(lead_id=lead.id).delete()
    db.delete(lead)
    db.commit()
    return {"ok": True}


@router.post("/leads/trial")
def create_trial_lead(db: Session = Depends(get_db)) -> dict:
    """One-click sample client so the founder can test the full loop."""
    lead = upsert_lead(
        db,
        {
            "name": "أمين الطرابلسي",
            "phone": "+21620111222",
            "country": "Tunisia",
            "product": "portfolio",
            "profession": "محامي",
            "language": "ar",
            "source": "trial",
            "status": "new",
            "consent_opt_in": True,
        },
    )
    return lead_to_dict(lead)


@router.get("/leads/{lead_id}/messages")
def lead_messages(lead_id: int, db: Session = Depends(get_db)) -> list[dict[str, str]]:
    lead = _lead_or_404(db, lead_id)
    conversation = get_or_create_conversation(db, f"lead-{lead.id}", lead)
    return load_history(db, conversation.id)


OPENING = {
    "ar": (
        "مرحبا {name}. أنا مساعد السيد Moetez Khaled. "
        "نعمل على منصة جديدة ونحب رأيك في شيء بسيط — عندك دقيقتين؟"
    ),
    "fr": (
        "Bonjour {name}. Je suis l'assistant de M. Moetez Khaled. "
        "Nous travaillons sur une nouvelle plateforme — vous avez 2 minutes ?"
    ),
    "en": (
        "Hi {name}. I am the assistant of Mr. Moetez Khaled. "
        "We are working on a new platform and would value your view — do you have 2 minutes?"
    ),
}


@router.post("/leads/{lead_id}/start")
def start_conversation(lead_id: int, db: Session = Depends(get_db)) -> dict:
    """Send the consultative opening once, then wait for the lead."""
    lead = _lead_or_404(db, lead_id)
    conversation = get_or_create_conversation(db, f"lead-{lead.id}", lead)
    history = load_history(db, conversation.id)
    if history:
        return {"reply": history[-1]["content"], "history": history, "already_started": True}
    name = lead.name or ""
    lang = lead.language or detect_language(lead.phone, fallback="ar")
    template = OPENING.get(lang, OPENING["en"])
    reply = template.format(name=name).replace("مرحبا .", "مرحبا.")
    save_message(db, conversation.id, "assistant", reply)
    lead.status = "contacted"
    db.commit()
    return {"reply": reply, "history": load_history(db, conversation.id), "already_started": False}


@router.post("/leads/{lead_id}/chat")
def chat(lead_id: int, payload: ChatIn, db: Session = Depends(get_db)) -> dict:
    """Run one orchestrator turn. This is a local simulator, not WhatsApp send."""
    lead = _lead_or_404(db, lead_id)
    if lead.opted_out:
        raise HTTPException(status_code=409, detail="هذا العميل اختار إيقاف التواصل")

    conversation = get_or_create_conversation(db, f"lead-{lead.id}", lead)
    if is_opt_out(payload.message):
        lead.opted_out = True
        lead.status = "opted_out"
        db.commit()
        save_message(db, conversation.id, "user", payload.message)
        reply = "تم. لن نراسلك مرة أخرى."
        save_message(db, conversation.id, "assistant", reply)
        return {"reply": reply, "lead": lead_to_dict(lead), "opted_out": True}

    history = load_history(db, conversation.id)
    save_message(db, conversation.id, "user", payload.message)
    latest_demo = (
        db.query(DemoSite).filter_by(lead_id=lead.id).order_by(DemoSite.id.desc()).first()
    )
    result = run_turn(
        user_text=payload.message,
        lead=lead_to_dict(lead),
        history=history,
        demo_url=latest_demo.url if latest_demo else None,
        demo_slug=latest_demo.slug if latest_demo else None,
        user_wants_demo=payload.force_demo,
        subscription_offered=lead.status == "offered",
    )
    updated = result.get("lead") or lead_to_dict(lead)
    updated["id"] = lead.id
    lead = upsert_lead(db, updated)
    reply = result.get("last_assistant") or ""
    save_message(db, conversation.id, "assistant", reply)

    demo_url = result.get("demo_url")
    if demo_url and result.get("demo_slug"):
        persist_demo(
            db,
            lead.id,
            result["demo_slug"],
            demo_url,
            (result.get("lead") or {}).get("product") or lead.product,
        )
        lead.status = "demo_ready"

    if wants_subscription(payload.message) and (demo_url or latest_demo):
        lead.status = "offered"
        conversation.phase = "closing"
    elif result.get("phase"):
        conversation.phase = result["phase"]
    db.commit()

    return {
        "reply": reply,
        "lead": lead_to_dict(lead),
        "phase": conversation.phase,
        "demo_url": demo_url or (latest_demo.url if latest_demo else None),
    }


@router.post("/leads/{lead_id}/build-demo")
def force_build_demo(lead_id: int, db: Session = Depends(get_db)) -> dict:
    """HITL: super admin builds the demo without waiting for a chat yes."""
    lead = _lead_or_404(db, lead_id)
    conversation = get_or_create_conversation(db, f"lead-{lead.id}", lead)
    history = load_history(db, conversation.id)
    result = run_turn(
        user_text="نعم، أريد أن أرى النسخة",
        lead=lead_to_dict(lead),
        history=history,
        user_wants_demo=True,
    )
    updated = result.get("lead") or lead_to_dict(lead)
    updated["id"] = lead.id
    lead = upsert_lead(db, updated)
    if result.get("demo_url") and result.get("demo_slug"):
        persist_demo(
            db,
            lead.id,
            result["demo_slug"],
            result["demo_url"],
            lead.product or "portfolio",
        )
        lead.status = "demo_ready"
        db.commit()
    reply = result.get("last_assistant") or ""
    if reply:
        save_message(db, conversation.id, "assistant", reply)
    return {
        "reply": reply,
        "lead": lead_to_dict(lead),
        "demo_url": result.get("demo_url"),
    }


@router.post("/leads/{lead_id}/subscribe")
def subscribe(lead_id: int, payload: SubscribeIn, db: Session = Depends(get_db)) -> dict:
    lead = _lead_or_404(db, lead_id)
    sub = create_subscription(db, lead.id, payload.plan)
    sub.price_usd = payload.price_usd
    lead.status = "subscriber"
    db.commit()
    return {"id": sub.id, "status": sub.status, "lead": lead_to_dict(lead)}


@router.post("/leads/{lead_id}/support")
def support(lead_id: int, payload: ChangeIn, db: Session = Depends(get_db)) -> dict:
    """Agent 5 in Phase 0: log the change. Auto PR/merge is a later phase."""
    lead = _lead_or_404(db, lead_id)
    row = log_change_request(db, lead.id, payload.request)
    return {"id": row.id, "status": row.status}


@router.get("/demos")
def list_demos(db: Session = Depends(get_db)) -> list[dict]:
    rows = db.query(DemoSite).order_by(DemoSite.id.desc()).all()
    return [
        {
            "id": row.id,
            "lead_id": row.lead_id,
            "slug": row.slug,
            "url": row.url,
            "template": row.template,
        }
        for row in rows
    ]


@router.get("/subscriptions")
def list_subscriptions(db: Session = Depends(get_db)) -> list[dict]:
    rows = db.query(Subscription).order_by(Subscription.id.desc()).all()
    return [
        {
            "id": row.id,
            "lead_id": row.lead_id,
            "plan": row.plan,
            "price_usd": row.price_usd,
            "status": row.status,
        }
        for row in rows
    ]


@router.get("/support")
def list_support(db: Session = Depends(get_db)) -> list[dict]:
    rows = db.query(ChangeRequest).order_by(ChangeRequest.id.desc()).all()
    return [
        {
            "id": row.id,
            "lead_id": row.lead_id,
            "request": row.request_text,
            "status": row.status,
        }
        for row in rows
    ]
