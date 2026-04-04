/**
 * Auth Layout Component
 * Purpose: Layout wrapper for authentication pages (login, register, etc.)
 */
import { Outlet } from 'react-router-dom'

export function AuthLayout() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="max-w-md w-full space-y-8">
        <div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
            Agriculture Administration
          </h2>
        </div>
        <Outlet />
      </div>
    </div>
  )
}
