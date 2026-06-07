# Agent Code

The agent implementation lives in `core/`:

- `llm_client.py` talks to Groq vision models.
- `prompt_builder.py`, `prompt_builder_l2.py`, and `prompt_builder_l3.py` define agent instructions.
- `schemas.py`, `schemas_l2.py`, and `schemas_l3.py` define validation contracts.
- `validator.py` parses and validates LLM JSON.
- `browser.py`, `scan_engine.py`, `dynamic_filter.py`, and `baseline_store.py` implement Level 3 autonomy.
- `report_generator.py` writes JSON and HTML reports.

This folder documents the boundary: `core/` is the decision-making agent layer,
while `api/` is transport and `frontend/` is UI.
