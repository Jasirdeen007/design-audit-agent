"""Streamlit UI for the Design Audit Agent."""

from __future__ import annotations

import json
import os
from pathlib import Path
from urllib.parse import urlparse

import httpx
import streamlit as st


DEFAULT_API_BASE = os.getenv("STREAMLIT_API_BASE", "http://localhost:8001")
CONFIG_PATH = Path("config/generated_scan_config.json")


st.set_page_config(page_title="Design Audit Agent", page_icon="DA", layout="wide")
st.markdown(
    """
    <style>
      .block-container { max-width: 1140px; padding-top: 1.4rem; }
      [data-testid="stMetric"] {
        background: rgba(148, 163, 184, 0.08);
        border: 1px solid rgba(148, 163, 184, 0.35);
        border-radius: 8px;
        padding: 10px 12px;
      }
      .hint {
        background: rgba(148, 163, 184, 0.10);
        border: 1px solid rgba(148, 163, 184, 0.35);
        border-radius: 8px;
        padding: 12px 14px;
        margin: 8px 0 16px;
      }
      .small { opacity: 0.75; font-size: 0.9rem; }
      .status-note {
        border-left: 3px solid #38bdf8;
        padding: 8px 10px;
        background: rgba(56, 189, 248, 0.10);
        border-radius: 4px;
        margin: 8px 0;
      }
    </style>
    """,
    unsafe_allow_html=True,
)


def api_url(api_base: str, endpoint: str) -> str:
    return f"{api_base.rstrip('/')}{endpoint}"


def get_json(api_base: str, endpoint: str) -> dict | list:
    with httpx.Client(timeout=30) as client:
        response = client.get(api_url(api_base, endpoint))
        response.raise_for_status()
        return response.json()


def post_json(api_base: str, endpoint: str, payload: dict) -> dict:
    with httpx.Client(timeout=240) as client:
        response = client.post(api_url(api_base, endpoint), json=payload)
        response.raise_for_status()
        return response.json()


def post_files(api_base: str, endpoint: str, files: dict) -> dict:
    with httpx.Client(timeout=240) as client:
        response = client.post(api_url(api_base, endpoint), files=files)
        response.raise_for_status()
        return response.json()


def slug(value: str) -> str:
    parsed = urlparse(value)
    text = parsed.path.strip("/") or parsed.netloc or value or "page"
    cleaned = "".join(ch.lower() if ch.isalnum() else "_" for ch in text)
    return cleaned.strip("_") or "page"


def download_reports(report: dict, prefix: str) -> None:
    cols = st.columns(2)
    for col, label, key, mime in [
        (cols[0], "Download JSON", "json_report_path", "application/json"),
        (cols[1], "Download HTML", "html_report_path", "text/html"),
    ]:
        path = report.get(key)
        if path and Path(path).exists():
            col.download_button(
                label,
                Path(path).read_bytes(),
                file_name=Path(path).name,
                mime=mime,
                key=f"{prefix}-{key}-{path}",
            )
        elif path:
            col.caption(f"{label}: `{path}`")


def show_error_response(result: dict) -> bool:
    if result.get("report"):
        return False
    st.error(result.get("error") or "Request failed")
    if result.get("error_detail"):
        st.code(result["error_detail"])
    return True


def render_l1(api_base: str) -> None:
    st.header("Level 1: Single Screenshot Audit")
    st.markdown('<div class="hint">Upload one UI screenshot. The agent returns visible design issues across hierarchy, contrast, spacing, alignment, and consistency.</div>', unsafe_allow_html=True)
    image = st.file_uploader("Screenshot", type=["png", "jpg", "jpeg", "webp"])
    if image:
        st.image(image, caption=image.name, use_column_width=True)
    if st.button("Analyze screenshot", type="primary", disabled=image is None):
        files = {"file": (image.name, image.getvalue(), image.type or "application/octet-stream")}
        with st.spinner("Analyzing screenshot..."):
            result = post_files(api_base, "/api/v1/analyze", files)
        if show_error_response(result):
            return
        report = result["report"]
        summary = report.get("summary", {})
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Findings", summary.get("total", 0))
        c2.metric("High", summary.get("high", 0))
        c3.metric("Flagged", summary.get("flagged_for_review", 0))
        c4.metric("LLM Attempts", report.get("llm_attempts", 0))
        for finding in report.get("findings", []):
            with st.expander(f"{finding['finding_id']} | {finding['severity']} | {finding['principle']}"):
                st.write(f"Location: {finding['location']}")
                st.write(f"Observation: {finding['observation']}")
                st.write(f"Impact: {finding['user_impact']}")
                st.write(f"Recommendation: {finding['recommendation']}")
                st.write(f"Confidence: {finding['confidence']}%")
        download_reports(report, "l1")


