# Design Audit Agent

Design Audit Agent is an AI-assisted visual quality platform for reviewing UI screenshots, comparing before/after design changes, and running browser-based visual regression scans across live websites.

The project combines FastAPI, Streamlit, Playwright, SQLite baseline storage, and Groq vision models to support three review workflows from one deployable application.

## Capabilities

| Level | Workflow | Purpose |
| --- | --- | --- |
| Level 1 | Single Screenshot Audit | Analyze one UI screenshot and return structured design findings. |
| Level 2 | Before/After Comparison | Compare baseline and current screenshots to classify regressions, improvements, and neutral changes. |
| Level 3 | Autonomous Website Scan | Visit configured website pages, capture screenshots, maintain baselines, and detect visual regressions. |

All levels evaluate common design quality dimensions including visual hierarchy, WCAG AA contrast, spacing, alignment, and consistency.

## Key Features

- Streamlit review workspace for non-technical users.
- FastAPI backend with documented REST endpoints.
- Groq vision model integration for design reasoning.
- Playwright-powered browser automation for Level 3 scans.
- Authenticated website scan support through configurable CSS selectors.
- SQLite baseline database with versioned baseline screenshots.
- Dynamic DOM masking and image-level filtering to reduce false positives.
- JSON and HTML report generation for every workflow.
- Guardrails for file validation, bounded LLM calls, structured model output, and controlled scan execution.
- Docker Compose setup for repeatable deployment.

## Architecture

```text
design-audit-agent/
+-- backend/              # FastAPI application export
+-- core/                 # Shared LLM client, report generation, and guardrails
+-- frontend/             # Streamlit application
+-- level1/               # Single screenshot audit workflow
+-- level2/               # Before/after comparison workflow
+-- level3/               # Autonomous scan workflow
+-- utils/                # Shared utilities
+-- config/               # Scan configuration examples and generated config
+-- output/               # Reports, screenshots, baselines, and scan history
+-- docker-compose.yml    # API and UI service orchestration
+-- Dockerfile            # Runtime image with Playwright browser dependencies
+-- main.py               # FastAPI app startup and router registration
```

### Service Layout

| Service | Technology | Default URL |
| --- | --- | --- |
| Streamlit UI | Streamlit | `http://localhost:8501` |
| API | FastAPI / Uvicorn | `http://localhost:8001` |
| API Docs | OpenAPI / Swagger | `http://localhost:8001/docs` |
| Health Check | FastAPI endpoint | `http://localhost:8001/api/v1/health` |

## Prerequisites

Recommended setup:

- Docker Desktop or Docker Engine
- Groq API key

Optional local setup:

- Python 3.11+
- Playwright Chromium runtime

## Configuration

Create a local environment file from the provided template:

```bash
copy .env.example .env
```

Set the required Groq key:

```env
GROQ_API_KEY=your_real_groq_api_key
```

For authenticated Level 3 scans, configure website test credentials:

```env
SCAN_USERNAME=your_test_username
SCAN_PASSWORD=your_test_password
```

Use a non-production test account for website scans. These credentials are for the scanned website, not for Groq.

## Run With Docker

Docker is the recommended way to run the full application because it installs Python dependencies, Playwright dependencies, Chromium, FastAPI, and Streamlit inside the container image.

```bash
docker compose up --build
```

Open:

- Streamlit UI: `http://localhost:8501`
- API docs: `http://localhost:8001/docs`
- Health check: `http://localhost:8001/api/v1/health`

Stop the application:

```bash
docker compose down
```

Rebuild after dependency or source changes:

```bash
docker compose up --build
```

If you need a clean image rebuild:

```bash
docker compose down
docker compose build --no-cache
docker compose up
```

Generated reports, screenshots, baselines, and SQLite data are persisted to the local `output/` directory through Docker volumes.

## Run Locally Without Docker

