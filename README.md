# Design Audit Agent - Levels 1 and 2

AI agent that analyzes UI screenshots with Groq vision models.

- **Level 1:** single screenshot design audit.
- **Level 2:** before/after screenshot comparison with improvement, regression, and neutral classification.

Both levels evaluate Visual Hierarchy, WCAG AA Contrast, Spacing, Alignment, and Consistency.

## Setup

```bash
cd design-audit-agent
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

## Configure Environment

Copy `.env.example` to `.env` and replace the placeholder key.

```bash
copy .env.example .env
```

Set your Groq API key:

- `GROQ_API_KEY=your_real_key_here`

## Run

```bash
uvicorn main:app --reload --port 8001
```

Open:

- API docs: `http://localhost:8001/docs`
- Upload UI: `http://localhost:8001/ui`

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

## Output

- JSON report: `output/audit_{report_id}.json`
- HTML report: `output/audit_{report_id}.html`
- Level 2 JSON report: `output/diff_{report_id}.json`
- Level 2 HTML report: `output/diff_{report_id}.html`
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

- `main.py`: FastAPI app startup
- `api/routes.py`: HTTP endpoints
- `api/routes_l2.py`: before/after comparison endpoint
- `core/schemas.py`: Pydantic contracts shared by future levels
- `core/schemas_l2.py`: Level 2 comparison contracts
- `core/prompt_builder.py`: Level 1 prompt construction
- `core/prompt_builder_l2.py`: Level 2 comparison prompt construction
- `core/llm_client.py`: Groq vision wrapper
- `core/validator.py`: LLM JSON parsing and validation
- `core/report_generator.py`: JSON and HTML report generation
- `utils/image_utils.py`: Image loading, validation, resizing, encoding
- `utils/logger.py`: Structured JSON logging

## Level 3 Extension Points

- Level 3 adds browser automation and baseline storage
- Level 3 can reuse `ComparisonFinding` and `DiffReport` from `core/schemas_l2.py`
