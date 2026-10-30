# Product development plan

Each round completes one feature or repair. Future items are planned, not implemented claims.

## Current round

github-skill-discovery

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

### github-skill-discovery — GitHub skill discovery with sparse checkout

Status: done

Acceptance:
- GitHub API client with authentication and rate limit handling
- Sparse checkout using --filter=blob:none to download only skill directories
- SKILL.md parsing with frontmatter extraction (name, description, version, author, license, tags)
- Skill discovery endpoint: POST /api/skills/discover with GitHub repo URL
- Skill listing endpoint: GET /api/skills with pagination and filtering
- Skill detail endpoint: GET /api/skills/{id}
- Search endpoint: GET /api/skills/search?q=...
- Skills persisted to database with content hash for change detection
- Frontend: Discover page to enter GitHub repo URL and trigger discovery
- Frontend: Skills list page with search, filter, pagination
- Frontend: Skill detail page showing parsed metadata and README

Implementation: `backend/app/services/github_service.py`, `backend/app/services/skill_parser.py`, `backend/app/api/skills.py`, `backend/tests/test_github_service.py`, `backend/tests/test_skill_parser.py`, `backend/tests/test_skills_api.py`, `frontend/src/pages/DiscoverPage.tsx`, `frontend/src/pages/SkillsListPage.tsx`, `frontend/src/pages/SkillDetailPage.tsx`, `frontend/src/components/SkillCard.tsx`, `frontend/src/components/SkillSearch.tsx`

Tests: `backend/tests/test_github_service.py`, `backend/tests/test_skills_api.py`

### skill-installation — Skill installation with lockfile

Status: planned

Acceptance:
- Skill installation endpoint: POST /api/skills/{id}/install
- Skills-lock.json created/updated with installed skill hashes
- Hash verification on installation
- Frontend: Install button on skill cards and detail page
- Frontend: Installations list in dashboard
- Uninstall endpoint and UI

