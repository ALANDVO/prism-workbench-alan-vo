import { useEffect, useState } from 'react'
import { api, Skill, Installation, PaginatedResponse } from '../api/client'
import { useToast } from '../components/Toast'
import { SkillCard } from '../components/SkillCard'
import { Spinner, EmptyState } from '../components/ui'

export function DashboardPage() {
  const toast = useToast()
  const [skills, setSkills] = useState<Skill[]>([])
  const [installations, setInstallations] = useState<Installation[]>([])
  const [loading, setLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')
  const [activeTab, setActiveTab] = useState<'installed' | 'discovered'>('installed')

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    setLoading(true)
    try {
      const [installedResp, skillsResp] = await Promise.all([
        api.get<PaginatedResponse<Installation>>('/installations', { page: 1, page_size: 50 }),
        api.get<PaginatedResponse<Skill>>('/skills', { page: 1, page_size: 50 }),
      ])
      setInstallations(installedResp.items)
      setSkills(skillsResp.items)
    } catch (error) {
      toast.error('Failed to load dashboard data')
    } finally {
      setLoading(false)
    }
  }

  const filteredSkills = skills.filter((skill) =>
    skill.skill_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    skill.description?.toLowerCase().includes(searchQuery.toLowerCase()) ||
    skill.owner.toLowerCase().includes(searchQuery.toLowerCase()) ||
    skill.repo.toLowerCase().includes(searchQuery.toLowerCase())
  )

  const installedSkillIds = new Set(installations.map((i) => i.skill_id))
  const installedSkills = filteredSkills.filter((s) => installedSkillIds.has(s.id))
  const availableSkills = filteredSkills.filter((s) => !installedSkillIds.has(s.id))

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Spinner size="lg" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-[var(--color-text)]">Dashboard</h1>
          <p className="text-[var(--color-text-secondary)]">Manage your agent skills</p>
        </div>
        <div className="flex items-center gap-2">
          <input
            type="text"
            placeholder="Search skills..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="input w-64"
          />
        </div>
      </div>

      <div className="tabs">
        <button
          className={`tab ${activeTab === 'installed' ? 'active' : ''}`}
          onClick={() => setActiveTab('installed')}
        >
          Installed ({installedSkills.length})
        </button>
        <button
          className={`tab ${activeTab === 'discovered' ? 'active' : ''}`}
          onClick={() => setActiveTab('discovered')}
        >
          Discovered ({availableSkills.length})
        </button>
      </div>

      {activeTab === 'installed' ? (
        installedSkills.length > 0 ? (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {installedSkills.map((skill) => (
              <SkillCard key={skill.id} skill={skill} installed={true} />
            ))}
          </div>
        ) : (
          <EmptyState
            icon={<PackageIcon className="w-12 h-12 text-[var(--color-text-muted)]" />}
            title="No skills installed"
            description="Discover and install skills from the Discovered tab"
          />
        )
      ) : (
        availableSkills.length > 0 ? (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {availableSkills.map((skill) => (
              <SkillCard key={skill.id} skill={skill} installed={false} />
            ))}
          </div>
        ) : (
          <EmptyState
            icon={<PackageIcon className="w-12 h-12 text-[var(--color-text-muted)]" />}
            title="No skills discovered"
            description="Use the API to discover skills from GitHub repositories"
          />
        )
      )}
    </div>
  )
}

function PackageIcon({ className, ...props }: React.SVGProps<SVGSVGElement>) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" className={className} {...props}>
      <path d="M12 2L2 7l10 5 10-5-10-5z" />
      <path d="M2 17l10 5 10-5" />
      <path d="M2 12l10 5 10-5" />
    </svg>
  )
}