import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "../../lib/utils"

const statusBadgeVariants = cva(
  "inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium transition-all duration-200",
  {
    variants: {
      variant: {
        default: "bg-gray-100 text-gray-800",
        success: "bg-green-100 text-green-800 border border-green-200",
        warning: "bg-yellow-100 text-yellow-800 border border-yellow-200", 
        danger: "bg-red-100 text-red-800 border border-red-200",
        info: "bg-blue-100 text-blue-800 border border-blue-200",
        pending: "bg-blue-100 text-blue-800 border border-blue-200",
        processing: "bg-yellow-100 text-yellow-800 border border-yellow-200",
        approved: "bg-green-100 text-green-800 border border-green-200",
        rejected: "bg-red-100 text-red-800 border border-red-200",
        active: "bg-green-100 text-green-800 border border-green-200",
        inactive: "bg-gray-100 text-gray-800 border border-gray-200",
      },
      size: {
        sm: "px-2 py-0.5 text-xs",
        default: "px-2.5 py-0.5 text-xs",
        lg: "px-3 py-1 text-sm",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
)

export interface StatusBadgeProps
  extends React.HTMLAttributes<HTMLSpanElement>,
    VariantProps<typeof statusBadgeVariants> {
  status: string
}

const StatusBadge = React.forwardRef<HTMLSpanElement, StatusBadgeProps>(
  ({ className, variant, size, status, ...props }, ref) => {
    const getStatusVariant = (status: string) => {
      switch (status.toLowerCase()) {
        case 'uploaded':
        case 'pending':
          return 'pending'
        case 'processing':
          return 'processing'
        case 'processed':
        case 'approved':
        case 'active':
          return 'approved'
        case 'under_review':
        case 'needs_review':
          return 'warning'
        case 'rejected':
          return 'rejected'
        case 'inactive':
          return 'inactive'
        default:
          return 'default'
      }
    }

    const badgeVariant = variant || getStatusVariant(status)

    return (
      <span
        ref={ref}
        className={cn(statusBadgeVariants({ variant: badgeVariant, size, className }))}
        {...props}
      >
        {status.replace('_', ' ').charAt(0).toUpperCase() + status.replace('_', ' ').slice(1)}
      </span>
    )
  }
)
StatusBadge.displayName = "StatusBadge"

export { StatusBadge, statusBadgeVariants }
