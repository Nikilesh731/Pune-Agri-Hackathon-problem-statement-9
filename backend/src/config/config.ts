/**
 * Application Configuration
 * Purpose: Centralized configuration management
 */
import dotenv from 'dotenv'

dotenv.config()

interface Config {
  port: number
  nodeEnv: string
  corsOrigin: string | string[]
  jwtSecret: string
  jwtExpiresIn: string
  bcryptRounds: number
  databaseUrl: string
  directUrl: string
  aiServiceUrl?: string
}

export const config: Config = {
  port: parseInt(process.env.PORT || '3001', 10),
  nodeEnv: process.env.NODE_ENV || 'development',
  corsOrigin: process.env.CORS_ORIGIN
    ? process.env.CORS_ORIGIN.split(',')
        .map(origin => origin.trim())
        .filter(Boolean)
    : [
        'http://localhost:3000',
        'http://localhost:3002',
        'http://127.0.0.1:3000',
        'http://127.0.0.1:3002',
        'https://pune-agri-hackathon-problem-stateme.vercel.app'
      ],
  jwtSecret: process.env.JWT_SECRET || 'your-secret-key',
  jwtExpiresIn: process.env.JWT_EXPIRES_IN || '24h',
  bcryptRounds: parseInt(process.env.BCRYPT_ROUNDS || '12', 10),
  databaseUrl: process.env.DATABASE_URL || '',
  directUrl: process.env.DIRECT_URL || '',
  aiServiceUrl: process.env.AI_SERVICE_URL,
}

// Debug log to verify CORS origins
console.log('Loaded CORS_ORIGIN:', config.corsOrigin)

// Validate required database environment variables
if (!config.databaseUrl) {
  throw new Error('DATABASE_URL environment variable is required')
}

if (!config.directUrl) {
  throw new Error('DIRECT_URL environment variable is required')
}
