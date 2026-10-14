import pytest
from fastapi.testclient import TestClient
from app.models.user import User, UserRole


class TestAuthEndpoints:
    def test_me_unauthenticated(self, client: TestClient):
        response = client.get("/api/auth/me")
        assert response.status_code == 401

    def test_logout_unauthenticated(self, client: TestClient):
        response = client.post("/api/auth/logout")
        # Logout succeeds even without session (clears cookie)
        assert response.status_code == 200
        assert response.json()["detail"] == "Logged out"

    def test_refresh_unauthenticated(self, client: TestClient):
        response = client.post("/api/auth/refresh")
        assert response.status_code == 401

    def test_demo_login_enabled(self, client: TestClient):
        response = client.get("/api/auth/demo-login", follow_redirects=False)
        # FastAPI returns 307 for redirects
        assert response.status_code in (302, 307)
        assert "/dashboard" in response.headers.get("location", "")
        assert "prism_session" in response.cookies

    @pytest.mark.asyncio
    async def test_demo_login_creates_user(self, client: TestClient, async_session):
        from sqlalchemy import select

        response = client.get("/api/auth/demo-login", follow_redirects=False)
        assert response.status_code in (302, 307)

        session_id = response.cookies.get("prism_session")
        assert session_id is not None

        result = await async_session.execute(select(User).where(User.subject == "demo-user"))
        user = result.scalar_one_or_none()
        assert user is not None
        assert user.username == "demo"
        assert user.role == UserRole.OPERATOR

    @pytest.mark.asyncio
    async def test_demo_login_idempotent(self, client: TestClient, async_session):
        from sqlalchemy import select

        client.get("/api/auth/demo-login", follow_redirects=False)
        client.get("/api/auth/demo-login", follow_redirects=False)

        result = await async_session.execute(select(User).where(User.subject == "demo-user"))
        users = result.scalars().all()
        assert len(users) == 1


class TestProtectedRoutes:
    def test_protected_route_requires_auth(self, client: TestClient):
        # Test a backend protected route
        response = client.get("/api/auth/me", follow_redirects=False)
        assert response.status_code == 401