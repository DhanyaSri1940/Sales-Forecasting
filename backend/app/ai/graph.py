from __future__ import annotations

from typing import Any

from backend.app.ai.nodes import analyze_node, generate_node, retrieve_node, validate_node
from backend.app.ai.state import InsightState


def _run_pipeline(question: str) -> InsightState:
    state: InsightState = {"question": question, "grounded": False, "unavailable": []}
    state = retrieve_node(state)
    state = analyze_node(state)
    state = validate_node(state)
    state = generate_node(state)
    return state


def build_graph():
    try:
        from langgraph.graph import END, StateGraph

        graph = StateGraph(InsightState)
        graph.add_node("retrieve", retrieve_node)
        graph.add_node("analyze", analyze_node)
        graph.add_node("validate", validate_node)
        graph.add_node("generate", generate_node)
        graph.set_entry_point("retrieve")
        graph.add_edge("retrieve", "analyze")
        graph.add_edge("analyze", "validate")
        graph.add_edge("validate", "generate")
        graph.add_edge("generate", END)
        return graph.compile()
    except Exception:
        class _Fallback:
            def invoke(self, state: dict[str, Any]) -> InsightState:
                return _run_pipeline(state.get("question", ""))

        return _Fallback()


INSIGHT_GRAPH = build_graph()


def run_insight(question: str) -> InsightState:
    result = INSIGHT_GRAPH.invoke({"question": question})
    return result
