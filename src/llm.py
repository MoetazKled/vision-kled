"""LLM client factory. Supports OpenAI, Anthropic, Gemini, and a local fallback."""

from __future__ import annotations

import logging

from src.config import settings
from src.fallback import FallbackChatModel

logger = logging.getLogger("visionkled")


def has_llm_key() -> bool:
    """True when a usable provider key is configured (not a placeholder)."""
    provider = settings.llm_provider.lower().strip()
    if provider in {"mock", "fallback", "local"}:
        return False
    if provider == "anthropic":
        return _looks_like_key(settings.anthropic_api_key)
    if provider in {"gemini", "google"}:
        return _looks_like_key(settings.google_api_key)
    return _looks_like_key(settings.openai_api_key)


def _looks_like_key(value: str) -> bool:
    text = (value or "").strip()
    if not text:
        return False
    lowered = text.lower()
    return not any(token in lowered for token in ("your-", "replace", "changeme", "xxx"))


def get_chat_model(temperature: float = 0.4):
    """Return the configured chat model.

    Why a factory: Phase 0 must stay cheap. Swap provider via env without
    touching agent code. If no key is set, a rule-based fallback keeps
    the WhatsApp simulator usable on localhost.
    """
    if not has_llm_key():
        logger.warning("No LLM API key found — using local fallback replies")
        return FallbackChatModel()

    provider = settings.llm_provider.lower().strip()

    if provider == "anthropic":
        from langchain_anthropic import ChatAnthropic

        return ChatAnthropic(
            model=settings.llm_model or "claude-3-5-haiku-latest",
            api_key=settings.anthropic_api_key,
            temperature=temperature,
        )

    if provider in {"gemini", "google"}:
        from langchain_google_genai import ChatGoogleGenerativeAI

        return ChatGoogleGenerativeAI(
            model=settings.llm_model or "gemini-2.0-flash",
            google_api_key=settings.google_api_key,
            temperature=temperature,
        )

    from langchain_openai import ChatOpenAI

    return ChatOpenAI(
        model=settings.llm_model or "gpt-4o-mini",
        api_key=settings.openai_api_key,
        temperature=temperature,
    )
