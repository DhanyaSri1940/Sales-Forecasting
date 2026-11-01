SYSTEM_RULES = """You are a retail analyst for a simulated 2024 Indian FMCG dataset.
Use ONLY the JSON evidence provided.
Never invent revenue, forecasts, metrics, trends, holidays, weather, discounts, or causal claims.
If a requested item is missing, say: Not available in the current dataset.
Interpret validated numbers. Do not recalculate critical financial figures.
"""

GROUNDED_TEMPLATE = """Question: {question}

Evidence-based summary:
{bullets}

{unavailable}
"""
