# Product development plan

Each round completes one feature or repair. Future items are planned, not implemented claims.

## Current round

core-skeleton

## Roadmap

### core-skeleton — Core FastAPI/React skeleton with Docker and CI

Status: done

Acceptance:
- FastAPI app starts and serves health endpoint
- React + Vite + TypeScript frontend builds and serves
- Docker compose brings up backend, frontend, Keycloak, PostgreSQL
- CI workflow runs backend tests, frontend build/test, Docker builds
- SQLite persistent storage with basic models
- OIDC Keycloak authentication flow (backend-managed sessions with HttpOnly cookies)

Implementation: `backend/app/main.py`, `backend/app/core/config.py`, `backend/app/core/database.py`, `backend/app/core/security.py`, `backend/app/api/health.py`, `backend/app/api/auth.py`, `backend/app/models/user.py`, `backend/app/models/skill.py`, `backend/requirements.txt`, `backend/Dockerfile`, `backend/tests/test_health.py`, `backend/tests/test_auth.py`, `backend/tests/test_database.py`, `frontend/package.json`, `frontend/vite.config.ts`, `frontend/src/main.tsx`, `frontend/src/App.tsx`, `frontend/src/api/client.ts`, `frontend/Dockerfile`, `frontend/src/App.test.tsx`, `compose.yaml`, `.github/workflows/ci.yml`, `.env.example`, `.gitignore`, `README.md`, `LICENSE`, `CHANGELOG.md`, `pyproject.toml`, `portfolio.json`

Tests: `backend/tests/test_health.py`, `backend/tests/test_auth.py`, `backend/tests/test_database.py`, `frontend/src/App.test.tsx`

