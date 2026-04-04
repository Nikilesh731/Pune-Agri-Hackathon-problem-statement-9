import express from 'express'
import cors from 'cors'
import helmet from 'helmet'
import morgan from 'morgan'
import { config } from './config/config'
import { errorHandler } from './middlewares/errorHandler'
import { asyncHandler } from './middlewares/asyncHandler'
import { applicationsRoutes } from './modules/applications/applications.routes'
import { aiOrchestratorRoutes } from './modules/ai-orchestrator/ai-orchestrator.routes'
import dashboardRoutes from './routes/dashboardRoutes'

const app = express()

app.use(helmet())

const allowedOrigins = Array.isArray(config.corsOrigin)
  ? config.corsOrigin
  : String(config.corsOrigin || '')
      .split(',')
      .map((o) => o.trim())
      .filter(Boolean)

const corsOptions: cors.CorsOptions = {
  origin: (origin, callback) => {
    console.log(`[CORS] Incoming origin: ${origin || 'undefined'}`)
    console.log(`[CORS] Allowed origins:`, allowedOrigins)

    if (!origin) {
      return callback(null, true)
    }

    const isDevelopment = config.nodeEnv ==='production'
    const isLocalhost =
      origin.startsWith('http://localhost:') ||
      origin.startsWith('http://127.0.0.1:')

    if (allowedOrigins.includes(origin) || (isDevelopment && isLocalhost)) {
      return callback(null, true)
    }

    console.log(`[CORS] Blocking origin: ${origin}`)
    return callback(null, false)
  },
  credentials: true,
  methods: ['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS'],
  allowedHeaders: ['Content-Type', 'Authorization', 'X-Requested-With'],
}

app.use(cors(corsOptions))
app.options('*', cors(corsOptions))

app.use(morgan('combined'))
app.use(express.json({ limit: '10mb' }))
app.use(express.urlencoded({ extended: true }))

app.get('/health', asyncHandler(async (req, res) => {
  res.json({
    status: 'OK',
    timestamp: new Date().toISOString(),
    service: 'AI Smart Agriculture Backend',
  })
}))

app.use('/api/applications', applicationsRoutes)
app.use('/api/ai-orchestrator', aiOrchestratorRoutes)
app.use('/api/dashboard', dashboardRoutes)

app.use(errorHandler)

export default app