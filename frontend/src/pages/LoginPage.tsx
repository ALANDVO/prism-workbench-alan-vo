import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api/client'
import { useToast } from '../components/Toast'

export function LoginPage() {
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()
  const toast = useToast()

  const handleOIDCLogin = async () => {
    setLoading(true)
    try {
      await api.login()
    } catch {
      toast.error('Failed to initiate login')
      setLoading(false)
    }
  }

  const handleDemoLogin = async () => {
    setLoading(true)
    try {
      await api.demoLogin()
      toast.success('Demo login successful')
      navigate('/dashboard', { replace: true })
    } catch {
      toast.error('Demo login failed')
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-[var(--color-bg-secondary)] px-4">
      <div className="w-full max-w-md">
        <div className="card overflow-hidden">
          <div className="card-header text-center">
            <div className="flex items-center justify-center gap-2 mb-4">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="w-10 h-10 text-[var(--color-primary)]">
                <path d="M12 2L2 7l10 5 10-5-10-5z" />
                <path d="M2 17l10 5 10-5" />
                <path d="M2 12l10 5 10-5" />
              </svg>
              <h1 className="text-2xl font-bold text-[var(--color-text)]">Prism Workbench</h1>
            </div>
            <p className="text-[var(--color-text-secondary)]">Open agent skills management tool</p>
          </div>
          <div className="card-body space-y-4">
            <div className="relative">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-[var(--color-border)]" />
              </div>
              <div className="relative flex justify-center text-sm">
                <span className="px-2 bg-[var(--color-bg)] text-[var(--color-text-muted)]">Or continue with</span>
              </div>
            </div>

            <button
              onClick={handleOIDCLogin}
              disabled={loading}
              className="btn btn-primary w-full justify-center gap-2 py-3"
            >
              <svg viewBox="0 0 24 24" fill="currentColor" className="w-5 h-5" aria-hidden="true">
                <path d="M12 0C5.374 0 0 5.373 0 12c0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23A11.509 11.509 0 0112 5.803c1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576C20.566 21.797 24 17.3 24 12c0-6.627-5.373-12-12-12z"/>
              </svg>
              <span>Sign in with Keycloak</span>
            </button>

            <button
              onClick={handleDemoLogin}
              disabled={loading}
              className="btn btn-secondary w-full justify-center gap-2 py-3"
            >
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="w-5 h-5" aria-hidden="true">
                <circle cx="12" cy="12" r="10" />
                <path d="M12 6v6l4 2" />
              </svg>
              <span>Demo Login (Local Only)</span>
            </button>
          </div>
          <div className="card-footer text-center">
            <p className="text-sm text-[var(--color-text-muted)]">
              Demo mode creates a local operator account. Not available in production.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}