import { Outlet, NavLink, useNavigate } from 'react-router-dom'
import { useState } from 'react'
import { UserInfo } from '../api/client'
import { api } from '../api/client'
import { useToast } from './Toast'

interface LayoutProps {
  user: UserInfo
  onLogout: () => void
}

export function Layout({ user, onLogout }: LayoutProps) {
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [userMenuOpen, setUserMenuOpen] = useState(false)
  const navigate = useNavigate()
  const toast = useToast()

  const handleLogout = async () => {
    try {
      await api.logout()
    } catch {
      // ignore
    }
    onLogout()
    navigate('/login', { replace: true })
  }

  const handleDemoLogin = async () => {
    try {
      await api.demoLogin()
      toast.success('Demo login successful')
      setTimeout(() => window.location.reload(), 500)
    } catch (error) {
      toast.error('Demo login failed')
    }
  }

  const navItems = [
    { path: '/dashboard', label: 'Dashboard', icon: DashboardIcon },
    { path: '/settings', label: 'Settings', icon: SettingsIcon },
  ]

  return (
    <div className="min-h-screen bg-[var(--color-bg-secondary)]">
      <aside
        className={`fixed inset-y-0 left-0 z-40 w-64 bg-[var(--color-bg)] border-r border-[var(--color-border)] transform transition-transform duration-200 lg:translate-x-0 ${
          sidebarOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        <div className="flex flex-col h-full">
          <div className="flex items-center justify-between h-16 px-4 border-b border-[var(--color-border)]">
            <div className="flex items-center gap-2">
              <PrismIcon className="w-8 h-8 text-[var(--color-primary)]" />
              <span className="text-lg font-bold text-[var(--color-text)]">Prism</span>
            </div>
            <button
              className="lg:hidden p-2 rounded hover:bg-[var(--color-bg-secondary)]"
              onClick={() => setSidebarOpen(false)}
              aria-label="Close sidebar"
            >
              <MenuIcon className="w-5 h-5" />
            </button>
          </div>

          <nav className="flex-1 p-4 space-y-1 overflow-y-auto">
            {navItems.map((item) => (
              <NavLink
                key={item.path}
                to={item.path}
                className={({ isActive }) =>
                  `flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors ${
                    isActive
                      ? 'bg-[var(--color-primary)] text-white'
                      : 'text-[var(--color-text-secondary)] hover:bg-[var(--color-bg-secondary)] hover:text-[var(--color-text)]'
                  }`
              }>
                <item.icon className="w-5 h-5 flex-shrink-0" aria-hidden="true" />
                {item.label}
              </NavLink>
            ))}
          </nav>

          <div className="p-4 border-t border-[var(--color-border)]">
            <div className="flex items-center gap-3 px-3 py-2">
              <UserIcon className="w-8 h-8 text-[var(--color-primary)]" aria-hidden="true" />
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-[var(--color-text)] truncate">{user.username || user.email || 'User'}</p>
                <p className="text-xs text-[var(--color-text-muted)] truncate">{user.email}</p>
              </div>
              <button
                onClick={() => setUserMenuOpen(!userMenuOpen)}
                className="p-1 rounded hover:bg-[var(--color-bg-secondary)]"
                aria-label="User menu"
                aria-expanded={userMenuOpen}
              >
                <ChevronDownIcon className={`w-4 h-4 transition-transform ${userMenuOpen ? 'rotate-180' : ''}`} />
              </button>
            </div>

            {userMenuOpen && (
              <div className="dropdown-menu mt-2">
                <div className="dropdown-item px-3 py-2 text-sm text-[var(--color-text-secondary)]">
                  Role: {user.role}
                </div>
                <div className="dropdown-divider" />
                <button
                  onClick={handleDemoLogin}
                  className="dropdown-item w-full text-left px-3 py-2 text-sm text-[var(--color-primary)] hover:bg-[var(--color-bg-secondary)]"
                >
                  Demo Login
                </button>
                <button
                  onClick={handleLogout}
                  className="dropdown-item w-full text-left px-3 py-2 text-sm text-[var(--color-error)] hover:bg-[var(--color-bg-secondary)]"
                >
                  <LogoutIcon className="w-4 h-4 inline mr-2" />
                  Logout
                </button>
              </div>
            )}
          </div>
        </div>
      </aside>

      <div className="lg:pl-64 flex flex-col min-h-screen">
        <header className="sticky top-0 z-30 h-16 bg-[var(--color-bg)] border-b border-[var(--color-border)] lg:hidden">
          <div className="flex items-center justify-between h-full px-4">
            <button
              onClick={() => setSidebarOpen(true)}
              className="p-2 rounded hover:bg-[var(--color-bg-secondary)]"
              aria-label="Open sidebar"
            >
              <MenuIcon className="w-6 h-6" />
            </button>
            <div className="flex-1 text-center">
              <span className="text-lg font-bold text-[var(--color-text)]">Prism Workbench</span>
            </div>
            <div className="w-10" />
          </div>
        </header>

        <main className="flex-1 p-4 lg:p-8">
          <Outlet />
        </main>
      </div>

      {sidebarOpen && (
        <div
          className="fixed inset-0 z-30 bg-black/50 lg:hidden"
          onClick={() => setSidebarOpen(false)}
          aria-hidden="true"
        />
      )}
    </div>
  )
}

function PrismIcon({ className, ...props }: React.SVGProps<SVGSVGElement>) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className} {...props}>
      <path d="M12 2L2 7l10 5 10-5-10-5z" />
      <path d="M2 17l10 5 10-5" />
      <path d="M2 12l10 5 10-5" />
    </svg>
  )
}

function DashboardIcon({ className, ...props }: React.SVGProps<SVGSVGElement>) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className} {...props}>
      <rect x="3" y="3" width="7" height="7" rx="1" />
      <rect x="14" y="3" width="7" height="7" rx="1" />
      <rect x="3" y="14" width="7" height="7" rx="1" />
      <rect x="14" y="14" width="7" height="7" rx="1" />
    </svg>
  )
}

function SettingsIcon({ className, ...props }: React.SVGProps<SVGSVGElement>) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className} {...props}>
      <circle cx="12" cy="12" r="3" />
      <path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42" />
    </svg>
  )
}

function UserIcon({ className, ...props }: React.SVGProps<SVGSVGElement>) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className} {...props}>
      <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
      <circle cx="12" cy="7" r="4" />
    </svg>
  )
}

function MenuIcon({ className, ...props }: React.SVGProps<SVGSVGElement>) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className} {...props}>
      <line x1="3" y1="12" x2="21" y2="12" />
      <line x1="3" y1="6" x2="21" y2="6" />
      <line x1="3" y1="18" x2="21" y2="18" />
    </svg>
  )
}

function ChevronDownIcon({ className, ...props }: React.SVGProps<SVGSVGElement>) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className} {...props}>
      <polyline points="6 9 12 15 18 9" />
    </svg>
  )
}

function LogoutIcon({ className, ...props }: React.SVGProps<SVGSVGElement>) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className} {...props}>
      <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
      <polyline points="16 17 21 12 16 7" />
      <line x1="21" y1="12" x2="9" y2="12" />
    </svg>
  )
}