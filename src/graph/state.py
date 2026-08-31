"""LangGraph state shared by every Vision Kled agent node."""

from __future__ import annotations

from typing import Annotated, Any, TypedDict

from langgraph.graph.message import add_messages


class AgentState(TypedDict, total=False):
    """Conversation state that travels through the orchestrator."""

    messages: Annotated[list, add_messages]
    lead: dict[str, Any]
    language: str
    phase: str
    demo_url: str | None
    demo_slug: str | None
    ready_for_demo: bool
    user_wants_demo: bool
    subscription_offered: bool
    last_assistant: str
