from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.api.auth import require_user, require_operator
from app.models.skill import Skill, SkillStatus, SkillSourceType
from app.models.user import User, UserRole
from app.services import github_service
from pydantic import BaseModel, HttpUrl


router = APIRouter(prefix="/skills", tags=["skills"])


class SkillDiscoverRequest(BaseModel):
    repo_url: HttpUrl
    ref: str = "main"


class SkillDiscoverResponse(BaseModel):
    discovered: int
    skills: List["SkillResponse"]


class SkillResponse(BaseModel):
    id: int
    source_type: SkillSourceType
    source_url: str
    source_ref: Optional[str]
    owner: str
    repo: str
    skill_folder: str
    skill_name: str
    display_name: Optional[str]
    description: Optional[str]
    version: Optional[str]
    author: Optional[str]
    license: Optional[str]
    homepage: Optional[str]
    tags: Optional[List[str]]
    readme_content: Optional[str]
    skill_md_content: Optional[str]
    skill_folder_hash: Optional[str]
    status: SkillStatus
    discovered_at: str
    indexed_at: Optional[str]

    @classmethod
    def from_model(cls, skill: Skill) -> "SkillResponse":
        tags = skill.tags.split(",") if skill.tags else None
        return cls(
            id=skill.id,
            source_type=skill.source_type,
            source_url=skill.source_url,
            source_ref=skill.source_ref,
            owner=skill.owner,
            repo=skill.repo,
            skill_folder=skill.skill_folder,
            skill_name=skill.skill_name,
            display_name=skill.display_name,
            description=skill.description,
            version=skill.version,
            author=skill.author,
            license=skill.license,
            homepage=skill.homepage,
            tags=tags,
            readme_content=skill.readme_content,
            skill_md_content=skill.skill_md_content,
            skill_folder_hash=skill.skill_folder_hash,
            status=skill.status,
            discovered_at=skill.discovered_at.isoformat() if skill.discovered_at else "",
            indexed_at=skill.indexed_at.isoformat() if skill.indexed_at else "",
        )


class PaginatedSkillsResponse(BaseModel):
    items: List[SkillResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


@router.post("/discover", response_model=SkillDiscoverResponse)
async def discover_skills(
    request: SkillDiscoverRequest,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_operator),
) -> SkillDiscoverResponse:
    """Discover skills from a GitHub repository."""
    repo_url = str(request.repo_url)

    # Discover skills using GitHub service
    skills = await github_service.discover_skills(repo_url, request.ref)

    saved_skills = []
    for skill in skills:
        # Check if skill already exists (by owner, repo, skill_folder)
        existing = await session.execute(
            select(Skill).where(
                Skill.owner == skill.owner,
                Skill.repo == skill.repo,
                Skill.skill_folder == skill.skill_folder,
            )
        )
        existing_skill = existing.scalar_one_or_none()

        if existing_skill:
            # Update if hash changed
            if existing_skill.skill_folder_hash != skill.skill_folder_hash:
                existing_skill.skill_md_content = skill.skill_md_content
                existing_skill.readme_content = skill.readme_content
                existing_skill.skill_folder_hash = skill.skill_folder_hash
                existing_skill.display_name = skill.display_name
                existing_skill.description = skill.description
                existing_skill.version = skill.version
                existing_skill.author = skill.author
                existing_skill.license = skill.license
                existing_skill.homepage = skill.homepage
                existing_skill.tags = skill.tags
                existing_skill.status = SkillStatus.UPDATED
            skill = existing_skill
        else:
            session.add(skill)

        saved_skills.append(skill)

    await session.commit()

    for skill in saved_skills:
        await session.refresh(skill)

    return SkillDiscoverResponse(
        discovered=len(saved_skills),
        skills=[SkillResponse.from_model(s) for s in saved_skills],
    )


@router.get("", response_model=PaginatedSkillsResponse)
async def list_skills(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    owner: Optional[str] = Query(None),
    repo: Optional[str] = Query(None),
    status: Optional[SkillStatus] = Query(None),
    source_type: Optional[SkillSourceType] = Query(None),
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_user),
) -> PaginatedSkillsResponse:
    """List skills with pagination and filtering."""
    query = select(Skill)

    if search:
        search_term = f"%{search.lower()}%"
        query = query.where(
            or_(
                Skill.skill_name.ilike(search_term),
                Skill.description.ilike(search_term),
                Skill.owner.ilike(search_term),
                Skill.repo.ilike(search_term),
                Skill.tags.ilike(search_term),
            )
        )

    if owner:
        query = query.where(Skill.owner.ilike(f"%{owner}%"))

    if repo:
        query = query.where(Skill.repo.ilike(f"%{repo}%"))

    if status:
        query = query.where(Skill.status == status)

    if source_type:
        query = query.where(Skill.source_type == source_type)

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await session.execute(count_query)
    total = total_result.scalar() or 0

    # Apply pagination
    query = query.order_by(Skill.discovered_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await session.execute(query)
    skills = result.scalars().all()

    return PaginatedSkillsResponse(
        items=[SkillResponse.from_model(s) for s in skills],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size,
    )


@router.get("/search", response_model=List[SkillResponse])
async def search_skills(
    q: str = Query(..., min_length=1),
    limit: int = Query(10, ge=1, le=50),
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_user),
) -> List[SkillResponse]:
    """Search skills by query string."""
    search_term = f"%{q.lower()}%"
    query = (
        select(Skill)
        .where(
            or_(
                Skill.skill_name.ilike(search_term),
                Skill.description.ilike(search_term),
                Skill.owner.ilike(search_term),
                Skill.repo.ilike(search_term),
                Skill.tags.ilike(search_term),
            )
        )
        .order_by(Skill.discovered_at.desc())
        .limit(limit)
    )

    result = await session.execute(query)
    skills = result.scalars().all()

    return [SkillResponse.from_model(s) for s in skills]


@router.get("/{skill_id}", response_model=SkillResponse)
async def get_skill(
    skill_id: int,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_user),
) -> SkillResponse:
    """Get skill details by ID."""
    skill = await session.get(Skill, skill_id)
    if not skill:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Skill not found")
    return SkillResponse.from_model(skill)