"""Optional Chainlit chat — same LangGraph as the admin simulator.

Install extra: pip install chainlit
Run: chainlit run chainlit_app.py --port 8001
"""

from __future__ import annotations

import chainlit as cl

from src.bootstrap import init_db
from src.database import SessionLocal
from src.graph.graph import run_turn
from src.memory import (
    get_or_create_conversation,
    lead_to_dict,
    load_history,
    save_message,
    upsert_lead,
)


@cl.on_chat_start
async def start() -> None:
    init_db()
    cl.user_session.set("lead", {"name": "", "phone": "+21620123456", "product": "portfolio"})
    await cl.Message(
        content="مرحبا. أنا مساعد السيد Moetez Khaled. نعمل على منصة جديدة — عندك دقيقتين؟"
    ).send()


@cl.on_message
async def on_message(message: cl.Message) -> None:
    db = SessionLocal()
    try:
        lead = upsert_lead(db, cl.user_session.get("lead") or {})
        conversation = get_or_create_conversation(db, cl.user_session.get("id") or "chainlit", lead)
        history = load_history(db, conversation.id)
        save_message(db, conversation.id, "user", message.content)
        result = run_turn(user_text=message.content, lead=lead_to_dict(lead), history=history)
        reply = result.get("last_assistant") or ""
        save_message(db, conversation.id, "assistant", reply)
        updated = result.get("lead") or {}
        updated["id"] = lead.id
        cl.user_session.set("lead", lead_to_dict(upsert_lead(db, updated)))
        await cl.Message(content=reply).send()
    finally:
        db.close()
