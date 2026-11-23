import json
from pathlib import Path
import os

lockfile_path = Path("skills-lock.json")


async def sync_lockfile_for_installation(user_id, installation, skill):
    """Add or update a lockfile entry for an installation."""
    entry = {
        "user_id": user_id,
        "skill_id": installation.skill_id,
        "skill_folder": skill.skill_folder or "",
        "skill_folder_hash": skill.skill_folder_hash or "",
        "target_path": installation.target_path,
        "scope": installation.scope,
        "installed_at": installation.installed_at.isoformat() if installation.installed_at else None,
        "updated_at": installation.updated_at.isoformat() if installation.updated_at else None,
        "source_url": skill.source_url or "",
    }

    if lockfile_path.exists():
        try:
            with open(lockfile_path, "r") as f:
                data = json.load(f)
        except Exception:
            data = []
    else:
        data = []

    # Check if entry already exists for this user/skill/scope combination
    existing_index = None
    for i, d in enumerate(data):
        if (d.get("user_id") == user_id and
                d.get("skill_id") == installation.skill_id and
                d.get("scope") == installation.scope):
            existing_index = i
            break

    if existing_index is not None:
        data[existing_index] = entry
    else:
        data.append(entry)

    with open(lockfile_path, "w") as f:
        json.dump(data, f, indent=2)


async def remove_lockfile_entry(user_id, skill_id, scope):
    """Remove a lockfile entry for an installation."""
    if not lockfile_path.exists():
        return

    try:
        with open(lockfile_path, "r") as f:
            data = json.load(f)
    except Exception:
        return

    new_data = [e for e in data if not (
        e.get("user_id") == user_id and
        e.get("skill_id") == skill_id and
        e.get("scope") == scope
    )]

    if len(new_data) != len(data):
        with open(lockfile_path, "w") as f:
            json.dump(new_data, f, indent=2)
