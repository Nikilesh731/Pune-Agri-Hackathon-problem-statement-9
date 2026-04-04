import { ReactNode } from 'react'
import { motion } from 'framer-motion'
import { Card } from './Card'
import { cn } from '../../lib/utils'

interface StatCardProps {
  title: string
  value: string | number
  icon?: ReactNode
  color?: 'blue' | 'green' | 'yellow' | 'red' | 'indigo' | 'purple' | 'gray'
  trend?: {
    value: string
    isPositive: boolean
  }
  className?: string
  variant?: 'default' | 'elevated' | 'outlined'
}

export function StatCard({ 
  title, 
  value, 
  icon, 
  color = 'green', 
  trend, 
  className,
  variant = 'elevated'
}: StatCardProps) {
  const colorClasses = {
    blue: 'bg-blue-500',
    green: 'bg-green-600',
    yellow: 'bg-yellow-500',
    red: 'bg-red-500',
    indigo: 'bg-indigo-500',
    purple: 'bg-purple-500',
    gray: 'bg-gray-500'
  }

  const bgColors = {
    blue: 'bg-blue-50/80 border-blue-200/60',
    green: 'bg-green-50/80 border-green-200/60',
    yellow: 'bg-yellow-50/80 border-yellow-200/60',
    red: 'bg-red-50/80 border-red-200/60',
    indigo: 'bg-indigo-50/80 border-indigo-200/60',
    purple: 'bg-purple-50/80 border-purple-200/60',
    gray: 'bg-gray-50/80 border-gray-200/60'
  }

  const iconBgColors = {
    blue: 'bg-blue-100',
    green: 'bg-green-100',
    yellow: 'bg-yellow-100',
    red: 'bg-red-100',
    indigo: 'bg-indigo-100',
    purple: 'bg-purple-100',
    gray: 'bg-gray-100'
  }

  return (
    <motion.div
      whileHover={{ y: -4, scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
      transition={{ duration: 0.2, ease: "easeOut" }}
    >
      <Card 
        variant={variant === 'default' ? 'default' : variant}
        hover="lift"
        className={cn(
          bgColors[color],
          'border-2 agri-transition backdrop-blur-sm relative overflow-hidden',
          className
        )}
      >
        {/* Subtle background pattern */}
        <div className="absolute inset-0 opacity-[0.03]">
          <div className="absolute inset-0 bg-gradient-to-br from-transparent via-white/20 to-transparent"></div>
        </div>
        
        <div className="relative flex items-center">
          <div className="flex-shrink-0">
            {icon ? (
              <div className={cn(
                "w-12 h-12 rounded-2xl flex items-center justify-center agri-shadow",
                iconBgColors[color]
              )}>
                {icon}
              </div>
            ) : (
              <div className={cn(
                "w-12 h-12 rounded-2xl flex items-center justify-center agri-shadow",
                iconBgColors[color]
              )}>
                <div className={cn("w-6 h-6 rounded-lg", colorClasses[color])}></div>
              </div>
            )}
          </div>
          <div className="ml-5 w-0 flex-1">
            <dl>
              <dt className="text-sm font-semibold text-gray-600 truncate mb-2 leading-tight">
                {title}
              </dt>
              <dd className="flex items-baseline">
                <div className="text-3xl font-bold text-gray-900 leading-tight">{value}</div>
                {trend && (
                  <div className={`ml-3 flex items-baseline text-sm font-semibold px-2 py-1 rounded-lg ${
                    trend.isPositive 
                      ? 'text-green-700 bg-green-100/70' 
                      : 'text-red-700 bg-red-100/70'
                  }`}>
                    <span className="mr-1">
                      {trend.isPositive ? '↑' : '↓'}
                    </span>
                    {trend.value}
                  </div>
                )}
              </dd>
            </dl>
          </div>
        </div>
      </Card>
    </motion.div>
  )
}