def render_l2(api_base: str) -> None:
    st.header("Level 2: Before / After Comparison")
    st.markdown(
        '<div class="hint"><strong>Direction matters:</strong> baseline = before/old/approved, current = after/updated/candidate. If current fixes a baseline defect, the expected classification is improvement.</div>',
        unsafe_allow_html=True,
    )
    col_a, col_b = st.columns(2)
    baseline = col_a.file_uploader("Baseline screenshot", type=["png", "jpg", "jpeg", "webp"], key="baseline")
    current = col_b.file_uploader("Current screenshot", type=["png", "jpg", "jpeg", "webp"], key="current")
    swap = st.checkbox("Swap baseline and current before comparing")
    if baseline:
        col_a.image(baseline, caption=baseline.name, use_column_width=True)
    if current:
        col_b.image(current, caption=current.name, use_column_width=True)
    if st.button("Compare screenshots", type="primary", disabled=baseline is None or current is None):
        left = current if swap else baseline
        right = baseline if swap else current
        files = {
            "baseline": (left.name, left.getvalue(), left.type or "application/octet-stream"),
            "current": (right.name, right.getvalue(), right.type or "application/octet-stream"),
        }
        with st.spinner("Comparing screenshots..."):
            result = post_files(api_base, "/api/v1/compare", files)
        if show_error_response(result):
            return
        report = result["report"]
        verdict = report["verdict"]
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Verdict", verdict["net_result"])
        c2.metric("Regressions", verdict["regression_count"])
        c3.metric("Improvements", verdict["improvement_count"])
        c4.metric("Accessibility", verdict["accessibility_regressions_count"])
        st.write(verdict["summary"])
        for finding in report.get("findings", []):
            with st.expander(f"{finding['finding_id']} | {finding['change_direction']} | {finding['severity']}"):
                st.write(f"Location: {finding['location']}")
                st.write(f"Change: {finding['change_summary']}")
                st.write(f"Reasoning: {finding['reasoning']}")
                st.write(f"Confidence: {finding['confidence']}%")
        download_reports(report, "l2")


def default_pages() -> list[dict]:
    return [
        {"url": "/secure", "name": "Authenticated Secure Area", "page_id": "secure_home", "wait_for_selector": ".flash.success", "dynamic_selectors": ".flash"},
        {"url": "/checkboxes", "name": "Checkboxes", "page_id": "checkboxes", "wait_for_selector": "form#checkboxes", "dynamic_selectors": "footer"},
        {"url": "/login", "name": "Login Form", "page_id": "login_form", "wait_for_selector": "#login", "dynamic_selectors": ".flash, footer"},
    ]


def rows_to_pages(rows: list[dict]) -> list[dict]:
    pages = []
    for row in rows:
        url = str(row.get("url") or "").strip()
        if not url:
            continue
        page_id = str(row.get("page_id") or slug(url)).strip()
        dynamic = str(row.get("dynamic_selectors") or "")
        pages.append(
            {
                "page_id": page_id,
                "url": url,
                "name": str(row.get("name") or page_id).strip(),
                "wait_for_selector": str(row.get("wait_for_selector") or "").strip() or None,
                "dynamic_selectors": [item.strip() for item in dynamic.split(",") if item.strip()],
                "scroll_to_top": True,
            }
        )
    return pages


def comparison_status(page_result: dict) -> str:
    if page_result.get("error"):
        return "error"
    if page_result.get("comparison_report"):
        return page_result["comparison_report"]["verdict"]["net_result"]
    if not page_result.get("baseline_exists"):
        return "baseline_created_or_refreshed"
    diff = page_result.get("pixel_diff_percentage")
    if diff is not None:
        return f"not_run_pixel_diff_below_threshold_{diff}%"
    return "not_run"


def default_pages_for_url(target_url: str) -> list[dict]:
    host = urlparse(target_url).netloc
    if "the-internet.herokuapp.com" in host:
        return default_pages()
    return [
        {"url": "/", "name": "Home", "page_id": "home", "wait_for_selector": "body", "dynamic_selectors": "header, footer"},
        {"url": "/about", "name": "About", "page_id": "about", "wait_for_selector": "body", "dynamic_selectors": "header, footer"},
        {"url": "/contact", "name": "Contact", "page_id": "contact", "wait_for_selector": "body", "dynamic_selectors": "header, footer"},
    ]


