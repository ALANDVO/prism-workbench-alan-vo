from datetime import datetime, timezone
from enum import Enum as PyEnum
from typing import Optional, List
from sqlalchemy import String, DateTime, Enum, Text, Boolean, Integer, ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class SkillSourceType(str, PyEnum):
    GITHUB = "github"
    GITLAB = "gitlab"
    LOCAL = "local"


class SkillStatus(str, PyEnum):
    DISCOVERED = "discovered"
    INDEXED = "indexed"
    INSTALLED = "installed"
    UPDATED = "updated"
    FAILED = "failed"
    REMOVED = "removed"


class SkillScope(str, PyEnum):
    PROJECT = "project"
    GLOBAL = "global"


class Skill(Base):
    __tablename__ = "skills"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    source_type: Mapped[SkillSourceType] = mapped_column(Enum(SkillSourceType), nullable=False)
    source_url: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    source_ref: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    owner: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    repo: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    skill_folder: Mapped[str] = mapped_column(String(500), nullable=False)
    skill_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    display_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    version: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    author: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    license: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    homepage: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    tags: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    readme_content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    skill_md_content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    skill_folder_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    status: Mapped[SkillStatus] = mapped_column(Enum(SkillStatus), default=SkillStatus.DISCOVERED, nullable=False)
    discovered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    indexed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_checked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    installations: Mapped[List["Installation"]] = relationship(back_populates="skill", lazy="selectin")

    __table_args__ = (
        UniqueConstraint("source_url", "skill_folder", name="uq_skill_source_folder"),
        Index("ix_skills_owner_repo_name", "owner", "repo", "skill_name"),
        Index("ix_skills_status_hash", "status", "skill_folder_hash"),
    )

    def __repr__(self) -> str:
        return f"<Skill(id={self.id}, name={self.skill_name}, owner={self.owner}, repo={self.repo})>"


class Installation(Base):
    __tablename__ = "installations"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    skill_id: Mapped[int] = mapped_column(ForeignKey("skills.id", ondelete="CASCADE"), nullable=False, index=True)
    scope: Mapped[SkillScope] = mapped_column(Enum(SkillScope), default=SkillScope.PROJECT, nullable=False)
    target_path: Mapped[str] = mapped_column(String(500), nullable=False)
    installed_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    installed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    install_metadata: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    user: Mapped["User"] = relationship(back_populates="installations", lazy="selectin")
    skill: Mapped["Skill"] = relationship(back_populates="installations", lazy="selectin")

    __table_args__ = (
        UniqueConstraint("user_id", "skill_id", "scope", "target_path", name="uq_installation_user_skill_scope"),
        Index("ix_installations_user_scope_active", "user_id", "scope", "is_active"),
    )

    def __repr__(self) -> str:
        return f"<Installation(id={self.id}, user_id={self.user_id}, skill_id={self.skill_id}, scope={self.scope})>"


class LockfileEntry(Base):
    __tablename__ = "lockfile_entries"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    skill_id: Mapped[int] = mapped_column(ForeignKey("skills.id", ondelete="CASCADE"), nullable=False, index=True)
    scope: Mapped[SkillScope] = mapped_column(Enum(SkillScope), default=SkillScope.PROJECT, nullable=False)
    source_url: Mapped[str] = mapped_column(String(500), nullable=False)
    skill_folder: Mapped[str] = mapped_column(String(500), nullable=False)
    skill_folder_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    target_path: Mapped[str] = mapped_column(String(500), nullable=False)
    installed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        UniqueConstraint("user_id", "skill_id", "scope", name="uq_lockfile_user_skill_scope"),
        Index("ix_lockfile_user_scope", "user_id", "scope"),
    )

    def __repr__(self) -> str:
        return f"<LockfileEntry(id={self.id}, user_id={self.user_id}, skill_id={self.skill_id})>"