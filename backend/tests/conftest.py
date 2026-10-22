import pytest
import pytest_asyncio
from unittest.mock import patch
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.core.database import Base, get_db_session
from app.main import create_app


@pytest.fixture(scope="session")
def test_settings() -> Settings:
    return Settings(
        DATABASE_URL="sqlite+aiosqlite:///:memory:",
        DEBUG=True,
        DEMO_MODE=True,
        SECRET_KEY="test-secret-key-for-testing-only-32-chars-minimum",
        OIDC_ENABLED=False,
    )


@pytest_asyncio.fixture(scope="function")
async def async_engine(test_settings: Settings):
    engine = create_async_engine(
        test_settings.DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def async_session(async_engine) -> AsyncSession:
    async_session_maker = sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session_maker() as session:
        yield session


@pytest.fixture(scope="function")
def client(async_session, test_settings):
    app = create_app()
    app.dependency_overrides[get_db_session] = lambda: async_session

    # Patch global settings in modules that import it at module level
    with patch('app.core.config.settings', test_settings), \
         patch('app.main.settings', test_settings), \
         patch('app.api.auth.settings', test_settings), \
         patch('app.api.health.settings', test_settings), \
         patch('app.core.security.settings', test_settings), \
         patch('app.core.database.settings', test_settings):
        with TestClient(app) as test_client:
            yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def demo_user_headers(client):
    """Get auth headers for demo user via demo login."""
    # Login via demo mode to get session cookie
    response = client.get("/api/auth/demo-login", follow_redirects=False)
    # Extract session cookie
    session_cookie = response.cookies.get("prism_session")
    if session_cookie:
        return {"Cookie": f"prism_session={session_cookie}"}
    return {}


@pytest_asyncio.fixture
async def test_skill(async_session: AsyncSession):
    from app.models.skill import Skill, SkillSourceType, SkillStatus

    skill = Skill(
        source_type=SkillSourceType.GITHUB,
        source_url="https://github.com/owner/repo",
        source_ref="main",
        owner="owner",
        repo="repo",
        skill_folder="skills/test-skill",
        skill_name="test-skill",
        display_name="Test Skill",
        description="A test skill",
        version="1.0.0",
        author="Test Author",
        license="MIT",
        tags="tag1,tag2",
        skill_folder_hash="abc123",
        status=SkillStatus.INDEXED,
    )
    async_session.add(skill)
    await async_session.commit()
    await async_session.refresh(skill)
    return skill