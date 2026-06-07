# Backend

FastAPI backend files currently live at the project root and in `api/`:

- `main.py` starts FastAPI and mounts all Level 1, Level 2, and Level 3 routes.
- `api/routes.py` exposes Level 1 screenshot audit endpoints.
- `api/routes_l2.py` exposes Level 2 screenshot comparison endpoints.
- `api/routes_l3.py` exposes Level 3 autonomous scan endpoints.
- `utils/` contains logging and image utilities used by the backend.

The backend is intentionally kept import-compatible with the existing tests and
demo commands.
