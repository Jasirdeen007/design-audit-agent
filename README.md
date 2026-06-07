# Design Audit Agent - Levels 1, 2, and 3

AI agent that analyzes UI screenshots with Groq vision models.

- **Level 1:** single screenshot design audit.
- **Level 2:** before/after screenshot comparison with improvement, regression, and neutral classification.
- **Level 3:** autonomous browser-based UI regression scans with login, baseline storage, dynamic masking, and HTML/JSON reports.

All levels evaluate Visual Hierarchy, WCAG AA Contrast, Spacing, Alignment, and Consistency.

## Fastest Setup: Docker

Docker is the recommended way to run this project on another system. It installs
Python dependencies, Playwright browser dependencies, Chromium, FastAPI, and
Streamlit inside containers.

Prerequisites:

- Docker Desktop or Docker Engine
- A Groq API key

```bash
cd design-audit-agent
copy .env.example .env
```

Edit `.env` and set:

- `GROQ_API_KEY=your_real_key_here`

For authenticated Level 3 scans, also set:

- `SCAN_USERNAME=your_test_account_username`
- `SCAN_PASSWORD=your_test_account_password`

These are not Groq credentials. Use a non-production test account for the website
being scanned.

Start the full project:

```bash
docker compose up --build
```

Open:

- Streamlit UI: `http://localhost:8501`
- API docs: `http://localhost:8001/docs`
- Health check: `http://localhost:8001/api/v1/health`

Generated reports, screenshots, baselines, and the SQLite database are written
to the local `output/` folder through Docker volumes.

Stop the project:

```bash
docker compose down
```

Rebuild after code or dependency changes:

```bash
docker compose up --build
```

If the API container previously failed, reset the old containers before rebuilding:

```bash
docker compose down
docker compose build --no-cache
docker compose up
```

The Docker image runs Uvicorn with `--loop asyncio` so Playwright and the Level 3
scan thread work consistently without `uvloop`/`nest_asyncio` conflicts.

## Optional Local Setup

Use this only if you do not want Docker.

```bash
cd design-audit-agent
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium
```

Start the backend:

```bash
uvicorn backend.app:app --reload --port 8001
```

Start Streamlit in another terminal:

```bash
streamlit run frontend/streamlit_app.py
```

On Windows, restart FastAPI after installing Playwright or after pulling code
changes. Level 3 uses Playwright, which must run with a Windows event loop that
supports subprocesses; `main.py` sets that policy during startup.

Open:

- API docs: `http://localhost:8001/docs`
- Upload UI: `http://localhost:8001/ui`
- Streamlit UI: `http://localhost:8501`

The Streamlit UI is now organized by sidebar workflow:

- `Level 1 Audit`
- `Level 2 Compare`
- `Level 3 Website Scan`
- `Baselines`
- `History`

The Streamlit UI has separate workflows for:

- Level 1: upload one screenshot and download JSON/HTML audit reports.
- Level 2: upload baseline and current screenshots and download JSON/HTML diff reports.
- Level 3: enter a website URL, at least 3 page paths, optional login selectors, viewport settings, and whether to refresh baselines.

Uploaded screenshots are shown as small previews so they do not dominate the
workspace. The UI also creates a session id in the URL and stores current uploads
and reports under `output/ui_sessions/`, so refreshing the browser preserves the
current activity. Use the sidebar `Start new session` button when you want a
clean workspace.

In Level 3, `page_id` is generated automatically from the `Report name`. Baseline
storage is still scoped by website domain internally, so a `Home` page on one
website cannot collide with a `Home` page on another website.

For Level 3, the UI writes `config/generated_scan_config.json` and calls the existing FastAPI scan endpoint.

Level 2 direction:

- Baseline = before/original/approved screenshot.
- Current = after/updated/candidate screenshot.
- If the baseline is defective and current fixes it, the expected classification is improvement.
- Use the Streamlit swap checkbox if you accidentally selected the images in reverse order.

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
- Use clear report names such as `Home`, `Pricing`, and `Contact`; these become the page IDs.
- Turn off authentication if the site is public.
- If auth is needed, provide the login URL and CSS selectors, and set username/password env vars in `.env`.

The UI uses `body` as the default readiness selector and masks common dynamic
regions such as `header` and `footer` automatically. Advanced scan configuration
is still available through `config/scan_config.example.json` for teams that need
custom wait selectors or dynamic masking rules.

Example authenticated Level 3 inputs:

- Website URL: `https://the-internet.herokuapp.com`
- Page 1: `/secure`, report name `Authenticated Secure Area`
- Page 2: `/checkboxes`, report name `Checkboxes`
- Page 3: `/login`, report name `Login Form`
- Auth enabled
- Login URL: `https://the-internet.herokuapp.com/login`
- Username selector: `#username`
- Password selector: `#password`
- Submit selector: `button[type=submit]`
- Success indicator: `.flash.success`
- `.env`: `SCAN_USERNAME=your_test_account_username`, `SCAN_PASSWORD=your_test_account_password`

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
- Docker installs Playwright Chromium and OS browser dependencies, so Level 3 runs on fresh machines.
- Docker Compose starts both services: `api` on port `8001` and `ui` on port `8501`.
- Runtime configuration comes from `.env`; secrets are excluded from Docker and git.
- Docker support is included for repeatable deployment.
- The service exposes `/api/v1/health` for operational checks.
- Reports are persisted as JSON and HTML.
- Guardrails prevent unbounded LLM loops and record `decision_trace` plus `llm_attempts`.

## Evaluation Alignment

- **Code quality and architecture:** FastAPI transport (`api/`), agent logic (`core/`), UI (`frontend/`), database boundary (`database/`), schemas, validators, prompts, and report generation are separated.
- **Real-world complexity:** unsupported images, corrupt uploads, invalid model JSON, auth failure, browser capture failure, missing env credentials, tiny pixel diffs, and dynamic content are handled with explicit errors or skip decisions.
- **Agentic design thinking:** every report includes `decision_trace`; LLM calls are bounded; Level 3 only calls the model after measurable visual diff evidence.
- **Completeness:** Levels 1, 2, and 3 produce structured JSON plus human-readable HTML reports and have Streamlit workflows for non-technical users.
- **Production readiness:** Docker, `.env.example`, health checks, tests, SQLite baseline persistence, versioned baselines, and package entrypoints are included.

## Architecture

Organized workflow:

- `frontend/`: Streamlit UI entrypoint.
- `backend/`: FastAPI package entrypoint and backend documentation.
- `agent/`: agent-code package boundary and documentation.
- `database/`: SQLite database package boundary and documentation.
- `api/`: FastAPI route implementations.
- `core/`: actual agent logic and schemas.
- `utils/`: shared backend utilities.
- `output/`: generated reports, screenshots, baselines, and SQLite DB.

Important files:

- `main.py`: FastAPI app startup
- `Dockerfile`: portable runtime image with FastAPI, Streamlit, Playwright, and Chromium
- `docker-compose.yml`: starts the API and Streamlit UI together
- `streamlit_app.py`: backward-compatible root Streamlit launcher
- `frontend/streamlit_app.py`: Streamlit UI entrypoint for all levels
- `backend/app.py`: deployable FastAPI app export
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
