import { ReactNode } from 'react'

interface DataTableProps {
  headers: { key: string; label: string; className?: string }[]
  data: any[]
  emptyMessage?: string
  children?: (row: any, index: number) => ReactNode
}

export function DataTable({ headers, data, emptyMessage = 'No data available', children }: DataTableProps) {
  if (data.length === 0) {
    return (
      <div className="text-center py-12 text-gray-500 border border-gray-200 rounded-lg">
        {emptyMessage}
      </div>
    )
  }

  return (
    <div className="overflow-hidden shadow ring-1 ring-black ring-opacity-5 md:rounded-lg">
      <table className="min-w-full divide-y divide-gray-300">
        <thead className="bg-gray-50">
          <tr>
            {headers.map((header) => (
              <th
                key={header.key}
                scope="col"
                className={`px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider ${header.className || ''}`}
              >
                {header.label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {data.map((row, index) => (
            <tr key={row.id || index}>
              {children ? children(row, index) : (
                headers.map((header) => (
                  <td key={header.key} className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {row[header.key]}
                  </td>
                ))
              )}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
