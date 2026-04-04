export function LoadingState({ message = 'Loading...' }: { message?: string }) {
  return (
    <div className="flex justify-center items-center h-64">
      <div className="text-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-green-600 mx-auto mb-4"></div>
        <div className="text-gray-500">{message}</div>
      </div>
    </div>
  )
}
