# Changelog

## 1.2.0 — work-in-progress checkpoint

Partial code published for continued development. Known issues: STATUS.md.

## 1.1.0 — work-in-progress checkpoint

Partial code published for continued development. Known issues: STATUS.md.

## 1.0.0 — work-in-progress checkpoint

Partial code published for continued development. Known issues: STATUS.md.

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-10-14

### Added
- Initial FastAPI backend with modular structure (app/, api/, core/, models/, services/)
- React + TypeScript + Vite frontend with dashboard, skill detail, settings pages
- OIDC authentication via Keycloak with PKCE, state, nonce validation
- Backend-managed sessions with HttpOnly SameSite cookies
- Role-based access control (viewer, operator, admin)
- SQLite/PostgreSQL persistence with SQLAlchemy async
- Health and readiness endpoints
- Docker Compose with Keycloak, PostgreSQL, backend, frontend
- CI/CD workflow with backend tests, frontend build/test, Docker builds
- Demo mode for local development (explicitly disabled in production)
- Skill, Installation, and LockfileEntry data models
- Portfolio.json with schema v1 metadata

### Security
- CSRF protection via double-submit cookie pattern
- Secure session cookie configuration
- Input validation via Pydantic models
- Redacted error messages
- No tokens in localStorage

### Infrastructure
- Non-root Docker users
- Healthchecks for all services
- .env.example with documented variables
- .gitignore excluding secrets, dependencies, build artifacts

## [1.1.0] - 2026-10-30

### Added
- GitHub skill discovery with sparse checkout (--filter=blob:none)
- SKILL.md parsing with frontmatter extraction (name, description, version, author, license, tags)
- Skill discovery endpoint: POST /api/skills/discover with GitHub repo URL
- Skill listing endpoint: GET /api/skills with pagination and filtering
- Skill detail endpoint: GET /api/skills/{id}
- Search endpoint: GET /api/skills/search?q=...
- Skills persisted to database with content hash for change detection
- Frontend: Discover page to enter GitHub repo URL and trigger discovery
- Frontend: Skills list page with search, filter, pagination
- Frontend: Skill detail page showing parsed metadata and README
- SkillSearch component with debounced input
- Pagination component for skills listing
- Navigation links for Skills and Discover pages

### Fixed
- TypeScript build errors in SkillSearch component
- Select onChange handlers in SkillsListPage
- UserInfo type missing subject field in SettingsPage

### Infrastructure
- Added Select, Pagination, Badge, Button, Card, Input components to ui.tsx

## [Unreleased]

### Planned
- Skill installation to agent directories
- skills-lock.json management with hash verification
- `npx prism install` / `ci` commands
- Skill update command with hash comparison
- AI/ML evaluation engine for skill quality scoring
- Security analysis (advisory, labeled)

### Known Issues
- Demo mode credentials are predictable (mitigated: disabled in production)
- SQLite not suitable for concurrent production (use PostgreSQL)
- No rate limiting (add via reverse proxy)
- Audit logging minimal
