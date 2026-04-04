/**
 * Dashboard Layout Component
 * Purpose: Main application layout with navigation and sidebar for authenticated users - Agricultural Admin Theme
 */
import { Outlet } from 'react-router-dom'
import { Sidebar } from '../components/Navigation/Sidebar'
import { MobileNavigation } from '../components/Navigation/MobileNavigation'

export function DashboardLayout() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-green-50/30 to-gray-50">
      {/* Agricultural themed background with subtle radial accents */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-0 right-0 w-96 h-96 bg-green-100/20 rounded-full blur-3xl"></div>
        <div className="absolute bottom-0 left-0 w-80 h-80 bg-amber-50/15 rounded-full blur-3xl"></div>
        <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-64 h-64 bg-emerald-50/10 rounded-full blur-2xl"></div>
      </div>
      
      {/* Mobile Navigation */}
      <MobileNavigation />
      
      <div className="relative flex">
        {/* Desktop Sidebar */}
        <Sidebar />
        
        {/* Main Content */}
        <main className="flex-1 md:pl-0">
          <div className="max-w-6xl mx-auto px-6 sm:px-8 lg:px-10 py-8">
            <div className="agri-surface rounded-2xl agri-shadow-lg backdrop-blur-sm min-h-screen">
              <div className="p-8">
                <Outlet />
              </div>
            </div>
          </div>
        </main>
      </div>
    </div>
  )
}
