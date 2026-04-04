import { useLocation, Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { 
  LayoutDashboard, 
  Users, 
  FileText, 
  Upload, 
  CheckCircle, 
  Sprout
} from 'lucide-react'
import { cn } from '../../lib/utils'

const navigation = [
  { name: 'Dashboard', href: '/', icon: LayoutDashboard },
  { name: 'Farmer Records', href: '/farmer-records', icon: Users },
  { name: 'Case Management', href: '/applications', icon: FileText },
  { name: 'Upload Documents', href: '/upload', icon: Upload },
  { name: 'Verification Queue', href: '/verification', icon: CheckCircle },
]

export function Sidebar() {
  const location = useLocation()

  const baseClasses = "group flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200 cursor-pointer"
  const activeClasses = "bg-green-600 text-white shadow-sm"
  const inactiveClasses = "text-gray-600 hover:bg-green-600 hover:text-white"

  return (
    <div className="hidden md:flex md:w-72 md:flex-col">
      <div className="flex flex-col flex-grow pt-6 agri-surface agri-shadow-lg border-r border-gray-200/60 overflow-y-auto">
        {/* Logo/Brand Section */}
        <div className="flex items-center flex-shrink-0 px-8 pb-6 border-b border-gray-200/50">
          <motion.div 
            className="flex items-center"
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.3 }}
          >
            <div className="w-12 h-12 agri-primary rounded-2xl flex items-center justify-center agri-shadow">
              <Sprout className="w-7 h-7 text-white" />
            </div>
            <div className="ml-4">
              <h2 className="text-xl font-bold text-green-800">Agri Office</h2>
              <p className="text-sm text-gray-600 font-medium">Administration Portal</p>
            </div>
          </motion.div>
        </div>
        
        {/* Navigation */}
        <div className="mt-8 flex-1 flex flex-col">
          <nav className="flex-1 px-6 pb-6 space-y-2">
            {navigation.map((item, index) => {
              const isActive = location.pathname === item.href || 
                             (item.href !== '/' && location.pathname.startsWith(item.href))
              const Icon = item.icon
              
              return (
                <motion.div
                  key={item.name}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ duration: 0.2, delay: index * 0.05 }}
                >
                  <Link
                    to={item.href}
                    className={`${baseClasses} ${
                      isActive ? activeClasses : inactiveClasses
                    }`}
                  >
                    <Icon 
                      className={`w-5 h-5 ${
                        isActive ? "text-white" : "text-gray-500 group-hover:text-white"
                      }`}
                    />
                    <span className={cn(
                      "transition-all duration-200",
                      isActive ? "font-semibold text-white" : "font-medium"
                    )}>
                      {item.name}
                    </span>
                    {isActive && (
                      <motion.div
                        className="ml-auto w-2 h-2 bg-white rounded-full shadow-sm"
                        layoutId="activeIndicator"
                        initial={{ scale: 0 }}
                        animate={{ scale: 1 }}
                        transition={{ duration: 0.2 }}
                      />
                    )}
                  </Link>
                </motion.div>
              )
            })}
          </nav>
          
          {/* System Status Card */}
          <div className="px-6 py-6 border-t border-gray-200/50">
            <motion.div
              className="bg-green-50 rounded-2xl p-5 border border-green-200/60 agri-shadow"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3, delay: 0.5 }}
            >
              <div className="flex items-center mb-3">
                <div className="w-8 h-8 bg-green-500 rounded-xl flex items-center justify-center shadow-sm">
                  <span className="text-white text-sm font-bold">i</span>
                </div>
                <h3 className="ml-3 text-sm font-semibold text-green-800">System Status</h3>
              </div>
              <p className="text-xs text-green-700 leading-relaxed">All systems operational. Last sync: 2 mins ago</p>
              <div className="mt-3 flex items-center space-x-1">
                <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                <span className="text-xs text-green-600">Live</span>
              </div>
            </motion.div>
          </div>
        </div>
      </div>
    </div>
  )
}
