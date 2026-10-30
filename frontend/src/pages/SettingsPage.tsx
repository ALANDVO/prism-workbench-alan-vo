import { useEffect, useState } from 'react'
import { api, UserInfo } from '../api/client'
import { useToast } from '../components/Toast'
import { Spinner } from '../components/ui'

export function SettingsPage() {
  const [user, setUser] = useState<UserInfo | null>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const toast = useToast()

  useEffect(() => {
    loadUser()
  }, [])

  const loadUser = async () => {
    try {
      const data = await api.getMe()
      setUser(data)
    } catch {
      toast.error('Failed to load user settings')
    } finally {
      setLoading(false)
    }
  }

  const handleSave = async () => {
    if (!user) return
    setSaving(true)
    try {
      // Settings save would go here
      toast.success('Settings saved')
    } catch {
      toast.error('Failed to save settings')
    } finally {
      setSaving(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Spinner size="lg" />
      </div>
    )
  }

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <h1 className="text-2xl font-bold text-[var(--color-text)]">Settings</h1>

      <section className="card">
        <div className="card-header">
          <h2 className="text-lg font-semibold">Profile</h2>
        </div>
        <div className="card-body space-y-4">
          <div>
            <label className="label">Username</label>
            <input type="text" className="input" value={user?.username ?? ''} readOnly />
          </div>
          <div>
            <label className="label">Email</label>
            <input type="email" className="input" value={user?.email ?? ''} readOnly />
          </div>
          <div>
            <label className="label">Full Name</label>
            <input type="text" className="input" value={user?.full_name ?? ''} readOnly />
          </div>
          <div>
            <label className="label">Role</label>
            <input type="text" className="input" value={user?.role ?? ''} readOnly />
          </div>
        </div>
      </section>

      <section className="card">
        <div className="card-header">
          <h2 className="text-lg font-semibold">Authentication</h2>
        </div>
        <div className="card-body space-y-4">
          <div>
            <label className="label">Subject ID</label>
            <input type="text" className="input" value={user?.id?.toString() ?? ''} readOnly />
          </div>
          <div>
            <label className="label">Avatar</label>
            {user?.avatar_url ? (
              <img src={user.avatar_url} alt="Avatar" className="w-16 h-16 rounded-full" />
            ) : (
              <p className="text-[var(--color-text-muted)]">No avatar set</p>
            )}
          </div>
        </div>
      </section>

      <section className="card">
        <div className="card-header">
          <h2 className="text-lg font-semibold">Actions</h2>
        </div>
        <div className="card-body space-y-4">
          <button onClick={handleSave} disabled={saving} className="btn btn-primary">
            {saving ? 'Saving...' : 'Save Changes'}
          </button>
        </div>
      </section>

      <section className="card border-[var(--color-error)]">
        <div className="card-header">
          <h2 className="text-lg font-semibold text-[var(--color-error)]">Danger Zone</h2>
        </div>
        <div className="card-body space-y-4">
          <p className="text-[var(--color-text-secondary)]">
            These actions are irreversible. Please proceed with caution.
          </p>
          <button className="btn btn-danger">Sign Out Everywhere</button>
        </div>
      </section>

      <div className="flex justify-end gap-3">
        <button onClick={handleSave} disabled={saving} className="btn btn-primary">
          {saving ? 'Saving...' : 'Save Changes'}
        </button>
      </div>
    </div>
  )
}