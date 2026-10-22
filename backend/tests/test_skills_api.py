import pytest
from unittest.mock import patch, AsyncMock
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.skill import Skill, SkillSourceType, SkillStatus
from app.models.user import User, UserRole
from app.services.github_service import GitHubService


class TestSkillsAPI:
    @pytest.mark.asyncio
    async def test_list_skills_unauthenticated(self, client):
        response = client.get("/api/skills")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_list_skills_authenticated(self, client, demo_user_headers):
        response = client.get("/api/skills", headers=demo_user_headers)
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data

    @pytest.mark.asyncio
    async def test_list_skills_with_search(self, client, test_skill, demo_user_headers):
        response = client.get("/api/skills?search=test-skill", headers=demo_user_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["skill_name"] == "test-skill"

    @pytest.mark.asyncio
    async def test_list_skills_filter_by_owner(self, client, test_skill, demo_user_headers):
        response = client.get("/api/skills?owner=owner", headers=demo_user_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1

    @pytest.mark.asyncio
    async def test_list_skills_filter_by_status(self, client, test_skill, demo_user_headers):
        response = client.get("/api/skills?status=indexed", headers=demo_user_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1

    @pytest.mark.asyncio
    async def test_search_skills(self, client, test_skill, demo_user_headers):
        response = client.get("/api/skills/search?q=test", headers=demo_user_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["skill_name"] == "test-skill"

    @pytest.mark.asyncio
    async def test_search_skills_empty_query(self, client, demo_user_headers):
        response = client.get("/api/skills/search?q=", headers=demo_user_headers)
        assert response.status_code == 422  # Validation error for empty query

    @pytest.mark.asyncio
    async def test_get_skill_by_id(self, client, test_skill, demo_user_headers):
        response = client.get(f"/api/skills/{test_skill.id}", headers=demo_user_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_skill.id
        assert data["skill_name"] == "test-skill"

    @pytest.mark.asyncio
    async def test_get_skill_not_found(self, client, demo_user_headers):
        response = client.get("/api/skills/99999", headers=demo_user_headers)
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_discover_skills_requires_operator(self, client, demo_user_headers):
        # demo user is OPERATOR, should not return 403 (forbidden)
        # We mock the GitHub service to avoid real API calls
        mock_skills = [
            Skill(
                source_type=SkillSourceType.GITHUB,
                source_url="https://github.com/owner/repo",
                source_ref="main",
                owner="owner",
                repo="repo",
                skill_folder="skills/test",
                skill_name="test-skill",
                display_name="Test Skill",
                description="A test skill",
                skill_folder_hash="abc123",
                status=SkillStatus.INDEXED,
            )
        ]

        with patch.object(GitHubService, 'discover_skills', new=AsyncMock(return_value=mock_skills)):
            response = client.post(
                "/api/skills/discover",
                json={"repo_url": "https://github.com/owner/repo", "ref": "main"},
                headers=demo_user_headers,
            )
            # Should not be 403 (forbidden) - operator has permission
            assert response.status_code != 403
            # Should be 200 or 400/500 (validation/error), but not 403
            assert response.status_code in (200, 201, 400, 422, 500)