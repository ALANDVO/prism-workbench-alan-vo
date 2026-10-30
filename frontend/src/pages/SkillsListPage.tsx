import { useEffect, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { api, Skill, PaginatedResponse } from '../api/client'
import { useToast } from '../components/Toast'
import { SkillCard } from '../components/SkillCard'
import { SkillSearch } from '../components/SkillSearch'
import { Spinner, Select, Card, Button, Pagination } from '../components/ui'

interface SkillsListFilters {
  page: number
  page_size: number
  search?: string
  owner?: string
  status?: string
}

export function SkillsListPage() {
  const [skills, setSkills] = useState<Skill[]>([])
  const [loading, setLoading] = useState(true)
  const [total, setTotal] = useState(0)
  const [totalPages, setTotalPages] = useState(0)
  const [filters, setFilters] = useState<SkillsListFilters>({
    page: 1,
    page_size: 12,
  })
  const [searchParams, setSearchParams] = useSearchParams()
  const toast = useToast()

  // Initialize filters from URL search params
  useEffect(() => {
    const page = parseInt(searchParams.get('page') || '1', 10)
    const pageSize = parseInt(searchParams.get('page_size') || '12', 10)
    const search = searchParams.get('search') || undefined
    const owner = searchParams.get('owner') || undefined
    const status = searchParams.get('status') || undefined

    setFilters({
      page: isNaN(page) ? 1 : page,
      page_size: isNaN(pageSize) ? 12 : pageSize,
      search,
      owner,
      status,
    })
  }, [searchParams])

  // Load skills when filters change
  useEffect(() => {
    loadSkills()
  }, [filters])

  const loadSkills = async () => {
    setLoading(true)
    try {
      const params: Record<string, string | number> = {
        page: filters.page,
        page_size: filters.page_size,
      }
      if (filters.search) params.search = filters.search
      if (filters.owner) params.owner = filters.owner
      if (filters.status) params.status = filters.status

      const response = await api.get<PaginatedResponse<Skill>>('/skills', params)
      setSkills(response.items)
      setTotal(response.total)
      setTotalPages(response.total_pages)
    } catch (error) {
      toast.error('Failed to load skills')
      console.error(error)
    } finally {
      setLoading(false)
    }
  }

  const handleFilterChange = (newFilters: Partial<SkillsListFilters>) => {
    const updatedFilters = { ...filters, ...newFilters, page: 1 }
    setFilters(updatedFilters)
    const newParams = new URLSearchParams()
    Object.entries(updatedFilters).forEach(([key, value]) => {
      if (value !== undefined && value !== '') {
        newParams.set(key, String(value))
      }
    })
    setSearchParams(newParams, { replace: true })
  }

  const handlePageChange = (page: number) => {
    handleFilterChange({ page })
  }

  const handleSearch = (query: string) => {
    handleFilterChange({ search: query || undefined })
  }

  const handleOwnerFilter = (event: React.ChangeEvent<HTMLSelectElement>) => {
    handleFilterChange({ owner: event.target.value || undefined })
  }

  const handleStatusFilter = (event: React.ChangeEvent<HTMLSelectElement>) => {
    handleFilterChange({ status: event.target.value || undefined })
  }

  const clearFilters = () => {
    handleFilterChange({ search: undefined, owner: undefined, status: undefined })
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Spinner className="h-8 w-8" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-[var(--color-text-primary)]">Skills</h1>
          <p className="text-[var(--color-text-secondary)] mt-1">
            {total} skill{total !== 1 ? 's' : ''} found
          </p>
        </div>
        <Link to="/discover" className="btn btn-primary">
          <svg className="h-4 w-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          Discover Skills
        </Link>
      </div>

      <Card className="space-y-4">
        <div className="flex flex-col sm:flex-row gap-4">
          <SkillSearch
            value={filters.search || ''}
            onSearch={handleSearch}
            placeholder="Search skills..."
          />
          <Select
            value={filters.owner || ''}
            onChange={handleOwnerFilter}
            placeholder="Filter by owner"
            options={[
              { value: '', label: 'All owners' },
              ...Array.from(new Set(skills.map((s) => s.owner))).map((owner) => ({
                value: owner,
                label: owner,
              })),
            ]}
            className="w-full sm:w-48"
          />
          <Select
            value={filters.status || ''}
            onChange={handleStatusFilter}
            placeholder="Filter by status"
            options={[
              { value: '', label: 'All statuses' },
              { value: 'discovered', label: 'Discovered' },
              { value: 'indexed', label: 'Indexed' },
              { value: 'installed', label: 'Installed' },
              { value: 'updated', label: 'Updated' },
              { value: 'failed', label: 'Failed' },
              { value: 'removed', label: 'Removed' },
            ]}
            className="w-full sm:w-48"
          />
        </div>

        {(filters.search || filters.owner || filters.status) && (
          <Button variant="ghost" size="sm" onClick={clearFilters}>
            Clear filters
          </Button>
        )}
      </Card>

      {skills.length === 0 ? (
        <Card>
          <div className="text-center py-12 text-[var(--color-text-secondary)]">
            <svg
              className="mx-auto h-12 w-12 text-[var(--color-text-muted)] mb-4"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1.5}
                d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
            <p className="text-lg">No skills found</p>
            <p className="mt-1">
              {filters.search || filters.owner || filters.status
                ? 'Try adjusting your filters or'
                : 'Get started by'}
              {' '}
              <Link to="/discover" className="text-[var(--color-primary)] hover:underline">
                discovering skills
              </Link>
              {filters.search || filters.owner || filters.status ? ' from a repository' : ''}
            </p>
          </div>
        </Card>
      ) : (
        <>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
            {skills.map((skill) => (
              <SkillCard key={skill.id} skill={skill} installed={false} />
            ))}
          </div>

          {totalPages > 1 && (
            <Pagination
              currentPage={filters.page}
              totalPages={totalPages}
              onPageChange={handlePageChange}
            />
          )}
        </>
      )}
    </div>
  )
}
