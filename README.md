# Design Audit Agent - Levels 1, 2, and 3

AI agent that analyzes UI screenshots with Groq vision models.

- **Level 1:** single screenshot design audit.
- **Level 2:** before/after screenshot comparison with improvement, regression, and neutral classification.
- **Level 3:** autonomous browser-based UI regression scans with login, baseline storage, dynamic masking, and HTML/JSON reports.

Both levels evaluate Visual Hierarchy, WCAG AA Contrast, Spacing, Alignment, and Consistency.

## Setup

```bash
cd design-audit-agent
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium
```

## Configure Environment

Copy `.env.example` to `.env` and replace the placeholder key.

```bash
copy .env.example .env
```

Set your Groq API key:

- `GROQ_API_KEY=your_real_key_here`

For the Level 3 example config, also set:

- `SCAN_USERNAME=tomsmith`
- `SCAN_PASSWORD=SuperSecretPassword!`

These are not your Groq credentials. They are demo login credentials for
`https://the-internet.herokuapp.com/login`, a public test site used by the Level 3
example config. For your own website, replace them with environment variables for
your test account, for example `SCAN_USERNAME=qa_user@example.com`.

## Run

```bash
uvicorn main:app --reload --port 8001
```

On Windows, restart FastAPI after installing Playwright or after pulling code
changes. Level 3 uses Playwright, which must run with a Windows event loop that
supports subprocesses; `main.py` sets that policy during startup.

Open:

- API docs: `http://localhost:8001/docs`
- Upload UI: `http://localhost:8001/ui`

## Run The Streamlit UI

Start the FastAPI server first, then in another terminal run:

```bash
streamlit run streamlit_app.py
```

The Streamlit UI is now organized by sidebar workflow:

- `Level 1 Audit`
- `Level 2 Compare`
- `Level 3 Website Scan`
- `Baselines`
- `History`

You can also run the organized frontend entrypoint:

```bash
streamlit run frontend/streamlit_app.py
```

The Streamlit UI has separate tabs for:

- Level 1: upload one screenshot and download JSON/HTML audit reports.
- Level 2: upload baseline and current screenshots and download JSON/HTML diff reports.
- Level 3: enter a website URL, pages to scan, optional login selectors, viewport settings, and whether to refresh baselines.

For Level 3, the UI writes `config/generated_scan_config.json` and calls the existing FastAPI scan endpoint.

Level 2 direction:

- Baseline = before/original/approved screenshot.
- Current = after/updated/candidate screenshot.
- If the baseline is defective and current fixes it, the expected classification is improvement.
- Use the Streamlit swap checkbox if you accidentally selected the images in reverse order.

## Run With Docker

```bash
docker compose up --build
```

The API will be available at `http://localhost:8001/docs`. Reports are written to the local `output/` folder through the compose volume.

## Analyze A Screenshot

```bash
curl -X POST http://localhost:8001/api/v1/analyze -F "file=@C:\path\to\screenshot.png"
```

## Compare Before / After Screenshots

```bash
curl -X POST http://localhost:8001/api/v1/compare ^
  -F "baseline=@C:\path\to\before.png" ^
  -F "current=@C:\path\to\after.png"
```

You can also use `http://localhost:8001/ui` to upload files from the browser.
For the complete UI across all levels, prefer Streamlit at `http://localhost:8501`.

## Run An Autonomous Level 3 Scan

First run creates baselines. Later runs compare against them.

Level 3 input is website scan configuration, not uploaded screenshots:

- Website URL, for example `https://your-app.example.com`.
- At least 3 pages to scan, for example `/dashboard`, `/settings`, `/billing`.
- Optional login selectors if the site requires auth.
- Dynamic selectors to ignore, such as timestamps, counters, session banners, avatars.
- Viewport size and wait time.

First run behavior:

- Opens the website using Playwright.
- Logs in if auth is enabled.
- Visits the configured pages.
- Captures screenshots.
- Saves those screenshots as current baselines and immutable baseline versions.
- Returns `overall_status: baseline_created`.

Second and later run behavior:

- Captures fresh screenshots.
- Compares them against the stored baselines.
- Skips LLM analysis for tiny pixel diffs below `0.5%`.
- Calls the Level 2 comparison agent only for meaningful visual changes.

If `comparison_report` is `null` in Level 3, it usually means one of these:

- The page just created or refreshed a baseline.
- The page pixel diff was below `0.5%`, so the agent correctly skipped the LLM call.
- The page capture failed, in which case `error` explains why.

To try a different website in Streamlit:

- Enter the new website URL.
- Edit the pages table to at least 3 real paths on that site.
- Use `body` as a safe wait selector if you do not know a specific selector yet.
- Add dynamic ignore selectors such as `header`, `footer`, `.timestamp`, `.avatar`, `.counter`.
- Turn off authentication if the site is public.
- If auth is needed, provide the login URL and CSS selectors, and set username/password env vars in `.env`.

Correct demo Level 3 inputs:

- Website URL: `https://the-internet.herokuapp.com`
- Page 1: `/secure`, name `Authenticated Secure Area`, page ID `secure_home`, wait selector `.flash.success`, ignore selector `.flash`
- Page 2: `/checkboxes`, name `Checkboxes`, page ID `checkboxes`, wait selector `form#checkboxes`, ignore selector `footer`
- Page 3: `/login`, name `Login Form`, page ID `login_form`, wait selector `#login`, ignore selectors `.flash, footer`
- Auth enabled
- Login URL: `https://the-internet.herokuapp.com/login`
- Username selector: `#username`
- Password selector: `#password`
- Submit selector: `button[type=submit]`
- Success indicator: `.flash.success`
- `.env`: `SCAN_USERNAME=tomsmith`, `SCAN_PASSWORD=SuperSecretPassword!`

