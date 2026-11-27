# skills-lock.json management
import json
import os
from pathlib import Path
from typing import Dict, Optional, List
from datetime import datetime, timezone

from app.core.config import settings


def get_lockfile_path(user_home: Optional[str] = None) -> str:
    """Get the path to the skills-lock.json file for a user."""
    if user_home:
        return os.path.join(user_home, ".agents", settings.LOCKFILE_NAME)
    return os.path.expanduser(os.path.join("~", settings.LOCKFILE_NAME))


def read_lockfile(user_home: Optional[str] = None) -> Dict:
    """Read the skills-lock.json file, return empty dict if not exists."""
    lockpath = get_lockfile_path(user_home)
    try:
        with open(lockpath, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def write_lockfile(data: Dict, user_home: Optional[str] = None) -> None:
    """Write the skills-lock.json file."""
    lockpath = get_lockfile_path(user_home)
    os.makedirs(os.path.dirname(lockpath), exist_ok=True)
    with open(lockpath, "w") as f:
        json.dump(data, f, indent=2)


def update_lockfile_for_installation(
    lock_data: Dict,
    installation: "Installation",
    skill: "Skill",
    user_home: Optional[str] = None,
) -> Dict:
    """Update lockfile data with a new installation entry."""
    # Key format: user_id:skill_id:scope
    lock_key = f"{installation.user_id}:{installation.skill_id}:{installation.scope.value}"
    
    entry = {
        "id": installation.id,
        "skill_id": installation.skill_id,
        "skill_name": skill.skill_name,
        "skill_owner": skill.owner,
        "skill_repo": skill.repo,
        "scope": installation.scope,
        "target_path": installation.target_path,
        "installed_hash": installation.installed_hash,
        "installed_at": installation.installed_at.isoformat() if installation.installed_at else None,
        "updated_at": str(installation.updated_at) if installation.updated_at else None,
    }
    
    lock_data[lock_key] = entry
    return lock_data
