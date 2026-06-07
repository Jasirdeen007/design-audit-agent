# Backend

FastAPI backend entrypoints and transport code:

- `main.py` starts FastAPI and mounts all Level 1, Level 2, and Level 3 routes.
- `backend/app.py` re-exports `main.app` for deployment tools that expect a package entrypoint.
- `level1/api/routes.py` exposes Level 1 screenshot audit endpoints.
- `level2/api/routes_l2.py` exposes Level 2 screenshot comparison endpoints.
- `level3/api/routes_l3.py` exposes Level 3 autonomous scan endpoints.
- `utils/` contains logging and image utilities used by the backend.

Run either:

```bash
uvicorn main:app --reload --port 8001
```

or:

```bash
uvicorn backend.app:app --reload --port 8001
```
