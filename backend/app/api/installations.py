from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import List, Optional
from pydantic import BaseModel
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import require_user
from app.core.database import get_db_session
from app.models.user import User
from app.models.skill import Installation, Skill, SkillScope, SkillStatus
router = APIRouter(prefix="/installations", tags=["installations"])


class InstallationCreateRequest(BaseModel):
    skill_id: int
    scope: SkillScope = SkillScope.PROJECT
    target_path: Optional[str] = None


class InstallationResponse(BaseModel):
    id: int
    skill_id: int
    skill_name: str
    skill_owner: str
    skill_repo: str
    scope: SkillScope
    target_path: str
    installed_hash: str
    installed_at: datetime
    updated_at: Optional[datetime]
    is_active: bool

    @classmethod
    def from_model(cls, installation: Installation) -> "InstallationResponse":
        return cls(
            id=installation.id,
            skill_id=installation.skill_id,
            skill_name=installation.skill.skill_name,
            skill_owner=installation.skill.owner,
            skill_repo=installation.skill.repo,
            scope=installation.scope,
            target_path=installation.target_path,
            installed_hash=installation.installed_hash,
            installed_at=installation.installed_at,
            updated_at=installation.updated_at,
            is_active=installation.is_active,
        )


class PaginatedInstallationsResponse(BaseModel):
    items: List[InstallationResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


@router.post("", response_model=InstallationResponse, status_code=status.HTTP_201_CREATED)
async def create_installation(
    request: InstallationCreateRequest,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_user),
) -> InstallationResponse:
    """Install a skill for the current user."""
    # Check if skill exists
    skill_result = await session.execute(select(Skill).where(Skill.id == request.skill_id))
    skill = skill_result.scalar_one_or_none()
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")

    # Determine target path
    if request.target_path:
        target_path = request.target_path
    else:
        if request.scope == SkillScope.GLOBAL:
            target_path = f"~/.agents/skills/{skill.owner}/{skill.repo}/{skill.skill_folder}"
        else:
            target_path = f"./skills/{skill.owner}/{skill.repo}/{skill.skill_folder}"

    # Check if installation already exists
    existing_result = await session.execute(
        select(Installation).where(
            and_(
                Installation.user_id == current_user.id,
                Installation.skill_id == skill.id,
                Installation.scope == request.scope,
                Installation.target_path == target_path,
            )
        )
    )
    existing = existing_result.scalar_one_or_none()

    if existing:
        if existing.is_active:
            raise HTTPException(
                status_code=409,
                detail="Skill already installed at this location",
            )
        else:
            # Reactivate existing installation
            existing.is_active = True
            existing.installed_hash = skill.skill_folder_hash or ""
            existing.updated_at = datetime.now(timezone.utc)
            await session.commit()
            await session.refresh(existing)
            return InstallationResponse.from_model(existing)

    # Create new installation
    installation = Installation(
        user_id=current_user.id,
        skill_id=skill.id,
        scope=request.scope,
        target_path=target_path,
        installed_hash=skill.skill_folder_hash or "",
        install_metadata=None,
    )
    session.add(installation)

    # Update skill status to installed
    skill.status = SkillStatus.INSTALLED

    await session.commit()
    await session.refresh(installation)

    return InstallationResponse.from_model(installation)


@router.get("", response_model=PaginatedInstallationsResponse)
async def list_installations(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    scope: Optional[SkillScope] = None,
    is_active: Optional[bool] = None,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_user),
) -> PaginatedInstallationsResponse:
    """List installations for the current user."""
    query = select(Installation).where(Installation.user_id == current_user.id)

    if scope:
        query = query.where(Installation.scope == scope)
    if is_active is not None:
        query = query.where(Installation.is_active == is_active)

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await session.execute(count_query)
    total = total_result.scalar_one()

    # Apply pagination
    query = query.order_by(Installation.installed_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await session.execute(query)
    installations = result.scalars().all()

    return PaginatedInstallationsResponse(
        items=[InstallationResponse.from_model(i) for i in installations],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size,
    )


@router.delete("/{installation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def uninstall_skill(
    installation_id: int,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_user),
) -> None:
    """Uninstall a skill (deactivate installation)."""
    result = await session.execute(
        select(Installation).where(
            and_(
                Installation.id == installation_id,
                Installation.user_id == current_user.id,
            )
        )
    )
    installation = result.scalar_one_or_none()

    if not installation:
        raise HTTPException(status_code=404, detail="Installation not found")

    installation.is_active = False
    installation.updated_at = datetime.now(timezone.utc)

    # Check if skill has any other active installations
    other_installations_result = await session.execute(
        select(Installation).where(
            and_(
                Installation.skill_id == installation.skill_id,
                Installation.is_active == True,
            )
        )
    )
    other_installations = other_installations_result.scalars().all()
    if not other_installations:
        installation.skill.status = SkillStatus.INDEXED

    await session.commit()


