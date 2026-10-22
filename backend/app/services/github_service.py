import asyncio
import hashlib
import os
import shutil
import tempfile
from pathlib import Path
from typing import List, Optional, Tuple
from urllib.parse import urlparse

import httpx
from git import Repo, GitCommandError

from app.core.config import settings
from app.models.skill import Skill, SkillSourceType, SkillStatus


class GitHubService:
    """GitHub API client with sparse checkout support for skill discovery."""

    def __init__(self):
        self.token = settings.GITHUB_TOKEN
        self.api_url = settings.GITHUB_API_URL
        self.timeout = settings.GITHUB_CLONE_TIMEOUT
        self.sparse_checkout = settings.GITHUB_SPARSE_CHECKOUT

    def _parse_repo_url(self, url: str) -> Tuple[str, str]:
        """Extract owner and repo from GitHub URL."""
        parsed = urlparse(url)
        path = parsed.path.strip("/")
        parts = path.split("/")
        if len(parts) >= 2:
            return parts[0], parts[1].removesuffix(".git")
        raise ValueError(f"Invalid GitHub repository URL: {url}")

    async def _get_headers(self) -> dict:
        headers = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    async def get_repo_tree(self, owner: str, repo: str, ref: str = "main") -> List[dict]:
        """Get repository tree to find skill directories."""
        url = f"{self.api_url}/repos/{owner}/{repo}/git/trees/{ref}?recursive=1"
        async with httpx.AsyncClient(timeout=30.0) as client:
            headers = await self._get_headers()
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            return data.get("tree", [])

    def find_skill_directories(self, tree: List[dict]) -> List[str]:
        """Find directories containing SKILL.md files."""
        skill_dirs = []
        for item in tree:
            if item["type"] == "blob" and item["path"].endswith("/SKILL.md"):
                skill_dir = str(Path(item["path"]).parent)
                if skill_dir not in skill_dirs:
                    skill_dirs.append(skill_dir)
        return skill_dirs

    async def clone_sparse(
        self, repo_url: str, skill_dirs: List[str], target_dir: Path
    ) -> List[Path]:
        """Clone repository with sparse checkout to get only skill directories."""
        target_dir.mkdir(parents=True, exist_ok=True)

        repo = Repo.init(target_dir, bare=False)
        origin = repo.create_remote("origin", repo_url)

        # Configure sparse checkout
        if self.sparse_checkout and skill_dirs:
            repo.git.config("core.sparseCheckout", "true")
            sparse_checkout_file = target_dir / ".git" / "info" / "sparse-checkout"
            sparse_checkout_file.parent.mkdir(parents=True, exist_ok=True)
            with open(sparse_checkout_file, "w") as f:
                for skill_dir in skill_dirs:
                    f.write(f"{skill_dir}/*\n")
                f.write("*.md\n")  # Include root markdown files

        # Fetch with depth=1 and filter=blob:none for partial clone
        fetch_args = ["--depth", "1"]
        if self.sparse_checkout:
            fetch_args.extend(["--filter=blob:none"])

        try:
            origin.fetch(*fetch_args, refspec="HEAD")
        except GitCommandError as e:
            # Fallback without partial clone if not supported
            if "--filter=blob:none" in fetch_args:
                fetch_args.remove("--filter=blob:none")
                origin.fetch(*fetch_args, refspec="HEAD")
            else:
                raise

        # Checkout the fetched HEAD
        repo.git.checkout("FETCH_HEAD")

        # Return paths to skill directories that were cloned
        result = []
        for skill_dir in skill_dirs:
            skill_path = target_dir / skill_dir
            if skill_path.exists():
                result.append(skill_path)
        return result

    def compute_folder_hash(self, folder: Path) -> str:
        """Compute SHA-256 hash of folder contents (for change detection)."""
        hashes = []
        for file_path in sorted(folder.rglob("*")):
            if file_path.is_file():
                rel_path = file_path.relative_to(folder)
                with open(file_path, "rb") as f:
                    content = f.read()
                file_hash = hashlib.sha256(content).hexdigest()
                hashes.append(f"{rel_path}:{file_hash}")
        combined = "\n".join(hashes)
        return hashlib.sha256(combined.encode()).hexdigest()

    async def discover_skills(self, repo_url: str, ref: str = "main") -> List[Skill]:
        """Discover skills from a GitHub repository."""
        owner, repo = self._parse_repo_url(repo_url)

        # Get repository tree to find skill directories
        tree = await self.get_repo_tree(owner, repo, ref)
        skill_dirs = self.find_skill_directories(tree)

        if not skill_dirs:
            return []

        # Clone with sparse checkout
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            cloned_dirs = await self.clone_sparse(repo_url, skill_dirs, tmp_path)

            skills = []
            for skill_path in cloned_dirs:
                skill = await self._parse_skill_directory(
                    skill_path, repo_url, owner, repo, ref
                )
                if skill:
                    skills.append(skill)

            return skills

    async def _parse_skill_directory(
        self, skill_path: Path, repo_url: str, owner: str, repo: str, ref: str
    ) -> Optional[Skill]:
        """Parse SKILL.md and create Skill object."""
        skill_md_path = skill_path / "SKILL.md"
        if not skill_md_path.exists():
            return None

        try:
            from app.services.skill_parser import parse_skill_md

            with open(skill_md_path, "r", encoding="utf-8") as f:
                skill_md_content = f.read()

            parsed = parse_skill_md(skill_md_content)
            folder_hash = self.compute_folder_hash(skill_path)

            # Read README if present
            readme_content = None
            for readme_name in ["README.md", "readme.md", "README.txt"]:
                readme_path = skill_path / readme_name
                if readme_path.exists():
                    with open(readme_path, "r", encoding="utf-8") as f:
                        readme_content = f.read()
                    break

            skill = Skill(
                source_type=SkillSourceType.GITHUB,
                source_url=repo_url,
                source_ref=ref,
                owner=owner,
                repo=repo,
                skill_folder=str(skill_path.relative_to(skill_path.parent.parent))
                if skill_path.parent.parent.exists()
                else str(skill_path.name),
                skill_name=parsed.get("name", skill_path.name),
                display_name=parsed.get("display_name"),
                description=parsed.get("description"),
                version=parsed.get("version"),
                author=parsed.get("author"),
                license=parsed.get("license"),
                homepage=parsed.get("homepage"),
                tags=",".join(parsed.get("tags", [])) if parsed.get("tags") else None,
                readme_content=readme_content,
                skill_md_content=skill_md_content,
                skill_folder_hash=folder_hash,
                status=SkillStatus.INDEXED,
            )
            return skill
        except Exception as e:
            # Log error but continue with other skills
            print(f"Error parsing skill at {skill_path}: {e}")
            return None


github_service = GitHubService()