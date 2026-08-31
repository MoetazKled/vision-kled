"""Agent nodes: extract lead facts, talk, build demo, present, close."""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from src.demo_builder import build_demo
from src.extract import heuristic_extract, last_assistant_text, last_user_text
from src.graph.state import AgentState
from src.intent import wants_demo
from src.language import detect_language
from src.llm import get_chat_model, has_llm_key
from src.prompts import build_system_prompt

logger = logging.getLogger("visionkled")

NEEDED_FIELDS = ("profession", "has_website", "how_found")


def _lead(state: AgentState) -> dict[str, Any]:
    return dict(state.get("lead") or {})


def language_node(state: AgentState) -> dict[str, Any]:
    """Agent 7 — language from phone, with a default of Arabic for this market."""
    lead = _lead(state)
    language = detect_language(lead.get("phone") or "", fallback="ar")
    lead["language"] = language
    return {"language": language, "lead": lead}


def extract_lead_node(state: AgentState) -> dict[str, Any]:
    """Pull structured facts from the latest user message."""
    lead = _lead(state)
    messages = state.get("messages") or []
    last_user = last_user_text(messages)
    assistant_text = last_assistant_text(messages)
    if not last_user:
        ready = _ready(lead)
        return {
            "lead": lead,
            "ready_for_demo": ready,
            "user_wants_demo": wants_demo(
                last_user,
                ready_for_demo=ready,
                has_demo=bool(state.get("demo_url")),
                last_assistant=assistant_text,
            )
            or bool(state.get("user_wants_demo")),
        }

    parsed: dict[str, Any] = {}
    if has_llm_key():
        try:
            parsed = _llm_extract(last_user)
        except Exception as exc:
            logger.warning("LLM extract failed (%s) — using heuristics", exc)
            parsed = {}
    if not parsed:
        lead = heuristic_extract(lead, last_user, assistant_text)

    for key, value in parsed.items():
        if value and not lead.get(key):
            lead[key] = str(value).strip()
    if lead.get("profession") and not lead.get("business_type"):
        lead["business_type"] = lead["profession"]

    ready = _ready(lead)
    consent = wants_demo(
        last_user,
        ready_for_demo=ready,
        has_demo=bool(state.get("demo_url")),
        last_assistant=assistant_text,
    ) or bool(state.get("user_wants_demo"))
    return {"lead": lead, "ready_for_demo": ready, "user_wants_demo": consent}


def talk_node(state: AgentState) -> dict[str, Any]:
    """Single speaking node. Phase only changes what the 13-block prompt emphasizes."""
    lead = _lead(state)
    language = state.get("language") or lead.get("language") or "ar"
    phase = _phase(state)
    prompt = build_system_prompt(
        language=language,
        lead=lead,
        phase=phase,
        product=lead.get("product") or "portfolio",
        demo_url=state.get("demo_url"),
    )
    model = get_chat_model()
    history = list(state.get("messages") or [])
    try:
        response = model.invoke([SystemMessage(content=prompt), *history])
    except Exception as exc:
        logger.warning("LLM call failed (%s) — using local fallback", exc)
        from src.fallback import FallbackChatModel

        response = FallbackChatModel().invoke([SystemMessage(content=prompt), *history])
    text = str(response.content).strip()
    return {"messages": [response], "last_assistant": text, "phase": phase}


def demo_builder_node(state: AgentState) -> dict[str, Any]:
    """Agent 3 — build the demo only after the user agrees (HITL)."""
    if not state.get("user_wants_demo"):
        return {}
    if (state.get("lead") or {}).get("product") == "bac":
        return {"phase": "closing"}
    result = build_demo(_lead(state))
    logger.info("Demo built for slug=%s url=%s", result["slug"], result["url"])
    return {
        "demo_slug": result["slug"],
        "demo_url": result["url"],
        "phase": "presentation",
        "user_wants_demo": False,
    }


def _phase(state: AgentState) -> str:
    if state.get("subscription_offered"):
        return "closing"
    if state.get("demo_url"):
        return "presentation"
    if state.get("ready_for_demo") and not state.get("demo_url"):
        return "demo"
    return state.get("phase") or "outreach"


def _ready(lead: dict[str, Any]) -> bool:
    return all(str(lead.get(field) or "").strip() for field in NEEDED_FIELDS)


def _llm_extract(last_user: str) -> dict[str, Any]:
    model = get_chat_model(temperature=0)
    extractor = SystemMessage(
        content=(
            "Extract known fields from the user message. Return JSON only with keys: "
            "name, profession, business_type, has_website, how_found, country. "
            "Use empty string when unknown. has_website must be yes, no, or empty."
        )
    )
    raw = model.invoke([extractor, HumanMessage(content=last_user)]).content
    return _parse_json(str(raw))


def _parse_json(raw: str) -> dict[str, Any]:
    text = raw.strip()
    match = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if not match:
        return {}
    try:
        data = json.loads(match.group(0))
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}
