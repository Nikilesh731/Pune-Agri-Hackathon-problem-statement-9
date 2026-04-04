import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { 
  LayoutDashboard, 
  Users, 
  FileText, 
  Upload,
  Sprout
} from 'lucide-react'
import { cn } from '../../lib/utils'

const mobileNavigation = [
  { name: 'Dashboard', href: '/', icon: LayoutDashboard },
  { name: 'Farmer Records', href: '/farmer-records', icon: Users },
  { name: 'Applications', href: '/applications', icon: FileText },
  { name: 'Upload', href: '/upload', icon: Upload },
]

export function MobileNavigation() {
  return (
    <div className="md:hidden">
      <div className="flex items-center justify-between bg-white border-b border-gray-200 px-4 py-3 shadow-sm">
        <motion.div 
          className="flex items-center"
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.3 }}
        >
          <div className="w-8 h-8 bg-gradient-to-br from-green-600 to-green-700 rounded-lg flex items-center justify-center shadow-md">
            <Sprout className="w-5 h-5 text-white" />
          </div>
          <div className="ml-3">
            <h2 className="text-lg font-bold text-gray-900">Agri Office</h2>
          </div>
        </motion.div>
        
        <div className="flex space-x-1">
          {mobileNavigation.map((item, index) => {
            const Icon = item.icon
            return (
              <motion.div
                key={item.name}
                initial={{ opacity: 0, y: -20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.2, delay: index * 0.05 }}
              >
                <Link
                  to={item.href}
                  className={cn(
                    "p-2 rounded-xl transition-all duration-200",
                    "text-gray-600 hover:bg-gray-100 hover:text-gray-900 hover:shadow-sm",
                    "active:scale-95"
                  )}
                >
                  <Icon className="w-5 h-5" />
                </Link>
              </motion.div>
            )
          })}
        </div>
      </div>
    </div>
  )
}
