import pytest
from datetime import datetime, timezone
from sqlalchemy import select
from app.models.user import User, UserRole, Session
from app.models.skill import Skill, SkillSourceType, SkillStatus, SkillScope, Installation, LockfileEntry
from app.core.security import get_password_hash, verify_password


class TestUserModel:
    @pytest.mark.asyncio
    async def test_create_user(self, async_session):
        user = User(
            subject="test-subject-123",
            email="test@example.com",
            username="testuser",
            full_name="Test User",
            role=UserRole.OPERATOR,
        )
        async_session.add(user)
        await async_session.commit()
        await async_session.refresh(user)

        assert user.id is not None
        assert user.subject == "test-subject-123"
        assert user.email == "test@example.com"
        assert user.role == UserRole.OPERATOR
        assert user.is_active is True
        assert user.created_at is not None

    @pytest.mark.asyncio
    async def test_user_unique_subject(self, async_session):
        user1 = User(subject="unique-subject", email="a@example.com")
        user2 = User(subject="unique-subject", email="b@example.com")
        async_session.add_all([user1, user2])
        with pytest.raises(Exception):
            await async_session.commit()

    @pytest.mark.asyncio
    async def test_user_unique_email(self, async_session):
        user1 = User(subject="sub1", email="same@example.com")
        user2 = User(subject="sub2", email="same@example.com")
        async_session.add_all([user1, user2])
        with pytest.raises(Exception):
            await async_session.commit()


class TestSkillModel:
    @pytest.mark.asyncio
    async def test_create_skill(self, async_session):
        skill = Skill(
            source_type=SkillSourceType.GITHUB,
            source_url="https://github.com/owner/repo",
            owner="owner",
            repo="repo",
            skill_folder="skills/my-skill",
            skill_name="my-skill",
            display_name="My Skill",
            description="A test skill",
            status=SkillStatus.DISCOVERED,
        )
        async_session.add(skill)
        await async_session.commit()
        await async_session.refresh(skill)

        assert skill.id is not None
        assert skill.skill_name == "my-skill"
        assert skill.status == SkillStatus.DISCOVERED

    @pytest.mark.asyncio
    async def test_skill_unique_source_folder(self, async_session):
        skill1 = Skill(
            source_type=SkillSourceType.GITHUB,
            source_url="https://github.com/owner/repo",
            owner="owner",
            repo="repo",
            skill_folder="skills/test",
            skill_name="test",
        )
        skill2 = Skill(
            source_type=SkillSourceType.GITHUB,
            source_url="https://github.com/owner/repo",
            owner="owner",
            repo="repo",
            skill_folder="skills/test",
            skill_name="test2",
        )
        async_session.add_all([skill1, skill2])
        with pytest.raises(Exception):
            await async_session.commit()


class TestInstallationModel:
    @pytest.mark.asyncio
    async def test_create_installation(self, async_session):
        user = User(subject="inst-user", email="inst@example.com", username="instuser")
        skill = Skill(
            source_type=SkillSourceType.GITHUB,
            source_url="https://github.com/owner/repo",
            owner="owner",
            repo="repo",
            skill_folder="skills/test",
            skill_name="test-skill",
        )
        async_session.add_all([user, skill])
        await async_session.flush()

        installation = Installation(
            user_id=user.id,
            skill_id=skill.id,
            scope=SkillScope.PROJECT,
            target_path=".claude/skills/test-skill",
            installed_hash="abc123def456",
        )
        async_session.add(installation)
        await async_session.commit()
        await async_session.refresh(installation)

        assert installation.id is not None
        assert installation.scope == SkillScope.PROJECT
        assert installation.is_active is True


class TestLockfileEntryModel:
    @pytest.mark.asyncio
    async def test_create_lockfile_entry(self, async_session):
        user = User(subject="lock-user", email="lock@example.com")
        skill = Skill(
            source_type=SkillSourceType.GITHUB,
            source_url="https://github.com/owner/repo",
            owner="owner",
            repo="repo",
            skill_folder="skills/test",
            skill_name="test-skill",
        )
        async_session.add_all([user, skill])
        await async_session.flush()

        entry = LockfileEntry(
            user_id=user.id,
            skill_id=skill.id,
            scope=SkillScope.PROJECT,
            source_url="https://github.com/owner/repo",
            skill_folder="skills/test",
            skill_folder_hash="abc123def456",
            target_path=".claude/skills/test-skill",
        )
        async_session.add(entry)
        await async_session.commit()
        await async_session.refresh(entry)

        assert entry.id is not None
        assert entry.skill_folder_hash == "abc123def456"


class TestSecurity:
    def test_password_hash_verify(self):
        password = "test-password-123"
        hashed = get_password_hash(password)
        assert verify_password(password, hashed)
        assert not verify_password("wrong-password", hashed)

    def test_password_hash_different_each_time(self):
        password = "same-password"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)
        assert hash1 != hash2
        assert verify_password(password, hash1)
        assert verify_password(password, hash2)