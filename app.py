"""Chainlit UI — local WhatsApp-style test of the Vision Kled agents."""

from __future__ import annotations

import chainlit as cl
from chainlit.input_widget import Select, TextInput
from sqlalchemy.orm import Session

from src.database import SessionLocal, init_db
from src.graph.graph import run_turn
from src.language import detect_language, language_label
from src.memory import (
    create_subscription,
    get_or_create_conversation,
    lead_to_dict,
    load_history,
    save_message,
    upsert_lead,
)
from src.models import DemoSite

init_db()

OPENING = {
    "ar": "مرحبا. أنا مساعد معتز خالد. نشتغل على منصة جديدة ونحب رأيك في حاجة بسيطة. عندك دقيقتين؟",
    "fr": "Bonjour. Je suis l'assistant de Moetez Khaled. On travaille sur une nouvelle plateforme et on aimerait votre avis. Vous avez deux minutes ?",
    "en": "Hello. I am the assistant of Moetez Khaled. We are working on a new platform and would like your opinion. Do you have two minutes?",
}


def _db() -> Session:
    return SessionLocal()


@cl.on_chat_start
async def start() -> None:
    await cl.ChatSettings(
        [
            Select(
                id="product",
                label="المنتج / Produit",
                values=["portfolio", "business", "bac"],
                initial_index=0,
            ),
            TextInput(id="name", label="الاسم (اختياري)", initial_value=""),
            TextInput(
                id="phone",
                label="الهاتف مع رمز الدولة مثل +216...",
                initial_value="+216",
            ),
        ]
    ).send()

    db = _db()
    try:
        session_id = cl.user_session.get("id") or cl.context.session.id
        conversation = get_or_create_conversation(db, session_id)
        lead = upsert_lead(db, {"product": "portfolio", "language": "ar"})
        conversation.lead_id = lead.id
        db.commit()
        cl.user_session.set("lead_id", lead.id)
        cl.user_session.set("conversation_id", conversation.id)
        cl.user_session.set("demo_url", None)
        cl.user_session.set("subscription_offered", False)
    finally:
        db.close()

    await cl.Message(
        content=(
            "Vision Kled — اختبار محلي للوكلاء.\n"
            "اكتب بالعربية أو الفرنسية أو الإنجليزية. املأ الاسم والهاتف من الإعدادات إن أردت.\n\n"
            + OPENING["ar"]
        )
    ).send()


@cl.on_settings_update
async def on_settings(values: dict) -> None:
    db = _db()
    try:
        lead_id = cl.user_session.get("lead_id")
        phone = values.get("phone") or ""
        language = detect_language(phone, fallback="ar")
        lead = upsert_lead(
            db,
            {
                "id": lead_id,
                "name": values.get("name") or "",
                "phone": phone,
                "product": values.get("product") or "portfolio",
                "language": language,
            },
        )
        cl.user_session.set("lead_id", lead.id)
        await cl.Message(
            content=f"تم حفظ العميل. اللغة المكتشفة: {language_label(language)}."
        ).send()
    finally:
        db.close()


@cl.on_message
async def main(message: cl.Message) -> None:
    db = _db()
    try:
        conversation_id = cl.user_session.get("conversation_id")
        lead_id = cl.user_session.get("lead_id")
        lead = upsert_lead(db, {"id": lead_id})
        save_message(db, conversation_id, "user", message.content)
        history = load_history(db, conversation_id)
        history = history[:-1]

        try:
            result = run_turn(
                user_text=message.content,
                lead=lead_to_dict(lead),
                history=history,
                demo_url=cl.user_session.get("demo_url"),
                demo_slug=cl.user_session.get("demo_slug"),
                user_wants_demo=False,
                subscription_offered=bool(cl.user_session.get("subscription_offered")),
            )
        except Exception as exc:
            await cl.Message(content=f"حصل خطأ تقني أثناء الرد: {exc}").send()
            return

        updated = result.get("lead") or lead_to_dict(lead)
        upsert_lead(db, {**updated, "id": lead.id})
        reply = result.get("last_assistant") or "..."
        save_message(db, conversation_id, "assistant", reply)

        actions = []
        if result.get("ready_for_demo") and not cl.user_session.get("demo_url"):
            actions.append(
                cl.Action(
                    name="build_demo",
                    payload={"value": "yes"},
                    label="ابنِ الديمو",
                )
            )
        if cl.user_session.get("demo_url") and not cl.user_session.get("subscription_offered"):
            actions.append(
                cl.Action(
                    name="offer_plan",
                    payload={"value": "yes"},
                    label="اعرض الاشتراك",
                )
            )

        await cl.Message(content=reply, actions=actions).send()
        cl.user_session.set("ready_for_demo", result.get("ready_for_demo"))
    finally:
        db.close()


@cl.action_callback("build_demo")
async def on_build_demo(action: cl.Action) -> None:
    db = _db()
    try:
        lead_id = cl.user_session.get("lead_id")
        conversation_id = cl.user_session.get("conversation_id")
        lead = upsert_lead(db, {"id": lead_id})
        history = load_history(db, conversation_id)
        result = run_turn(
            user_text="نعم، أريد أن أرى النسخة التجريبية.",
            lead=lead_to_dict(lead),
            history=history,
            user_wants_demo=True,
        )
        demo_url = result.get("demo_url")
        cl.user_session.set("demo_url", demo_url)
        cl.user_session.set("demo_slug", result.get("demo_slug"))
        upsert_lead(db, {**(result.get("lead") or {}), "id": lead.id, "status": "demo_ready"})
        if result.get("demo_slug"):
            db.add(
                DemoSite(
                    lead_id=lead.id,
                    slug=result["demo_slug"],
                    template="portfolio",
                    url=demo_url or "",
                )
            )
            db.commit()
        reply = result.get("last_assistant") or f"الديمو جاهز: {demo_url}"
        save_message(db, conversation_id, "assistant", reply)
        await cl.Message(
            content=reply,
            actions=[
                cl.Action(name="offer_plan", payload={"value": "yes"}, label="اعرض الاشتراك"),
            ],
        ).send()
    finally:
        db.close()


@cl.action_callback("offer_plan")
async def on_offer_plan(action: cl.Action) -> None:
    db = _db()
    try:
        lead_id = cl.user_session.get("lead_id")
        conversation_id = cl.user_session.get("conversation_id")
        create_subscription(db, lead_id)
        cl.user_session.set("subscription_offered", True)
        lead = upsert_lead(db, {"id": lead_id, "status": "closing"})
        history = load_history(db, conversation_id)
        result = run_turn(
            user_text="الموقع جاهز. أريد معرفة السعر.",
            lead=lead_to_dict(lead),
            history=history,
            demo_url=cl.user_session.get("demo_url"),
            demo_slug=cl.user_session.get("demo_slug"),
            subscription_offered=True,
        )
        reply = result.get("last_assistant") or ""
        save_message(db, conversation_id, "assistant", reply)
        await cl.Message(content=reply).send()
    finally:
        db.close()
