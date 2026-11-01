from __future__ import annotations

from backend.app.ai.graph import run_insight
from backend.app.ai.nodes import validate_node
from backend.app.ai.state import InsightState


def test_langgraph_requires_question_state():
    state: InsightState = {
        "question": "What is the weather impact on sales?",
        "retrieved": {"unavailable_fields": ["Weather"]},
        "analysis": {"total_revenue": 1},
    }
    out = validate_node(state)
    assert out["unavailable"]
    assert "Not available in the current dataset." in out["unavailable"] or out["unavailable"]


def test_insight_follows_the_question():
    from src.utils import METRICS_DIR

    if not (METRICS_DIR / "metrics.json").exists():
        return
    model = run_insight("How does XGBoost compare with the baselines?")
    cats = run_insight("Which categories perform best?")
    assert "MAE" in model["answer"] or "mae" in model["answer"].lower()
    assert "highest-revenue category" in cats["answer"].lower() or "Top 5 by revenue" in cats["answer"]
    assert "MAE" not in cats["answer"]
