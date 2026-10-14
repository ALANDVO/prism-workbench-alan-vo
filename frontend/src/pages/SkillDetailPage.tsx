import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { api, Skill } from '../api/client'
import { useToast } from '../components/Toast'
import { Spinner } from '../components/ui'
import { formatDateTime, formatRelativeTime } from '../utils/date'
import { marked } from 'marked'

export function SkillDetailPage() {
  const { skillId } = useParams<{ skillId: string }>()
  const [skill, setSkill] = useState<Skill | null>(null)
  const [loading, setLoading] = useState(true)
  const [installing, setInstalling] = useState(false)
  const [readmeHtml, setReadmeHtml] = useState<string>('')
  const [skillMdHtml, setSkillMdHtml] = useState<string>('')
  const toast = useToast()

  useEffect(() => {
    if (skillId) {
      loadSkill()
    }
  }, [skillId])

  const loadSkill = async () => {
    setLoading(true)
    try {
      const data = await api.get<Skill>(`/skills/${skillId}`)
      setSkill(data)
      // Render markdown content
      if (data.readme_content) {
        const html = await marked.parse(data.readme_content)
        setReadmeHtml(html)
      }
      if (data.skill_md_content) {
        const html = await marked.parse(data.skill_md_content)
        setSkillMdHtml(html)
      }
    } catch {
      toast.error('Failed to load skill details')
    } finally {
      setLoading(false)
    }
  }

  const handleInstall = async () => {
    if (!skill) return
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

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Spinner size="lg" />
      </div>
    )
  }

  if (!skill) {
    return (
      <div className="text-center py-12">
        <h2 className="text-xl font-semibold text-[var(--color-text)]">Skill not found</h2>
        <p className="text-[var(--color-text-secondary)] mt-2">The requested skill does not exist.</p>
        <Link to="/dashboard" className="btn btn-primary mt-4 inline-block">
          Back to Dashboard
        </Link>
      </div>
    )
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-2">
            <h1 className="text-2xl font-bold text-[var(--color-text)]">{skill.display_name || skill.skill_name}</h1>
            <span className={`badge ${getStatusBadgeClass(skill.status)}`}>{skill.status}</span>
          </div>
          <p className="text-[var(--color-text-secondary)]">{skill.description || 'No description available'}</p>
        </div>
        <button
          onClick={handleInstall}
          disabled={installing}
          className="btn btn-primary whitespace-nowrap"
        >
          {installing ? 'Installing...' : 'Install Skill'}
        </button>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <div className="card">
          <div className="card-header">
            <h3 className="font-semibold">Source</h3>
          </div>
          <div className="card-body space-y-2">
            <div className="flex justify-between">
              <span className="text-[var(--color-text-secondary)]">Owner</span>
              <span className="font-mono">{skill.owner}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-[var(--color-text-secondary)]">Repository</span>
              <span className="font-mono">{skill.repo}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-[var(--color-text-secondary)]">Folder</span>
              <span className="font-mono">{skill.skill_folder}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-[var(--color-text-secondary)]">Hash</span>
              <span className="font-mono text-xs">{skill.skill_folder_hash?.substring(0, 16)}...</span>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="card-header">
            <h3 className="font-semibold">Metadata</h3>
          </div>
          <div className="card-body space-y-2">
            {skill.version && (
              <div className="flex justify-between">
                <span className="text-[var(--color-text-secondary)]">Version</span>
                <span>{skill.version}</span>
              </div>
            )}
            {skill.author && (
              <div className="flex justify-between">
                <span className="text-[var(--color-text-secondary)]">Author</span>
                <span>{skill.author}</span>
              </div>
            )}
            {skill.license && (
              <div className="flex justify-between">
                <span className="text-[var(--color-text-secondary)]">License</span>
                <span>{skill.license}</span>
              </div>
            )}
            {skill.homepage && (
              <div className="flex justify-between">
                <span className="text-[var(--color-text-secondary)]">Homepage</span>
                <a href={skill.homepage} target="_blank" rel="noopener noreferrer" className="text-[var(--color-primary)] hover:underline">
                  {skill.homepage}
                </a>
              </div>
            )}
            {skill.tags && (
              <div className="flex justify-between">
                <span className="text-[var(--color-text-secondary)]">Tags</span>
                <span>{skill.tags}</span>
              </div>
            )}
          </div>
        </div>

        <div className="card">
          <div className="card-header">
            <h3 className="font-semibold">Timestamps</h3>
          </div>
          <div className="card-body space-y-2">
            <div className="flex justify-between">
              <span className="text-[var(--color-text-secondary)]">Discovered</span>
              <span>{formatDateTime(skill.discovered_at)}</span>
            </div>
            {skill.indexed_at && (
              <div className="flex justify-between">
                <span className="text-[var(--color-text-secondary)]">Indexed</span>
                <span>{formatDateTime(skill.indexed_at)}</span>
              </div>
            )}
            {skill.last_checked_at && (
              <div className="flex justify-between">
                <span className="text-[var(--color-text-secondary)]">Last Checked</span>
                <span>{formatRelativeTime(skill.last_checked_at)}</span>
              </div>
            )}
          </div>
        </div>
      </div>

      {readmeHtml && (
        <div className="card">
          <div className="card-header">
            <h3 className="font-semibold">README</h3>
          </div>
          <div className="card-body markdown" dangerouslySetInnerHTML={{ __html: readmeHtml }} />
        </div>
      )}

      {skillMdHtml && (
        <div className="card">
          <div className="card-header">
            <h3 className="font-semibold">SKILL.md</h3>
          </div>
          <div className="card-body markdown" dangerouslySetInnerHTML={{ __html: skillMdHtml }} />
        </div>
      )}

      <div className="flex gap-4">
        <Link to="/dashboard" className="btn btn-secondary">
          Back to Dashboard
        </Link>
        <a href={skill.source_url} target="_blank" rel="noopener noreferrer" className="btn btn-ghost">
          View on GitHub
        </a>
      </div>
    </div>
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