Use local setup only when Docker is not available.

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium
```

Start the API:

```bash
uvicorn backend.app:app --reload --port 8001
```

Start Streamlit in a second terminal:

```bash
streamlit run frontend/streamlit_app.py
```

On Windows, restart FastAPI after installing Playwright or pulling changes that affect browser automation.

## Streamlit Workflows

The Streamlit UI is available at `http://localhost:8501` and provides five sidebar workflows:

- `Level 1 Audit`
- `Level 2 Compare`
- `Level 3 Website Scan`
- `Baselines`
- `History`

The UI creates a browser session ID and stores uploaded files and report state under `output/ui_sessions/`. Use `Start new session` in the sidebar to clear the current workspace.

## Level 1: Screenshot Audit

Level 1 accepts a single UI screenshot and returns a structured audit report.

Typical use:

1. Open `Level 1 Audit` in Streamlit.
2. Upload a PNG, JPG, JPEG, or WEBP screenshot.
3. Select `Analyze screenshot`.
4. Review findings and download JSON or HTML reports.

API example:

```bash
curl -X POST http://localhost:8001/api/v1/analyze -F "file=@C:\path\to\screenshot.png"
```

## Level 2: Before/After Comparison

Level 2 compares a baseline screenshot against a current screenshot.

Direction rules:

- Baseline = before, original, or approved screenshot.
- Current = after, updated, or candidate screenshot.
- Improvements, regressions, and neutral changes are classified from baseline to current.
- Use the Streamlit swap option if the images were uploaded in reverse order.

API example:

```bash
curl -X POST http://localhost:8001/api/v1/compare ^
  -F "baseline=@C:\path\to\before.png" ^
  -F "current=@C:\path\to\after.png"
```

## Level 3: Autonomous Website Regression Scan

Level 3 runs a browser-based scan against configured website pages.

The first run creates baselines. Later runs compare new screenshots against stored baselines.

Level 3 supports:

- Website URL input.
- Three or more page paths.
- Optional authentication selectors.
- Viewport width and height settings.
- Navigation wait timing.
- Baseline refresh mode.
- Dynamic selector masking.

### First Run Behavior

- Launches Chromium through Playwright.
- Logs in when authentication is configured.
- Visits each configured page.
- Captures screenshots.
- Saves baseline screenshots and baseline metadata.
- Returns a baseline-created result.

### Later Run Behavior

- Captures fresh screenshots.
- Compares current screenshots against stored baselines.
- Skips LLM analysis when pixel difference is below the configured threshold.
- Calls the comparison agent when meaningful visual changes are detected.
- Stores scan history and downloadable reports.

### Example Level 3 Demo Configuration

Use this sample site to demonstrate authentication and multi-page scanning:

| Field | Value |
| --- | --- |
| Website URL | `https://the-internet.herokuapp.com` |
| Page 1 | `/secure` as `Authenticated Secure Area` |
| Page 2 | `/checkboxes` as `Checkboxes` |
| Page 3 | `/login` as `Login Form` |
| Login URL | `https://the-internet.herokuapp.com/login` |
| Username selector | `#username` |
| Password selector | `#password` |
| Submit selector | `button[type=submit]` |
| Success indicator | `.flash.success` |

Set credentials in `.env`:

```env
SCAN_USERNAME=tomsmith
SCAN_PASSWORD=SuperSecretPassword!
```

Start a scan through the API:

```bash
curl -X POST http://localhost:8001/api/v1/scan/start ^
  -H "Content-Type: application/json" ^
  -d "{\"config_file\":\"config/scan_config.example.json\",\"refresh_baseline\":false}"
```

Refresh baselines after approved UI changes:

```bash
curl -X POST http://localhost:8001/api/v1/scan/baseline/refresh ^
  -H "Content-Type: application/json" ^
  -d "{\"config_file\":\"config/scan_config.example.json\",\"page_id\":\"all\"}"
```

Useful Level 3 endpoints:

