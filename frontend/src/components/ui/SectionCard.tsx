import { ReactNode } from 'react'
import { motion } from 'framer-motion'
import { cn } from '../../lib/utils'

interface SectionCardProps {
  title: ReactNode
  children: ReactNode
  className?: string
  variant?: 'default' | 'compact' | 'elevated'
}

export function SectionCard({ 
  title, 
  children, 
  className,
  variant = 'default'
}: SectionCardProps) {
  const variants = {
    default: "agri-card rounded-2xl agri-shadow-lg p-8",
    compact: "agri-card rounded-xl agri-shadow p-6",
    elevated: "agri-card rounded-2xl agri-shadow-lg p-8"
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className={cn(variants[variant], className)}
    >
      <h2 className="text-xl font-bold text-green-800 mb-6 leading-tight">
        {title}
      </h2>
      {children}
    </motion.div>
  )
}
