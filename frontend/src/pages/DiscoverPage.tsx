import { useState } from 'react'
import { api, Skill, SkillDiscoverRequest } from '../api/client'
import { useToast } from '../components/Toast'
import { Spinner, Input, Button, Card } from '../components/ui'
import { SkillCard } from '../components/SkillCard'

export function DiscoverPage() {
  const [repoUrl, setRepoUrl] = useState('')
  const [ref, setRef] = useState('main')
  const [discovering, setDiscovering] = useState(false)
  const [discoveredSkills, setDiscoveredSkills] = useState<Skill[]>([])
  const [showResults, setShowResults] = useState(false)
  const toast = useToast()

  const validateUrl = (url: string): boolean => {
    try {
      const parsed = new URL(url)
      return parsed.hostname === 'github.com' && parsed.pathname.split('/').filter(Boolean).length >= 2
    } catch {
      return false
    }
  }

  const handleDiscover = async () => {
    if (!validateUrl(repoUrl)) {
      toast.error('Please enter a valid GitHub repository URL')
      return
    }

    setDiscovering(true)
    setShowResults(false)
    try {
      const request: SkillDiscoverRequest = { repo_url: repoUrl, ref }
      const response = await api.post<{ discovered: number; skills: Skill[] }>('/skills/discover', request)
      setDiscoveredSkills(response.skills)
      setShowResults(true)
      if (response.discovered > 0) {
        toast.success(`Discovered ${response.discovered} skill(s)`)
      } else {
        toast.info('No skills found in this repository')
      }
    } catch (error) {
      toast.error('Failed to discover skills')
      console.error(error)
    } finally {
      setDiscovering(false)
    }
  }

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-[var(--color-text-primary)]">Discover Skills</h1>
        <p className="text-[var(--color-text-secondary)] mt-1">
          Enter a GitHub repository URL to discover skills from SKILL.md files
        </p>
      </div>

      <Card className="space-y-4">
        <div className="space-y-4">
          <div>
            <label htmlFor="repo-url" className="label">
              GitHub Repository URL
            </label>
            <Input
              id="repo-url"
              type="url"
              value={repoUrl}
              onChange={(e) => setRepoUrl(e.target.value)}
              placeholder="https://github.com/owner/repo"
              disabled={discovering}
              className="mt-1"
            />
            <p className="text-sm text-[var(--color-text-muted)] mt-1">
              Enter a public GitHub repository URL. Private repositories require a GitHub token configured on the server.
            </p>
          </div>

          <div>
            <label htmlFor="ref" className="label">
              Branch / Tag / Commit (optional)
            </label>
            <Input
              id="ref"
              type="text"
              value={ref}
              onChange={(e) => setRef(e.target.value)}
              placeholder="main"
              disabled={discovering}
              className="mt-1"
            />
            <p className="text-sm text-[var(--color-text-muted)] mt-1">
              Leave empty to use the default branch (usually main or master).
            </p>
          </div>

          <Button
            onClick={handleDiscover}
            disabled={discovering || !repoUrl.trim()}
            className="w-full"
            size="lg"
          >
            {discovering ? (
              <>
                <Spinner className="mr-2 h-4 w-4" />
                Discovering...
              </>
            ) : (
              'Discover Skills'
            )}
          </Button>
        </div>
      </Card>

      {showResults && (
        <Card>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-medium text-[var(--color-text-primary)]">
              Discovered Skills ({discoveredSkills.length})
            </h2>
          </div>
          {discoveredSkills.length === 0 ? (
            <div className="text-center py-8 text-[var(--color-text-secondary)]">
              No skills were discovered in this repository.
            </div>
          ) : (
            <div className="space-y-3">
              {discoveredSkills.map((skill) => (
                <SkillCard key={skill.id} skill={skill} installed={false} />
              ))}
            </div>
          )}
        </Card>
      )}
    </div>
  )
}
