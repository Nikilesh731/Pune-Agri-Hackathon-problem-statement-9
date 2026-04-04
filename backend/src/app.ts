/**
 * Express App Configuration
 * Purpose: Configure Express middleware and routes
 */
import express from 'express'
import cors from 'cors'
import helmet from 'helmet'
import morgan from 'morgan'
import { config } from './config/config'
import { errorHandler } from './middlewares/errorHandler'
import { asyncHandler } from './middlewares/asyncHandler'
// Import routes
import { applicationsRoutes } from './modules/applications/applications.routes'
import { aiOrchestratorRoutes } from './modules/ai-orchestrator/ai-orchestrator.routes'
import dashboardRoutes from './routes/dashboardRoutes'

const app = express()

// Security middleware
app.use(helmet())

// CORS configuration with multiple origins and debug logging
const corsOptions = {
  origin: function (origin: string | undefined, callback: (err: Error | null, allow?: boolean) => void) {
    // Log the incoming origin for debugging
    console.log(`[CORS] Incoming origin: ${origin || 'undefined'}`)
    console.log(`[CORS] Allowed origins:`, config.corsOrigin)
    
    // Allow requests with no origin (like mobile apps or curl requests)
    if (!origin) {
      return callback(null, true)
    }
    
    // Check if the origin is in the allowed list
    const allowedOrigins = Array.isArray(config.corsOrigin) ? config.corsOrigin : [config.corsOrigin]
    
    // In development, also allow localhost and 127.0.0.1 on any port
    const isDevelopment = config.nodeEnv === 'development'
    const isLocalhost = origin.startsWith('http://localhost:') || origin.startsWith('http://127.0.0.1:')
    
    if (allowedOrigins.includes(origin) || (isDevelopment && isLocalhost)) {
      console.log(`[CORS] Allowing origin: ${origin}`)
      callback(null, true)
    } else {
      console.log(`[CORS] Blocking origin: ${origin}`)
      callback(new Error(`CORS blocked for origin: ${origin}`))
    }
  },
  credentials: true,
  methods: ['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS'],
  allowedHeaders: ['Content-Type', 'Authorization', 'X-Requested-With'],
}

app.use(cors(corsOptions))

// Handle preflight requests
app.options('*', cors(corsOptions))

// Logging middleware
app.use(morgan('combined'))

// Body parsing middleware
app.use(express.json({ limit: '10mb' }))
app.use(express.urlencoded({ extended: true }))

// Health check endpoint
app.get('/health', asyncHandler(async (req, res) => {
  res.json({
    status: 'OK',
    timestamp: new Date().toISOString(),
    service: 'AI Smart Agriculture Backend',
  })
}))

// API routes
app.use('/api/applications', applicationsRoutes)
app.use('/api/ai-orchestrator', aiOrchestratorRoutes)
app.use('/api/dashboard', dashboardRoutes)

// Error handling middleware (must be last)
app.use(errorHandler)

export default app
