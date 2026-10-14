from functools import lru_cache
from typing import Optional, List
from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    APP_NAME: str = "Prism Workbench"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    DEMO_MODE: bool = False

    # Server
    HOST: str = "127.0.0.1"
    PORT: int = 8000

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./prism.db"
    DATABASE_ECHO: bool = False

    # Security
    SECRET_KEY: str = Field(default="dev-secret-key-change-in-production-minimum-32-chars", min_length=32)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # OIDC / Keycloak
    OIDC_ENABLED: bool = True
    OIDC_ISSUER_URL: str = "http://localhost:8080/realms/prism"
    OIDC_CLIENT_ID: str = "prism-workbench"
    OIDC_CLIENT_SECRET: str = ""
    OIDC_REDIRECT_URI: str = "http://localhost:3000/auth/callback"
    OIDC_SCOPES: List[str] = ["openid", "profile", "email", "roles"]
    OIDC_JWKS_URI: Optional[str] = None
    OIDC_AUTHORIZATION_ENDPOINT: Optional[str] = None
    OIDC_TOKEN_ENDPOINT: Optional[str] = None
    OIDC_USERINFO_ENDPOINT: Optional[str] = None
    OIDC_LOGOUT_ENDPOINT: Optional[str] = None

    # Session
    SESSION_COOKIE_NAME: str = "prism_session"
    SESSION_COOKIE_SECURE: bool = False
    SESSION_COOKIE_SAMESITE: str = "lax"
    SESSION_COOKIE_HTTPONLY: bool = True
    SESSION_COOKIE_DOMAIN: Optional[str] = None
    SESSION_COOKIE_PATH: str = "/"

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    CORS_ALLOW_CREDENTIALS: bool = True

    # GitHub
    GITHUB_TOKEN: Optional[str] = None
    GITHUB_API_URL: str = "https://api.github.com"
    GITHUB_CLONE_TIMEOUT: int = 120
    GITHUB_SPARSE_CHECKOUT: bool = True

    # Skill Installation
    SKILL_INSTALL_DIRS: List[str] = [
        ".claude/skills",
        ".cursor/skills",
        ".agents/skills",
        ".codex/skills",
    ]
    GLOBAL_SKILL_DIR: str = "~/.agents/skills"
    LOCKFILE_NAME: str = "skills-lock.json"
    GLOBAL_LOCKFILE_PATH: str = "~/.agents/.skill-lock.json"

    # LLM (Optional, for AI/ML evaluation)
    LLM_API_KEY: Optional[str] = None
    LLM_PROVIDER: str = "openai-compatible"
    LLM_MODEL: str = "gpt-4o-mini"
    LLM_BASE_URL: Optional[str] = None
    LLM_TIMEOUT: float = 30.0
    LLM_MAX_RETRIES: int = 2

    # Redis (for session storage in production)
    REDIS_URL: Optional[str] = None
    REDIS_ENABLED: bool = False

    @computed_field
    @property
    def is_production(self) -> bool:
        return not self.DEBUG and not self.DEMO_MODE

    @computed_field
    @property
    def oidc_discovery_url(self) -> str:
        return f"{self.OIDC_ISSUER_URL.rstrip('/')}/.well-known/openid-configuration"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()