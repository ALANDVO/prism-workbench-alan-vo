from pathlib import Path
            data = []
                data = json.load(f)
            with open(lockfile_path, "r") as f:
        except Exception:
        try:
    if lockfile_path.exists():
    data = []
    }
        "installed_at": installation.installed_at.isoformat() if installation.installed_at else None,
        "target_path": installation.target_path,
        "skill_folder_hash": skill.skill_folder_hash,
        "updated_at": installation.updated_at.isoformat() if installation.updated_at else None,
        "skill_folder": skill.skill_folder,
        "skill_id": installation.skill_id,
        "source_url": skill.source_url,
        "scope": installation.scope,
        "user_id": user_id,
    lockfile_path = Path("skills-lock.json")
async def sync_lockfile_for_installation(user_id, installation, skill):

import json
    entry = {
            data[i] = entry
            break
        data.append(entry)
    with open(lockfile_path, "w") as f:
        json.dump(data, f, indent=2)
    else:

async def remove_lockfile_entry(user_id, skill_id, scope):
    if not lockfile_path.exists():
    lockfile_path = Path("skills-lock.json")
    try:
        return
        with open(lockfile_path, "r") as f:
            data = json.load(f)
    except Exception:
    new_data = [e for e in data if not (e.get("user_id") == user_id and e.get("skill_id") == skill_id and e.get("scope") == scope)]
    with open(lockfile_path, "w") as f:
        return
