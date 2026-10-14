import { useState } from 'react'
import { Link } from 'react-router-dom'
import { Skill } from '../api/client'
import { api } from '../api/client'
import { useToast } from '../components/Toast'

interface SkillCardProps {
  skill: Skill
  installed: boolean
}

export function SkillCard({ skill, installed }: SkillCardProps) {
  const [installing, setInstalling] = useState(false)
  const toast = useToast()

  const handleInstall = async () => {
    setInstalling(true)
    try {
      await api.post('/installations', {
        skill_id: skill.id,
        scope: 'project',
      })
      toast.success(`Installed ${skill.skill_name}`)
    } catch {
      toast.error('Installation failed')
    } finally {
      setInstalling(false)
    }
  }

  const handleUninstall = async () => {
    if (!confirm(`Uninstall "${skill.skill_name}"?`)) return
    try {
      await api.delete(`/installations/${skill.id}`)
      toast.success(`Uninstalled ${skill.skill_name}`)
    } catch {
      toast.error('Uninstallation failed')
    }
  }

  return (
    <article className="card overflow-hidden transition-shadow hover:shadow-md">
      <div className="card-header flex items-start justify-between gap-2">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-1">
            <h3 className="font-semibold text-[var(--color-text)]">{skill.display_name || skill.skill_name}</h3>
            <span className={`badge ${getStatusBadgeClass(skill.status)}`}>{skill.status}</span>
          </div>
          <p className="text-sm text-[var(--color-text-secondary)] line-clamp-2">{skill.description || 'No description'}</p>
        </div>
        {installed ? (
          <button onClick={handleUninstall} className="btn btn-ghost btn-sm" title="Uninstall">
            Uninstall
          </button>
        ) : (
          <button onClick={handleInstall} disabled={installing} className="btn btn-primary btn-sm">
            {installing ? 'Installing...' : 'Install'}
          </button>
        )}
      </div>
      <div className="card-body">
        <div className="flex items-center gap-2 text-xs text-[var(--color-text-muted)] mb-2">
          <span className="font-mono">{skill.owner}/{skill.repo}</span>
          <span>•</span>
          <span className="font-mono">{skill.skill_folder}</span>
        </div>
        {skill.skill_folder_hash && (
          <div className="text-xs text-[var(--color-text-muted)] font-mono">
            Hash: {skill.skill_folder_hash.substring(0, 12)}...
          </div>
        )}
      </div>
      <div className="card-footer flex items-center justify-end gap-2">
        <Link to={`/skills/${skill.id}`} className="btn btn-ghost btn-sm">
          Details
        </Link>
        {skill.source_url && (
          <a href={skill.source_url} target="_blank" rel="noopener noreferrer" className="btn btn-ghost btn-sm">
            GitHub
          </a>
        )}
      </div>
    </article>
  )
}

function getStatusBadgeClass(status: string): string {
  switch (status) {
    case 'discovered':
      return 'badge-secondary'
    case 'indexed':
      return 'badge-primary'
    case 'installed':
      return 'badge-success'
    case 'updated':
      return 'badge-primary'
    case 'failed':
      return 'badge-error'
    case 'removed':
      return 'badge-secondary'
    default:
      return 'badge-secondary'
  }
}