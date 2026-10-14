import { Navigate, Outlet } from 'react-router-dom'
import { UserInfo } from '../api/client'

interface ProtectedRouteProps {
  user: UserInfo | null
}

export function ProtectedRoute({ user }: ProtectedRouteProps) {
  if (!user) {
    return <Navigate to="/login" replace />
  }
  return <Outlet />
}