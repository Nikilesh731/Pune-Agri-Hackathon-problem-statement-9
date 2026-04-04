/**
 * Prisma Client Configuration
 * Purpose: Singleton-safe Prisma client setup for the application
 */
import { PrismaClient } from '../../generated/prisma'

// Global variable to hold the Prisma client instance
declare global {
  // Allow global `var` declarations
  // eslint-disable-next-line no-var
  var __prisma: PrismaClient | undefined
}

// Create a singleton Prisma client
const prisma = globalThis.__prisma || new PrismaClient({
  log: process.env.NODE_ENV === 'development' ? 
    ['query', 'info', 'warn', 'error'] : 
    ['error'],
  errorFormat: 'pretty',
})

// In development, save the client instance to global to avoid hot-reload issues
if (process.env.NODE_ENV === 'development') {
  globalThis.__prisma = prisma
  console.log('[Prisma] Development mode: singleton client cached in global')
}

/**
 * Graceful shutdown handler for Prisma client
 */
export const disconnectPrisma = async (): Promise<void> => {
  try {
    await prisma.$disconnect()
    console.log('Prisma client disconnected successfully')
  } catch (error) {
    console.error('Error disconnecting Prisma client:', error)
    throw error
  }
}

/**
 * Health check for Prisma connection
 */
export const checkPrismaHealth = async (): Promise<{ connected: boolean; message: string }> => {
  try {
    await prisma.$queryRaw`SELECT 1`
    return { connected: true, message: 'Prisma database connection healthy' }
  } catch (error) {
    return { 
      connected: false, 
      message: `Prisma connection failed: ${error instanceof Error ? error.message : 'Unknown error'}` 
    }
  }
}

// Export the configured Prisma client
export { prisma }
export default prisma
