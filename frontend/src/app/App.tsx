/**
 * Root App Component
 * Purpose: Main application wrapper with routing setup
 */
import { Routes, Route } from 'react-router-dom'
import { DashboardLayout } from '../layouts/DashboardLayout'
import { DashboardPage } from '../pages/DashboardPage'
import { ApplicationsPage } from '../pages/ApplicationsPage'
import { ApplicationDetailPage } from '../pages/ApplicationDetailPage'
import { FarmerRecordsPage } from '../pages/FarmerRecordsPage'
import { FarmerDetailPage } from '../pages/FarmerDetailPage'
import { VerificationPage } from '../pages/VerificationPage'
import { NotFoundPage } from '../pages/NotFoundPage'
import { UploadPage } from '../features/applications/pages/UploadPage'
import { Toaster } from '../components/ui/Toaster'

function App() {
  return (
    <div className="App">
      <Routes>
        {/* Main application routes with dashboard layout */}
        <Route path="/" element={<DashboardLayout />}>
          <Route index element={<DashboardPage />} />
          <Route path="applications" element={<ApplicationsPage />} />
          <Route path="applications/:id" element={<ApplicationDetailPage />} />
          <Route path="farmer-records" element={<FarmerRecordsPage />} />
          <Route path="farmers/:farmerId" element={<FarmerDetailPage />} />
          <Route path="verification" element={<VerificationPage />} />
          <Route path="upload" element={<UploadPage />} />
        </Route>
        
        {/* Fallback route */}
        <Route path="*" element={<NotFoundPage />} />
      </Routes>
      <Toaster />
    </div>
  )
}

export default App
