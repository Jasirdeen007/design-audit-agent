"""Backward-compatible Streamlit launcher.

Prefer running ``streamlit run frontend/streamlit_app.py``. This wrapper keeps
older commands working.
"""

from frontend import streamlit_app  # noqa: F401
