/**
 * 404 Not Found Page Component
 * Purpose: Fallback page for undefined routes
 */
export function NotFoundPage() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="text-center">
        <h1 className="text-4xl font-bold text-gray-900 mb-4">404</h1>
        <p className="text-lg text-gray-600 mb-8">Page not found</p>
        <button className="bg-green-600 text-white px-4 py-2 rounded-md hover:bg-green-700">
          Go back home
        </button>
      </div>
    </div>
  )
}
