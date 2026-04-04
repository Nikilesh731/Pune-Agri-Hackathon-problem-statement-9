/**
 * Database Configuration and Connection
 * Purpose: Centralized PostgreSQL/Supabase database connection management
 */
import { Pool, PoolClient } from 'pg'
import { config } from '../config/config'

class DatabaseConnection {
  private pool: Pool | null = null
  private isConnected = false

  /**
   * Initialize database connection pool
   */
  async connect(): Promise<void> {
    try {
      // Create connection pool with Supabase configuration
      this.pool = new Pool({
        connectionString: config.databaseUrl,
        max: 20, // Maximum number of connections in pool
        idleTimeoutMillis: 30000, // How long a client is allowed to remain idle before being closed
        connectionTimeoutMillis: 2000, // How long to wait when connecting a new client
      })

      // Test the connection
      const client = await this.pool.connect()
      await client.query('SELECT NOW()')
      client.release()

      this.isConnected = true
      console.log('✅ Database connected successfully to Supabase PostgreSQL')
      
      // Log connection info without exposing credentials
      const dbUrl = new URL(config.databaseUrl)
      console.log(`📊 Database host: ${dbUrl.hostname}, Database: ${dbUrl.pathname.slice(1)}`)
      
    } catch (error) {
      this.isConnected = false
      console.error('❌ Database connection failed:', error instanceof Error ? error.message : 'Unknown error')
      throw error
    }
  }

  /**
   * Get database connection pool
   */
  getPool(): Pool {
    if (!this.pool) {
      throw new Error('Database pool not initialized. Call connect() first.')
    }
    return this.pool
  }

  /**
   * Get a database client from the pool
   */
  async getClient(): Promise<PoolClient> {
    if (!this.pool) {
      throw new Error('Database pool not initialized. Call connect() first.')
    }
    return await this.pool.connect()
  }

  /**
   * Execute a query with automatic client management
   */
  async query<T = any>(text: string, params?: any[]): Promise<T[]> {
    const pool = this.getPool()
    const result = await pool.query(text, params)
    return result.rows
  }

  /**
   * Execute a query and return the first result
   */
  async queryOne<T = any>(text: string, params?: any[]): Promise<T | null> {
    const rows = await this.query<T>(text, params)
    return rows.length > 0 ? rows[0] : null
  }

  /**
   * Check if database is connected
   */
  isDatabaseConnected(): boolean {
    return this.isConnected && this.pool !== null
  }

  /**
   * Close all database connections
   */
  async disconnect(): Promise<void> {
    if (this.pool) {
      await this.pool.end()
      this.pool = null
      this.isConnected = false
      console.log('🔌 Database connection closed')
    }
  }

  /**
   * Get database connection status
   */
  getStatus(): { connected: boolean; totalConnections: number; idleConnections: number; waitingConnections: number } {
    if (!this.pool) {
      return {
        connected: false,
        totalConnections: 0,
        idleConnections: 0,
        waitingConnections: 0,
      }
    }

    return {
      connected: this.isConnected,
      totalConnections: this.pool.totalCount,
      idleConnections: this.pool.idleCount,
      waitingConnections: this.pool.waitingCount,
    }
  }
}

// Export singleton instance
export const database = new DatabaseConnection()

// Export types for use in repositories
export type { Pool, PoolClient }
