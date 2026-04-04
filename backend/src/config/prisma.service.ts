/**
 * Prisma Service
 * Purpose: Injectable Prisma client service for NestJS using the singleton pattern
 */
import { Injectable, OnModuleInit, OnModuleDestroy } from '@nestjs/common';
import { prisma } from './prisma';

@Injectable()
export class PrismaService implements OnModuleInit, OnModuleDestroy {
  private client = prisma

  async onModuleInit() {
    // Prisma singleton is already connected, but we ensure connection here
    try {
      await this.client.$connect()
      console.log('[PrismaService] Connected to database via singleton')
    } catch (error) {
      console.error('[PrismaService] Failed to connect:', error)
    }
  }

  async onModuleDestroy() {
    // Don't disconnect here since it's a singleton
    // Let the main app handle disconnection
  }

  // Proxy all PrismaClient methods to the singleton instance
  get $connect() {
    return this.client.$connect.bind(this.client)
  }

  get $disconnect() {
    return this.client.$disconnect.bind(this.client)
  }

  get $queryRaw() {
    return this.client.$queryRaw.bind(this.client)
  }

  get $queryRawUnsafe() {
    return this.client.$queryRawUnsafe.bind(this.client)
  }

  get $executeRaw() {
    return this.client.$executeRaw.bind(this.client)
  }

  get $executeRawUnsafe() {
    return this.client.$executeRawUnsafe.bind(this.client)
  }

  get $transaction() {
    return this.client.$transaction.bind(this.client)
  }

  get application() {
    return this.client.application
  }

  get document() {
    return this.client.document
  }

  get fraudCase() {
    return this.client.fraudCase
  }

  get officer() {
    return this.client.officer
  }

  get department() {
    return this.client.department
  }

  get $on() {
    return this.client.$on.bind(this.client)
  }
}