| Method | Endpoint | Description |
| --- | --- | --- |
| POST | `/api/v1/scan/start` | Run a website scan. |
| GET | `/api/v1/scan/baselines` | List stored baselines. |
| POST | `/api/v1/scan/baseline/refresh` | Refresh one or all baselines. |
| GET | `/api/v1/scan/history` | View recent scan history. |

## Reports And Output

Generated artifacts are written to `output/`.

| Artifact | Path Pattern |
| --- | --- |
| Level 1 JSON report | `output/audit_*.json` |
| Level 1 HTML report | `output/audit_*.html` |
| Level 2 JSON report | `output/diff_*.json` |
| Level 2 HTML report | `output/diff_*.html` |
| Level 3 JSON report | `output/scans/SCAN-*.json` |
| Level 3 HTML report | `output/scans/SCAN-*.html` |
| Current baselines | `output/baselines/*.png` |
| Baseline versions | `output/baselines/versions/*.png` |
| Baseline database | `output/baselines/baselines.db` |
| Streamlit sessions | `output/ui_sessions/` |

Reports include structured findings, summary metrics, LLM attempt counts, and decision traces where applicable.

## Guardrails And Reliability

- Uploaded images are validated for format, corruption, file size, and minimum dimensions.
- LLM responses must pass JSON parsing and Pydantic schema validation.
- LLM retry behavior is bounded by environment settings and code limits.
- Level 2 requires enough validated visual differences before producing a comparison report.
- Level 3 masks configured dynamic DOM selectors before screenshots.
- Level 3 applies a second image-level filter before pixel comparison.
- Level 3 skips LLM analysis for insignificant pixel differences.
- Level 3 scan cycles have a bounded runtime budget.
- API failures return structured `success: false` responses instead of unhandled errors.

## Testing

Run tests locally:

```bash
pytest tests/ level1/tests/ level2/tests/ level3/tests/ -v
```

Run tests through Docker:

```bash
docker compose run --rm api pytest tests/ level1/tests/ level2/tests/ level3/tests/ -v
```

## Important Files

| File | Purpose |
| --- | --- |
| `main.py` | FastAPI startup, lifespan initialization, and router registration. |
| `backend/app.py` | Deployable FastAPI app export. |
| `frontend/streamlit_app.py` | Streamlit UI for all workflows. |
| `streamlit_app.py` | Backward-compatible Streamlit launcher. |
| `core/llm_client.py` | Groq vision model wrapper. |
| `core/report_generator.py` | JSON and HTML report generation. |
| `level1/api/routes.py` | Level 1 API route. |
| `level2/api/routes_l2.py` | Level 2 API route. |
| `level3/api/routes_l3.py` | Level 3 API routes. |
| `level3/core/browser.py` | Playwright browser automation. |
| `level3/core/baseline_store.py` | SQLite baseline and scan history storage. |
| `level3/core/dynamic_filter.py` | Image-level dynamic filtering and pixel diff. |
| `level3/core/scan_engine.py` | Level 3 scan orchestration. |
| `utils/image_utils.py` | Image loading, validation, resizing, and encoding. |
| `utils/logger.py` | Structured JSON logging. |

## Production Readiness

- Docker image includes runtime dependencies for FastAPI, Streamlit, Playwright, and Chromium.
- Docker Compose starts API and UI services with health checks and persistent volumes.
- Runtime configuration is externalized through `.env`.
- `.env.example` documents required and optional environment variables.
- Generated artifacts are persisted outside containers in `output/`.
- SQLite baseline metadata and versioned baseline files support repeatable regression review.
- API documentation is available through OpenAPI at `/docs`.
- Tests cover shared utilities and level-specific contracts.

## Evaluation Notes

This project is structured to demonstrate three levels of AI-assisted design review:

- Level 1 shows focused visual audit reasoning on a single screenshot.
- Level 2 shows comparative design reasoning with regression and improvement classification.
- Level 3 shows autonomous scan orchestration, browser interaction, baseline persistence, dynamic masking, and selective model invocation.

The system is designed to make AI decisions observable through structured reports, decision traces, bounded model calls, and downloadable artifacts.
