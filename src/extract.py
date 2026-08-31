"""Heuristic lead extraction used when no LLM key is configured.

The LLM extractor is preferred. This fallback keeps Phase 0 testable
on a laptop with zero API cost by filling one slot at a time.
"""

from __future__ import annotations

from typing import Any

from src.intent import parse_website_answer


def last_assistant_text(messages: list) -> str:
    """Return the most recent assistant/AI message content."""
    for msg in reversed(messages or []):
        role = getattr(msg, "type", None) or (
            msg.get("role") if isinstance(msg, dict) else ""
        )
        content = getattr(msg, "content", None) or (
            msg.get("content") if isinstance(msg, dict) else ""
        )
        if role in {"ai", "assistant"} and content:
            return str(content)
    return ""


def last_user_text(messages: list) -> str:
    """Return the most recent human message content."""
    for msg in reversed(messages or []):
        role = getattr(msg, "type", None) or (
            msg.get("role") if isinstance(msg, dict) else ""
        )
        content = getattr(msg, "content", None) or (
            msg.get("content") if isinstance(msg, dict) else ""
        )
        if role in {"human", "user"} and content:
            return str(content)
    return ""


def heuristic_extract(lead: dict[str, Any], user_text: str, assistant_text: str) -> dict[str, Any]:
    """Fill discovery fields from a WhatsApp-style reply.

    A first message often contains job + website + how-found together,
    so we scan the whole text before falling back to slot-filling.
    """
    updated = dict(lead)
    text = (user_text or "").strip()
    if not text:
        return updated

    job = _guess_job(text)
    if job and not updated.get("profession"):
        updated["profession"] = text.strip() if len(text) <= 24 else job
        updated.setdefault("business_type", updated["profession"])

    website = parse_website_answer(text)
    if website and not updated.get("has_website"):
        updated["has_website"] = website

    found = _guess_how_found(text)
    if found and not updated.get("how_found"):
        updated["how_found"] = found

    asked = (assistant_text or "").lower()
    if not updated.get("profession"):
        if any(word in asked for word in ("مهنة", "عمل", "profession", "business", "métier")):
            updated["profession"] = text
            updated.setdefault("business_type", text)
            return updated
        if len(text) > 2 and not parse_website_answer(text):
            updated["profession"] = text
            updated.setdefault("business_type", text)
            return updated

    if not updated.get("has_website"):
        if any(word in asked for word in ("موقع", "website", "site")):
            updated["has_website"] = website or ("yes" if len(text) > 8 else "no")
            return updated

    if not updated.get("how_found"):
        updated["how_found"] = text
    return updated


_JOBS = (
    "نجار",
    "حداد",
    "حلاق",
    "خياط",
    "طبيب",
    "محامي",
    "مهندس",
    "مطعم",
    "كوافير",
    "carpenter",
    "lawyer",
    "doctor",
    "developer",
)


def _guess_job(text: str) -> str:
    lowered = text.lower()
    for job in _JOBS:
        if job in lowered:
            return job
    return ""


def _guess_how_found(text: str) -> str:
    if any(word in text for word in ("جيران", "فيسبوك", "انستغرام", "واتساب", "سوق")):
        return text
    if any(word in text.lower() for word in ("facebook", "instagram", "whatsapp", "google", "neighbor")):
        return text
    return ""

