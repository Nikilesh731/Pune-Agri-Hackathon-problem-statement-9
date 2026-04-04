import { motion } from "framer-motion"
import { cn } from "../../lib/utils"

interface AnimatedPageWrapperProps {
  children: React.ReactNode
  className?: string
  variant?: "fade" | "slide" | "scale" | "slideUp"
}

const pageVariants = {
  fade: {
    initial: { opacity: 0 },
    animate: { opacity: 1 },
    exit: { opacity: 0 }
  },
  slide: {
    initial: { opacity: 0, x: -20 },
    animate: { opacity: 1, x: 0 },
    exit: { opacity: 0, x: 20 }
  },
  slideUp: {
    initial: { opacity: 0, y: 20 },
    animate: { opacity: 1, y: 0 },
    exit: { opacity: 0, y: -20 }
  },
  scale: {
    initial: { opacity: 0, scale: 0.95 },
    animate: { opacity: 1, scale: 1 },
    exit: { opacity: 0, scale: 0.95 }
  }
}

const pageTransition = {
  duration: 0.3,
  ease: "easeInOut" as const
}

export function AnimatedPageWrapper({ 
  children, 
  className, 
  variant = "fade" 
}: AnimatedPageWrapperProps) {
  return (
    <motion.div
      className={cn("w-full", className)}
      initial="initial"
      animate="animate"
      exit="exit"
      variants={pageVariants[variant]}
      transition={pageTransition}
    >
      {children}
    </motion.div>
  )
}

export function AnimatedSection({ 
  children, 
  className, 
  delay = 0 
}: { 
  children: React.ReactNode
  className?: string
  delay?: number 
}) {
  return (
    <motion.div
      className={cn(className)}
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ 
        duration: 0.4, 
        delay,
        ease: "easeOut" as const
      }}
    >
      {children}
    </motion.div>
  )
}

export function AnimatedCard({ 
  children, 
  className, 
  delay = 0 
}: { 
  children: React.ReactNode
  className?: string
  delay?: number 
}) {
  return (
    <motion.div
      className={cn(className)}
      initial={{ opacity: 0, y: 15, scale: 0.98 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ 
        duration: 0.3, 
        delay,
        ease: "easeOut" as const
      }}
      whileHover={{ y: -2, scale: 1.01 }}
      whileTap={{ scale: 0.99 }}
    >
      {children}
    </motion.div>
  )
}
