"""LangGraph orchestrator: language → extract → optional demo → talk."""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from langchain_core.messages import AIMessage, HumanMessage
from langgraph.graph import END, START, StateGraph

from src.graph.nodes import demo_builder_node, extract_lead_node, language_node, talk_node
from src.graph.state import AgentState


def _after_extract(state: AgentState) -> str:
    if state.get("user_wants_demo") and not state.get("demo_url"):
        return "demo_builder"
    return "talk"


def build_graph():
    """Compile the Phase 0 graph.

    Why this order: language and memory extraction are cheap and must run
    before the speaking agent, so the demo builder never sees an empty lead.
    """
    graph = StateGraph(AgentState)
    graph.add_node("detect_lang", language_node)
    graph.add_node("extract_facts", extract_lead_node)
    graph.add_node("demo_builder", demo_builder_node)
    graph.add_node("talk", talk_node)
    graph.add_edge(START, "detect_lang")
    graph.add_edge("detect_lang", "extract_facts")
    graph.add_conditional_edges(
        "extract_facts",
        _after_extract,
        {"demo_builder": "demo_builder", "talk": "talk"},
    )
    graph.add_edge("demo_builder", "talk")
    graph.add_edge("talk", END)
    return graph.compile()


@lru_cache(maxsize=1)
def get_graph():
    return build_graph()


def run_turn(
    *,
    user_text: str,
    lead: dict[str, Any],
    history: list[dict[str, str]],
    demo_url: str | None = None,
    demo_slug: str | None = None,
    user_wants_demo: bool = False,
    subscription_offered: bool = False,
) -> dict[str, Any]:
    """Run one user turn and return updated lead, reply, and demo fields."""
    messages: list = []
    for item in history:
        if item["role"] == "user":
            messages.append(HumanMessage(content=item["content"]))
        else:
            messages.append(AIMessage(content=item["content"]))
    messages.append(HumanMessage(content=user_text))

    result = get_graph().invoke(
        {
            "messages": messages,
            "lead": lead,
            "demo_url": demo_url,
            "demo_slug": demo_slug,
            "user_wants_demo": user_wants_demo,
            "subscription_offered": subscription_offered,
            "ready_for_demo": False,
        }
    )
    return result
