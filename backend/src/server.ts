/**
 * Server Entry Point
 * Purpose: Initialize and start the Express server
 */
import dotenv from 'dotenv';
dotenv.config();

// Temporary debug logging to verify environment variables
console.log('SUPABASE_URL:', !!process.env.SUPABASE_URL);
console.log('SUPABASE_KEY:', !!process.env.SUPABASE_SERVICE_ROLE_KEY);

import app from './app'
import { config } from './config/config'
import { logger } from './utils/logger'

const PORT = config.port || 3001

// Start server
app.listen(PORT, () => {
  logger.info(`Server running on port ${PORT}`)
  logger.info(`Environment: ${config.nodeEnv}`)
})
