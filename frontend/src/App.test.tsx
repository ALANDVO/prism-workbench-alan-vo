import { render, screen, waitFor } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { vi, Mock } from 'vitest'
import App from './App'
import { ToastProvider } from './components/Toast'

vi.mock('./api/client', () => ({
  api: {
    getMe: vi.fn<() => Promise<UserInfo | null>>(),
    get: vi.fn().mockResolvedValue({ items: [] }),
    logout: vi.fn(),
    demoLogin: vi.fn(),
  },
}))

import { api } from './api/client'

interface UserInfo {
  id: number
  subject: string
  email: string
  username: string
  full_name: string
  avatar_url: string | null
  role: 'viewer' | 'operator' | 'admin'
  is_active: boolean
}

const renderApp = (user: UserInfo | null = null) => {
  (api.getMe as Mock).mockResolvedValue(user)
  return render(
    <BrowserRouter>
      <ToastProvider>
        <App />
      </ToastProvider>
    </BrowserRouter>
  )
}

describe('App', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('shows loading spinner initially', () => {
    vi.mocked(api.getMe).mockImplementation(() => new Promise(() => {}))
    renderApp()
    expect(screen.getByLabelText('Loading')).toBeInTheDocument()
  })

  it('redirects to login when not authenticated', async () => {
    vi.mocked(api.getMe).mockRejectedValue(new Error('Unauthorized'))
    renderApp()
    await waitFor(() => {
      expect(screen.getByText('Prism Workbench')).toBeInTheDocument()
    })
    expect(screen.getByText('Sign in with Keycloak')).toBeInTheDocument()
  })

  it('renders dashboard when authenticated', async () => {
    const mockUser: UserInfo = {
      id: 1,
      subject: 'test-sub',
      email: 'test@example.com',
      username: 'testuser',
      full_name: 'Test User',
      avatar_url: null,
      role: 'operator',
      is_active: true,
    }
    vi.mocked(api.getMe).mockResolvedValue(mockUser)
    renderApp(mockUser)
    await waitFor(() => {
      expect(screen.getByText('Dashboard')).toBeInTheDocument()
    })
  })

  it('shows demo login button', async () => {
    vi.mocked(api.getMe).mockRejectedValue(new Error('Unauthorized'))
    renderApp()
    await waitFor(() => {
      expect(screen.getByText('Demo Login (Local Only)')).toBeInTheDocument()
    })
  })
})