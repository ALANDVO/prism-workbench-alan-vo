import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from pathlib import Path
import tempfile

from app.services.github_service import GitHubService
from app.services.skill_parser import parse_skill_md, extract_sections, validate_skill_metadata


class TestSkillParser:
    def test_parse_skill_md_basic(self):
        content = """---
name: test-skill
display_name: "Test Skill"
description: "A test skill"
version: "1.0.0"
author: "Test Author"
license: "MIT"
homepage: "https://example.com"
tags: [tag1, tag2, tag3]
---
# Test Skill

This is a test skill.
"""
        result = parse_skill_md(content)
        assert result["name"] == "test-skill"
        assert result["display_name"] == "Test Skill"
        assert result["description"] == "A test skill"
        assert result["version"] == "1.0.0"
        assert result["author"] == "Test Author"
        assert result["license"] == "MIT"
        assert result["homepage"] == "https://example.com"
        assert result["tags"] == ["tag1", "tag2", "tag3"]

    def test_parse_skill_md_minimal(self):
        content = """---
name: minimal-skill
description: "Minimal skill"
---
"""
        result = parse_skill_md(content)
        assert result["name"] == "minimal-skill"
        assert result["description"] == "Minimal skill"
        assert "version" not in result

    def test_parse_skill_md_no_frontmatter(self):
        content = """# Test Skill

No frontmatter here.
"""
        result = parse_skill_md(content)
        # Without frontmatter, name is extracted from first heading
        assert result.get("name") == "Test Skill"

    def test_parse_skill_md_fallback_to_heading(self):
        content = """---
description: "Skill without name in frontmatter"
---
# Fallback Name

Content here.
"""
        result = parse_skill_md(content)
        assert result["name"] == "Fallback Name"

    def test_extract_sections(self):
        content = """---
name: test
---
# Introduction

Intro content.

## Details

Detail content.

### More

More content.
"""
        sections = extract_sections(content)
        assert "introduction" in sections
        assert sections["introduction"] == "Intro content."
        assert "details" in sections
        assert sections["details"] == "Detail content."

    def test_validate_skill_metadata_valid(self):
        metadata = {"name": "valid-skill", "description": "Valid skill"}
        errors = validate_skill_metadata(metadata)
        assert len(errors) == 0

    def test_validate_skill_metadata_missing_name(self):
        metadata = {"description": "No name"}
        errors = validate_skill_metadata(metadata)
        assert "Missing required field: name" in errors

    def test_validate_skill_metadata_missing_description(self):
        metadata = {"name": "no-desc"}
        errors = validate_skill_metadata(metadata)
        assert "Missing required field: description" in errors

    def test_validate_skill_metadata_invalid_name_format(self):
        metadata = {"name": "Invalid_Name", "description": "Test"}
        errors = validate_skill_metadata(metadata)
        assert any("kebab-case" in e for e in errors)


class TestGitHubService:
    @pytest.fixture
    def github_service(self):
        return GitHubService()

    def test_parse_repo_url_https(self):
        service = GitHubService()
        owner, repo = service._parse_repo_url("https://github.com/owner/repo")
        assert owner == "owner"
        assert repo == "repo"

    def test_parse_repo_url_with_git_suffix(self):
        service = GitHubService()
        owner, repo = service._parse_repo_url("https://github.com/owner/repo.git")
        assert owner == "owner"
        assert repo == "repo"

    def test_parse_repo_url_invalid(self):
        service = GitHubService()
        with pytest.raises(ValueError):
            service._parse_repo_url("https://example.com/not-github")

    def test_find_skill_directories(self):
        service = GitHubService()
        tree = [
            {"type": "blob", "path": "skills/skill1/SKILL.md"},
            {"type": "blob", "path": "skills/skill2/SKILL.md"},
            {"type": "blob", "path": "README.md"},
            {"type": "tree", "path": "skills/skill1"},
        ]
        dirs = service.find_skill_directories(tree)
        assert "skills/skill1" in dirs
        assert "skills/skill2" in dirs
        assert len(dirs) == 2

    def test_compute_folder_hash(self):
        service = GitHubService()
        with tempfile.TemporaryDirectory() as tmpdir:
            folder = Path(tmpdir) / "test"
            folder.mkdir()
            (folder / "file1.txt").write_text("content1")
            (folder / "file2.txt").write_text("content2")

            hash1 = service.compute_folder_hash(folder)
            hash2 = service.compute_folder_hash(folder)
            assert hash1 == hash2
            assert len(hash1) == 64  # SHA-256

            # Different content -> different hash
            (folder / "file1.txt").write_text("different")
            hash3 = service.compute_folder_hash(folder)
            assert hash3 != hash1

    @pytest.mark.asyncio
    async def test_get_repo_tree(self, github_service):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "tree": [
                {"type": "blob", "path": "skills/test/SKILL.md"},
                {"type": "blob", "path": "README.md"},
            ]
        }
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )
            tree = await github_service.get_repo_tree("owner", "repo", "main")
            assert len(tree) == 2
            assert tree[0]["path"] == "skills/test/SKILL.md"