def render_l3(api_base: str) -> None:
    st.header("Level 3: Autonomous Website Regression Scan")
    st.markdown(
        '<div class="hint">Input is a website URL plus at least 3 page paths. First run creates baselines. Later runs compare live screenshots only when pixel diff is at least 0.5%.</div>',
        unsafe_allow_html=True,
    )
    target_url = st.text_input("Website URL", "https://the-internet.herokuapp.com")
    st.caption("For a different site, replace the URL and edit the pages table to real paths on that site. Disable auth if the site is public.")
    st.subheader("Pages")
    page_rows = st.data_editor(
        default_pages_for_url(target_url),
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "url": st.column_config.TextColumn("URL or path", required=True),
            "name": st.column_config.TextColumn("Report name"),
            "page_id": st.column_config.TextColumn("Stable page ID"),
            "wait_for_selector": st.column_config.TextColumn("Wait selector"),
            "dynamic_selectors": st.column_config.TextColumn("Ignore selectors"),
        },
        key="l3-pages",
    )
    pages = rows_to_pages(page_rows)

    with st.expander("Authentication", expanded=True):
        use_auth = st.checkbox("Website requires login", value=True)
        col1, col2 = st.columns(2)
        login_url = col1.text_input("Login URL", "https://the-internet.herokuapp.com/login")
        success_indicator = col2.text_input("Success indicator", ".flash.success")
        username_selector = col1.text_input("Username selector", "#username")
        password_selector = col2.text_input("Password selector", "#password")
        submit_selector = col1.text_input("Submit selector", "button[type=submit]")
        username_env = col1.text_input("Username env var", "SCAN_USERNAME")
        password_env = col2.text_input("Password env var", "SCAN_PASSWORD")
        st.caption("For the demo site, .env should contain SCAN_USERNAME=tomsmith and SCAN_PASSWORD=SuperSecretPassword!")
        if not use_auth:
            st.caption("Auth fields are ignored when login is disabled.")

    with st.expander("Scan settings"):
        c1, c2, c3 = st.columns(3)
        viewport_width = c1.number_input("Viewport width", 320, 3840, 1440, step=10)
        viewport_height = c2.number_input("Viewport height", 320, 2160, 900, step=10)
        wait_ms = c3.number_input("Wait after navigation ms", 0, 10000, 1500, step=100)
        refresh_baseline = st.checkbox("Refresh baselines instead of comparing")

    config = {
        "target_url": target_url,
        "pages": pages,
        "viewport_width": int(viewport_width),
        "viewport_height": int(viewport_height),
        "wait_after_navigation_ms": int(wait_ms),
        "baseline_dir": "output/baselines",
        "scan_output_dir": "output/scans",
    }
    if use_auth:
        config["auth"] = {
            "login_url": login_url,
            "username_selector": username_selector,
            "password_selector": password_selector,
            "submit_selector": submit_selector,
            "success_indicator": success_indicator,
            "username": username_env,
            "password": password_env,
        }

    with st.expander("Preview generated config"):
        st.json(config)

    if st.button("Start website scan", type="primary"):
        if not target_url or len(pages) < 3:
            st.error("Level 3 requires a website URL and at least 3 configured pages.")
            return
        CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        CONFIG_PATH.write_text(json.dumps(config, indent=2), encoding="utf-8")
        with st.spinner("Running Playwright scan..."):
            result = post_json(api_base, "/api/v1/scan/start", {"config_file": str(CONFIG_PATH), "refresh_baseline": refresh_baseline})
        if show_error_response(result):
            return
        report = result["report"]
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Status", report["overall_status"])
        c2.metric("Pages", report["pages_scanned"])
        c3.metric("Regressions", report["pages_with_regressions"])
        c4.metric("Duration", f"{report['total_duration_seconds']}s")
        for page in report.get("page_results", []):
            with st.expander(f"{page['page_id']} | {page.get('page_url')}"):
                status = comparison_status(page)
                st.markdown(f'<div class="status-note"><strong>Comparison status:</strong> {status}</div>', unsafe_allow_html=True)
                st.write(f"Screenshot: {page.get('screenshot_path')}")
                st.write(f"Baseline: {page.get('baseline_screenshot_path')}")
                st.write(f"Pixel diff: {page.get('pixel_diff_percentage')}")
                st.write(f"Dynamic regions filtered: {page.get('dynamic_regions_filtered')}")
                if page.get("error"):
                    st.error(page["error"])
                if page.get("comparison_report"):
                    st.write(page["comparison_report"]["verdict"]["summary"])
                else:
                    st.caption("No comparison report means the page created/refreshed a baseline or the visual diff was below the LLM threshold.")
        download_reports(report, "l3")


def render_baselines(api_base: str) -> None:
    st.header("Level 3 Baselines")
    if st.button("Load baselines", type="primary"):
        st.json(get_json(api_base, "/api/v1/scan/baselines"))


def render_history(api_base: str) -> None:
    st.header("Scan History")
    if st.button("Load history", type="primary"):
        st.json(get_json(api_base, "/api/v1/scan/history"))


with st.sidebar:
    st.title("Design Audit")
    api_base = st.text_input("FastAPI URL", DEFAULT_API_BASE)
    page = st.radio("Workflow", ["Level 1 Audit", "Level 2 Compare", "Level 3 Website Scan", "Baselines", "History"])
    if st.button("Check API"):
        try:
            health = get_json(api_base, "/api/v1/health")
            st.success(f"Online: {health.get('status')}")
            st.caption(health.get("llm_model", ""))
        except Exception as exc:
            st.error(f"API unavailable: {exc}")

if page == "Level 1 Audit":
    render_l1(api_base)
elif page == "Level 2 Compare":
    render_l2(api_base)
elif page == "Level 3 Website Scan":
    render_l3(api_base)
elif page == "Baselines":
    render_baselines(api_base)
else:
    render_history(api_base)