```bash
curl -X POST http://localhost:8001/api/v1/scan/start ^
  -H "Content-Type: application/json" ^
  -d "{\"config_file\":\"config/scan_config.example.json\",\"refresh_baseline\":false}"
```

Refresh all baselines after reviewed changes:

```bash
curl -X POST http://localhost:8001/api/v1/scan/baseline/refresh ^
  -H "Content-Type: application/json" ^
  -d "{\"config_file\":\"config/scan_config.example.json\",\"page_id\":\"all\"}"
```

Useful Level 3 endpoints:

- `POST /api/v1/scan/start`
- `GET /api/v1/scan/baselines`
- `POST /api/v1/scan/baseline/refresh`
- `GET /api/v1/scan/history`

For Level 3, website URLs are accepted through the scan config. The Streamlit UI makes that config from user input, so non-technical users do not need to hand-write JSON.

## Output

- JSON report: `output/audit_{report_id}.json`
- HTML report: `output/audit_{report_id}.html`
- Level 2 JSON report: `output/diff_{report_id}.json`
- Level 2 HTML report: `output/diff_{report_id}.html`
- Level 3 scan reports: `output/scans/SCAN-*.json` and `output/scans/SCAN-*.html`
- Level 3 baselines: `output/baselines/{page_id}.png` and `output/baselines/baselines.db`
- Structured JSON response from `POST /api/v1/analyze`
- Structured JSON response from `POST /api/v1/compare`
- `decision_trace` records observable execution decisions such as image validation, LLM attempt limit, validation result, and report writing.
- `llm_attempts` records the exact number of LLM calls made.

## Guardrails

- One LLM call by default: `ALLOW_LLM_CORRECTION_RETRY=false`.
- Optional correction retry is capped at two total attempts with `ALLOW_LLM_CORRECTION_RETRY=true` and `LLM_MAX_ATTEMPTS=2`.
- Image uploads reject unsupported formats, corrupt files, files over `MAX_IMAGE_SIZE_MB`, and images smaller than 100px.
- LLM output must be valid JSON and match the Pydantic finding schema before a report is produced.
- Level 2 requires at least 5 validated visual differences before producing a diff report.
- Level 2 explicitly flags accessibility regressions such as contrast drops, font size reductions, spacing compression, and tap target reductions.
- Level 3 creates baselines on first run and only calls the LLM when pixel diff is at least `0.5%`.
- Level 3 masks configured dynamic DOM regions before screenshots and applies a second image-level filter before comparison.
- Level 3 uses a bounded LLM retry count through `L2_LLM_MAX_ATTEMPTS`, capped by code to prevent loops.
- Level 3 has a 180-second scan budget for a full scan cycle.
- Failures return structured `success: false` responses instead of unhandled server errors.

## Run Tests

```bash
pytest tests/ -v
```

## Production Readiness Checklist

- Python dependencies are pinned in `requirements.txt`.
- Runtime configuration comes from `.env`; secrets are excluded from Docker and git.
- Docker support is included for repeatable deployment.
- The service exposes `/api/v1/health` for operational checks.
- Reports are persisted as JSON and HTML.
- Guardrails prevent unbounded LLM loops and record `decision_trace` plus `llm_attempts`.

## Architecture

Organized workflow:

- `frontend/`: Streamlit UI entrypoint.
- `backend/`: backend boundary documentation.
- `agent/`: agent-code boundary documentation.
- `database/`: SQLite database documentation.
- `api/`: FastAPI route implementations.
- `core/`: actual agent logic and schemas.
- `utils/`: shared backend utilities.
- `output/`: generated reports, screenshots, baselines, and SQLite DB.

Important files:

- `main.py`: FastAPI app startup
- `streamlit_app.py`: root Streamlit UI entrypoint for all levels
- `frontend/streamlit_app.py`: organized Streamlit UI entrypoint
- `api/routes.py`: Level 1 endpoint
- `api/routes_l2.py`: Level 2 endpoint
- `api/routes_l3.py`: Level 3 endpoints
- `core/schemas.py`: Pydantic contracts shared by future levels
- `core/schemas_l2.py`: Level 2 comparison contracts
- `core/schemas_l3.py`: Level 3 scan contracts
- `core/prompt_builder.py`: Level 1 prompt construction
- `core/prompt_builder_l2.py`: Level 2 comparison prompt construction
- `core/prompt_builder_l3.py`: Level 3 regression context prompt
- `core/browser.py`: Playwright browser automation
- `core/baseline_store.py`: SQLite baseline and scan history store
- `core/dynamic_filter.py`: image-level dynamic content filtering and pixel diff
- `core/scan_engine.py`: Level 3 scan orchestration
- `core/llm_client.py`: Groq vision wrapper
- `core/validator.py`: LLM JSON parsing and validation
- `core/report_generator.py`: JSON and HTML report generation
- `utils/image_utils.py`: Image loading, validation, resizing, encoding
- `utils/logger.py`: Structured JSON logging

Database:

- The database is SQLite.
- Default DB file: `output/baselines/baselines.db`.
- It stores Level 3 baseline metadata and scan history.
- Baseline screenshots are stored as PNG files in `output/baselines/`.
- Immutable baseline history is stored in `output/baselines/versions/`.
