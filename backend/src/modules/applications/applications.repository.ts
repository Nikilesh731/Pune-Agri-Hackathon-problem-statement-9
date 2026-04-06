/**
 * Applications Repository
 * Purpose: Database interaction layer for application management using Prisma ORM
 */
import { prisma } from '../../config/prisma'
import { Application, CreateApplicationInput, UpdateApplicationInput, ApplicationQuery, ApplicationFilters } from './applications.types'
import { ApplicationStatus } from '../../../generated/prisma'

class ApplicationsRepository {
  /**
   * Create a new application in the database
   */
  async createApplication(applicationData: CreateApplicationInput): Promise<Application> {
    try {
      const application = await prisma.application.create({
        data: {
          applicantId: applicationData.applicantId || '',
          schemeId: applicationData.schemeId || '',
          type: applicationData.type || '',
          status: ApplicationStatus.UPLOADED,
          fileName: applicationData.fileName || null,
          fileUrl: applicationData.fileUrl || null,
          fileSize: applicationData.fileSize ? BigInt(applicationData.fileSize) : null,
          fileType: applicationData.fileType || null,
          personalInfo: applicationData.personalInfo || {} as any,
          farmInfo: applicationData.farmInfo || null as any,
          documents: applicationData.documents || [] as any,
          rawFileHash: (applicationData as any).rawFileHash || null,
          normalizedContentHash: (applicationData as any).normalizedContentHash || null,
          versionNumber: applicationData.versionNumber || 1,
          parentApplicationId: applicationData.parentApplicationId || null
        }
      })
      
      return this.mapPrismaApplicationToApplication(application)
    } catch (error) {
      throw new Error(`Failed to create application: ${error instanceof Error ? error.message : 'Unknown error'}`)
    }
  }

  /**
   * Get applications with pagination and filtering
   */
  async getApplications(query: ApplicationQuery): Promise<{ applications: Application[], total: number }> {
    try {
      console.log('[ApplicationsRepository] fetching applications')
      
      const { page = 1, limit = 10, filters, sortBy = 'submissionDate', sortOrder = 'desc' } = query
      const offset = (page - 1) * limit
      
      const whereConditions: any = {}
      
      if (filters) {
        if (filters.status) {
          whereConditions.status = filters.status.toUpperCase() as ApplicationStatus
        }
        if (filters.applicantId) {
          whereConditions.applicantId = filters.applicantId
        }
        if (filters.schemeId) {
          whereConditions.schemeId = filters.schemeId
        }
        if (filters.priorityMin !== undefined || filters.priorityMax !== undefined) {
          whereConditions.priorityScore = {}
          if (filters.priorityMin !== undefined) {
            whereConditions.priorityScore.gte = filters.priorityMin
          }
          if (filters.priorityMax !== undefined) {
            whereConditions.priorityScore.lte = filters.priorityMax
          }
        }
        if (filters.submissionDateFrom || filters.submissionDateTo) {
          whereConditions.submissionDate = {}
          if (filters.submissionDateFrom) {
            whereConditions.submissionDate.gte = filters.submissionDateFrom
          }
          if (filters.submissionDateTo) {
            whereConditions.submissionDate.lte = filters.submissionDateTo
          }
        }
      }
      
      // SEQUENTIAL execution to avoid connection pool timeout with limit 1
      console.log('[ApplicationsRepository] fetching applications data...')
      const applications = await prisma.application.findMany({
        where: whereConditions,
        orderBy: { [sortBy]: sortOrder },
        skip: offset,
        take: limit
      })
      
      console.log('[ApplicationsRepository] counting total applications...')
      const total = await prisma.application.count({ where: whereConditions })
      
      console.log(`[ApplicationsRepository] fetched ${applications.length} applications, total: ${total}`)
      
      return {
        applications: applications.map(app => this.mapPrismaApplicationToApplication(app)),
        total
      }
    } catch (error) {
      console.error('[ApplicationsRepository] error fetching applications:', error)
      throw new Error(`Failed to get applications: ${error instanceof Error ? error.message : 'Unknown error'}`)
    }
  }

  /**
   * Get application by ID
   */
  async getApplicationById(id: string): Promise<Application | null> {
    try {
      const application = await prisma.application.findUnique({
        where: { id }
      })
      
      return application ? this.mapPrismaApplicationToApplication(application) : null
    } catch (error) {
      throw new Error(`Failed to get application by ID: ${error instanceof Error ? error.message : 'Unknown error'}`)
    }
  }

  /**
   * Update application
   */
  async updateApplication(id: string, updateData: UpdateApplicationInput): Promise<Application> {
    try {
      const updateFields: any = {}
      
      if (updateData.status !== undefined) {
        // Some environments/databases may not yet have the CASE_READY enum value.
        // Map CASE_READY to a DB-safe fallback value to avoid runtime errors
        // until the database enum is migrated to include CASE_READY.
        let statusVal = updateData.status.toString().toUpperCase();
        // If an older codepath wrote a legacy 'PROCESSED' value, map it
        // to the new `CASE_READY` enum now that the database has been migrated.
        if (statusVal === 'PROCESSED') {
          statusVal = 'CASE_READY'
        }
        updateFields.status = statusVal as ApplicationStatus
      }
      if (updateData.priorityScore !== undefined) {
        updateFields.priorityScore = updateData.priorityScore
      }
      if (updateData.reviewerId !== undefined) {
        updateFields.reviewerId = updateData.reviewerId
      }
      if (updateData.notes !== undefined) {
        updateFields.notes = updateData.notes
      }
      if (updateData.documents !== undefined) {
        updateFields.documents = updateData.documents as any
      }
      if (updateData.farmInfo !== undefined) {
        updateFields.farmInfo = updateData.farmInfo as any
      }
      if (updateData.extractedData !== undefined) {
        updateFields.extractedData = updateData.extractedData as any
      }
      if (updateData.aiSummary !== undefined) {
        updateFields.aiSummary = updateData.aiSummary
      }
      if (updateData.priorityScore !== undefined) {
        updateFields.priorityScore = updateData.priorityScore
      }
      if (updateData.fraudRiskScore !== undefined) {
        updateFields.fraudRiskScore = updateData.fraudRiskScore
      }
      if (updateData.fraudFlags !== undefined) {
        updateFields.fraudFlags = updateData.fraudFlags as any
      }
      if (updateData.verificationRecommendation !== undefined) {
        updateFields.verificationRecommendation = updateData.verificationRecommendation
      }
      if (updateData.aiProcessingStatus !== undefined) {
        updateFields.aiProcessingStatus = updateData.aiProcessingStatus
      }
      if (updateData.ocrProcessedAt !== undefined) {
        updateFields.ocrProcessedAt = updateData.ocrProcessedAt
      }
      if (updateData.aiProcessedAt !== undefined) {
        updateFields.aiProcessedAt = updateData.aiProcessedAt
      }
      if (updateData.rawExtractedText !== undefined) {
        updateFields.rawExtractedText = updateData.rawExtractedText
      }
      if (updateData.farmerId !== undefined) {
        updateFields.farmerId = updateData.farmerId
      }
      if (updateData.versionNumber !== undefined) {
        updateFields.versionNumber = updateData.versionNumber
      }
      if (updateData.parentApplicationId !== undefined) {
        updateFields.parentApplicationId = updateData.parentApplicationId
      }
      if ((updateData as any).rawFileHash !== undefined) {
        updateFields.rawFileHash = (updateData as any).rawFileHash
      }
      if ((updateData as any).normalizedContentHash !== undefined) {
        updateFields.normalizedContentHash = (updateData as any).normalizedContentHash
      }
            
      const application = await prisma.application.update({
        where: { id },
        data: updateFields
      })
      
      return this.mapPrismaApplicationToApplication(application)
    } catch (error) {
      throw new Error(`Failed to update application: ${error instanceof Error ? error.message : 'Unknown error'}`)
    }
  }

  /**
   * Delete application
   */
  async deleteApplication(id: string): Promise<void> {
    try {
      await prisma.application.delete({
        where: { id }
      })
    } catch (error) {
      throw new Error(`Failed to delete application: ${error instanceof Error ? error.message : 'Unknown error'}`)
    }
  }

  /**
   * Delete all applications for local test reset
   */
  async deleteAllApplications(): Promise<{ deletedCount: number; errors?: string[] }> {
    console.log('[REPOSITORY] Deleting ALL applications');
    
    try {
      const deleteResult = await prisma.application.deleteMany({});
      
      console.log('[REPOSITORY] Delete result:', {
        count: deleteResult.count,
        deletedCount: deleteResult.count
      });
      
      return {
        deletedCount: deleteResult.count
      };
    } catch (error) {
      console.error('[REPOSITORY] Error deleting all applications:', error);
      throw new Error(`Failed to delete all applications: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  /**
   * Find applications by applicant ID
   */
  async findByApplicantId(applicantId: string): Promise<Application[]> {
    try {
      const applications = await prisma.application.findMany({
        where: { applicantId },
        orderBy: { createdAt: 'desc' }
      })
      
      return applications.map(app => this.mapPrismaApplicationToApplication(app))
    } catch (error) {
      throw new Error(`Failed to find applications by applicant ID: ${error instanceof Error ? error.message : 'Unknown error'}`)
    }
  }

  /**
   * Update application status
   */
  async updateStatus(id: string, status: string): Promise<Application> {
    return this.updateApplication(id, { status })
  }

  /**
   * Update extracted data for an application
   */
  async updateExtractedData(id: string, extractedData: any): Promise<Application> {
    return this.updateApplication(id, { extractedData })
  }

  /**
   * Map Prisma Application to Application object
   */
  private mapPrismaApplicationToApplication(prismaApp: any): Application {
    // Repository mapper: Prisma to Application conversion
    
    if (prismaApp.extractedData?.canonical) {
      console.log('  - canonical.document_type from DB:', prismaApp.extractedData.canonical.document_type)
      console.log('  - canonical.verification.classification_confidence from DB:', prismaApp.extractedData.canonical.verification?.classification_confidence)
    }
    
    const mapped = {
      id: prismaApp.id,
      applicantId: prismaApp.applicantId,
      schemeId: prismaApp.schemeId,
      type: prismaApp.type,
      status: prismaApp.status.toLowerCase() as Application['status'],
      priorityScore: prismaApp.priorityScore ? Number(prismaApp.priorityScore) : undefined,
      fileName: prismaApp.fileName || undefined,
      fileUrl: prismaApp.fileUrl || undefined,
      fileSize: prismaApp.fileSize ? Number(prismaApp.fileSize) : undefined,
      fileType: prismaApp.fileType || undefined,
      documents: Array.isArray(prismaApp.documents) 
        ? prismaApp.documents.map((doc: any) => ({
            ...doc,
            version: doc.version ?? 1 // Safe fallback for backward compatibility
          }))
        : JSON.parse(prismaApp.documents || '[]').map((doc: any) => ({
            ...doc,
            version: doc.version ?? 1 // Safe fallback for backward compatibility
          })),
      personalInfo: typeof prismaApp.personalInfo === 'object' ? prismaApp.personalInfo : JSON.parse(prismaApp.personalInfo || '{}'),
      farmInfo: prismaApp.farmInfo ? (typeof prismaApp.farmInfo === 'object' ? prismaApp.farmInfo : JSON.parse(prismaApp.farmInfo)) : undefined,
      extractedData: prismaApp.extractedData ? (typeof prismaApp.extractedData === 'object' ? prismaApp.extractedData : JSON.parse(prismaApp.extractedData)) : undefined,
      aiSummary: prismaApp.aiSummary || undefined,
      fraudRiskScore: prismaApp.fraudRiskScore ? Number(prismaApp.fraudRiskScore) : undefined,
      fraudFlags: prismaApp.fraudFlags ? (Array.isArray(prismaApp.fraudFlags) ? prismaApp.fraudFlags : JSON.parse(prismaApp.fraudFlags || '[]')) : undefined,
      verificationRecommendation: prismaApp.verificationRecommendation || undefined,
      aiProcessingStatus: prismaApp.aiProcessingStatus || undefined,
      ocrProcessedAt: prismaApp.ocrProcessedAt || undefined,
      aiProcessedAt: prismaApp.aiProcessedAt || undefined,
      rawExtractedText: prismaApp.rawExtractedText || undefined,
      rawFileHash: prismaApp.rawFileHash || undefined,
      normalizedContentHash: prismaApp.normalizedContentHash || undefined,
      farmerId: prismaApp.farmerId || undefined,
      caseId: prismaApp.caseId || undefined,
      versionNumber: prismaApp.versionNumber || 1,
      parentApplicationId: prismaApp.parentApplicationId || undefined,
      submissionDate: prismaApp.submissionDate,
      reviewDate: prismaApp.reviewDate || undefined,
      decisionDate: prismaApp.decisionDate || undefined,
      reviewerId: prismaApp.reviewerId || undefined,
      notes: prismaApp.notes || undefined,
      createdAt: prismaApp.createdAt,
      updatedAt: prismaApp.updatedAt
    }
    
    // Repository mapper: conversion complete
    
    return mapped
  }

  /**
   * Repository health check
   */
  async healthCheck(): Promise<{ message: string; databaseConnected: boolean }> {
    try {
      console.log('[ApplicationsRepository] performing health check...')
      await prisma.$queryRaw`SELECT 1`
      console.log('[ApplicationsRepository] health check successful')
      return { 
        message: 'Applications repository working', 
        databaseConnected: true 
      }
    } catch (error) {
      console.error('[ApplicationsRepository] health check failed:', error)
      return { 
        message: 'Applications repository error', 
        databaseConnected: false 
      }
    }
  }

  /**
   * Find farmer by Aadhaar number
   */
  async findFarmerByAadhaar(aadhaarNumber: string): Promise<any | null> {
    try {
      const farmer = await prisma.farmer.findUnique({
        where: { aadhaarNumber: aadhaarNumber.trim() }
      })
      return farmer
    } catch (error) {
      console.error('[ApplicationsRepository] error finding farmer by Aadhaar:', error)
      return null
    }
  }

  /**
   * Find farmer by mobile number
   */
  async findFarmerByMobile(mobileNumber: string): Promise<any | null> {
    try {
      const farmer = await prisma.farmer.findFirst({
        where: { mobileNumber: mobileNumber.trim() }
      })
      return farmer
    } catch (error) {
      console.error('[ApplicationsRepository] error finding farmer by mobile:', error)
      return null
    }
  }

  /**
   * Create a new farmer
   */
  async createFarmer(data: any): Promise<any> {
    try {
      const farmer = await prisma.farmer.create({
        data: {
          name: data.name?.trim() || null,
          aadhaarNumber: data.aadhaarNumber?.trim() || null,
          mobileNumber: data.mobileNumber?.trim() || null,
          address: data.address?.trim() || null,
          village: data.village?.trim() || null,
          district: data.district?.trim() || null,
          state: data.state?.trim() || null
        }
      })
      return farmer
    } catch (error) {
      console.error('[ApplicationsRepository] error creating farmer:', error)
      throw new Error(`Failed to create farmer: ${error instanceof Error ? error.message : 'Unknown error'}`)
    }
  }

  /**
   * Update farmer data
   */
  async updateFarmer(id: string, data: any): Promise<any> {
    try {
      const updateFields: any = {}
      
      if (data.name !== undefined) updateFields.name = data.name?.trim() || null
      if (data.aadhaarNumber !== undefined) updateFields.aadhaarNumber = data.aadhaarNumber?.trim() || null
      if (data.mobileNumber !== undefined) updateFields.mobileNumber = data.mobileNumber?.trim() || null
      if (data.address !== undefined) updateFields.address = data.address?.trim() || null
      if (data.village !== undefined) updateFields.village = data.village?.trim() || null
      if (data.district !== undefined) updateFields.district = data.district?.trim() || null
      if (data.state !== undefined) updateFields.state = data.state?.trim() || null
      
      const farmer = await prisma.farmer.update({
        where: { id },
        data: updateFields
      })
      return farmer
    } catch (error) {
      console.error('[ApplicationsRepository] error updating farmer:', error)
      throw new Error(`Failed to update farmer: ${error instanceof Error ? error.message : 'Unknown error'}`)
    }
  }

  /**
   * Get all farmers with their linked applications (excluding blocked duplicate attempts)
   */
  async getAllFarmersWithApplications() {
    try {
      return await prisma.farmer.findMany({
        include: {
          applications: {
            select: {
              id: true,
              type: true,
              status: true,
              createdAt: true,
              fileName: true,
              fileType: true,
              submissionDate: true,
              extractedData: true,
              parentApplicationId: true,
              versionNumber: true,
              notes: true
            },
            where: {
              OR: [
                { notes: { not: { contains: 'Duplicate submission' } } },
                { notes: { equals: null } }
              ]
            },
            orderBy: {
              createdAt: 'desc'
            }
          }
        },
        orderBy: {
          createdAt: 'desc'
        }
      })
    } catch (error) {
      console.error('[ApplicationsRepository] error fetching farmers with applications:', error)
      throw new Error(`Failed to fetch farmers with applications: ${error instanceof Error ? error.message : 'Unknown error'}`)
    }
  }

  /**
   * Get a single farmer by ID with their linked applications
   */
  async getFarmerByIdWithApplications(farmerId: string) {
    try {
      const farmer = await prisma.farmer.findUnique({
        where: { id: farmerId },
        include: {
          applications: {
            select: {
              id: true,
              type: true,
              status: true,
              createdAt: true,
              fileName: true,
              fileType: true,
              submissionDate: true,
              extractedData: true,
              parentApplicationId: true,
              versionNumber: true,
              notes: true
            },
            where: {
              OR: [
                { notes: { not: { contains: 'Duplicate submission' } } },
                { notes: { equals: null } }
              ]
            },
            orderBy: {
              createdAt: 'desc'
            }
          }
        }
      })

      if (!farmer) {
        throw new Error('Farmer not found')
      }

      return farmer
    } catch (error) {
      console.error('[ApplicationsRepository] error fetching farmer by ID:', error)
      throw new Error(`Failed to fetch farmer: ${error instanceof Error ? error.message : 'Unknown error'}`)
    }
  }

  /**
   * Archive test data for cleanup
   */
  async archiveTestData(options: { applicantId: string; status: string; olderThanDays: number }) {
    try {
      const cutoffDate = new Date()
      cutoffDate.setDate(cutoffDate.getDate() - options.olderThanDays)
      
      // Delete old test applications (hard delete for test data)
      const result = await prisma.application.deleteMany({
        where: {
          applicantId: options.applicantId,
          status: options.status as any,
          createdAt: {
            lt: cutoffDate
          }
        }
      })
      
      console.log(`[REPOSITORY] Deleted ${result.count} test applications older than ${options.olderThanDays} days`)
      
      return result
    } catch (error) {
      console.error('[ApplicationsRepository] error archiving test data:', error)
      throw new Error(`Failed to archive test data: ${error instanceof Error ? error.message : 'Unknown error'}`)
    }
  }

  async findActiveApplication(applicantId: string, documentType: string): Promise<Application | null> {
    try {
      const application = await prisma.application.findFirst({
        where: {
          applicantId,
          type: documentType,
          status: {
            notIn: ['REJECTED', 'REQUIRES_ACTION']
          }
        }
      })
      
      return application ? this.mapPrismaApplicationToApplication(application) : null
    } catch (error) {
      console.error('[ApplicationsRepository] error finding active application:', error)
      throw new Error(`Failed to find active application: ${error instanceof Error ? error.message : 'Unknown error'}`)
    }
  }

  /**
   * Find latest application by applicant and type for re-upload logic
   * Returns the most recent application regardless of status
   */
  async findLatestApplicationByApplicantAndType(applicantId: string, documentType: string): Promise<Application | null> {
    try {
      const application = await prisma.application.findFirst({
        where: {
          applicantId,
          type: documentType
        },
        orderBy: {
          createdAt: 'desc'
        }
      })

      return application ? this.mapPrismaApplicationToApplication(application) : null
    } catch (error) {
      console.error('[ApplicationsRepository] error finding latest application:', error)
      throw new Error(`Failed to find latest application: ${error instanceof Error ? error.message : 'Unknown error'}`)
    }
  }

  /**
   * Find applications by farmer ID and document type for duplicate detection
   */
  async findApplicationsByFarmerAndType(farmerId: string, documentType: string): Promise<Application[]> {
    try {
      const applications = await prisma.application.findMany({
        where: {
          farmerId,
          type: documentType
        },
        orderBy: {
          createdAt: 'desc'
        }
      })

      return applications.map(app => this.mapPrismaApplicationToApplication(app))
    } catch (error) {
      console.error('[ApplicationsRepository] error finding applications by farmer and type:', error)
      throw new Error(`Failed to find applications by farmer and type: ${error instanceof Error ? error.message : 'Unknown error'}`)
    }
  }

  /**
   * Find applications by applicant ID for preflight duplicate checking
   */
  async findApplicationsByApplicantId(applicantId: string) {
    try {
      return await prisma.application.findMany({
        where: {
          applicantId
        },
        select: {
          id: true,
          type: true,
          status: true,
          createdAt: true,
          fileName: true,
          fileType: true,
          submissionDate: true,
          extractedData: true,
          parentApplicationId: true,
          versionNumber: true,
          notes: true
        },
        orderBy: {
          createdAt: 'desc'
        }
      })
    } catch (error) {
      console.error('[ApplicationsRepository] error finding applications by applicant:', error)
      throw new Error(`Failed to find applications by applicant: ${error instanceof Error ? error.message : 'Unknown error'}`)
    }
  }

  /**
   * Find applications by raw file hash for exact duplicate checking
   */
  async findApplicationsByRawFileHash(rawFileHash: string): Promise<Application[]> {
    try {
      console.log('[REPOSITORY] Searching for applications with raw file hash:', rawFileHash.substring(0, 16) + '...')
      
      const applications = await prisma.application.findMany({
        where: {
          rawFileHash: rawFileHash
        },
        orderBy: {
          createdAt: 'desc'
        }
      })

      console.log('[REPOSITORY] Found applications by raw file hash:', applications.length)
      return applications.map(app => this.mapPrismaApplicationToApplication(app))
    } catch (error) {
      console.error('[ApplicationsRepository] error finding applications by raw file hash:', error)
      throw new Error(`Failed to find applications by raw file hash: ${error instanceof Error ? error.message : 'Unknown error'}`)
    }
  }

  /**
   * Find applications by file hash for strict duplicate checking (LEGACY - use rawFileHash)
   * @deprecated Use findApplicationsByRawFileHash instead
   */
  async findApplicationsByFileHash(fileHash: string): Promise<Application[]> {
    try {
      console.log('[REPOSITORY] LEGACY findApplicationsByFileHash - redirecting to rawFileHash')
      return this.findApplicationsByRawFileHash(fileHash)
    } catch (error) {
      console.error('[ApplicationsRepository] error in legacy file hash lookup:', error)
      throw new Error(`Failed to find applications by file hash: ${error instanceof Error ? error.message : 'Unknown error'}`)
    }
  }

  /**
   * Find applications by filename and size for fallback duplicate checking
   */
  async findApplicationsByFileNameAndSize(
    fileName: string,
    fileSize: number,
    applicantId: string
  ): Promise<Application[]> {
    try {
      const applications = await prisma.application.findMany({
        where: {
          fileName,
          fileSize: BigInt(fileSize),
          applicantId
        },
        orderBy: {
          createdAt: 'desc'
        }
      })

      return applications.map(app => this.mapPrismaApplicationToApplication(app))
    } catch (error) {
      console.error('[ApplicationsRepository] error finding applications by filename and size:', error)
      throw new Error(`Failed to find applications by filename and size: ${error instanceof Error ? error.message : 'Unknown error'}`)
    }
  }

  /**
   * Find applications by normalized content hash for cross-format duplicate detection
   */
  async findApplicationsByNormalizedContentHash(normalizedContentHash: string): Promise<Application[]> {
    try {
      console.log('[REPOSITORY] Searching for applications with normalized content hash:', normalizedContentHash.substring(0, 16) + '...')
      
      const applications = await prisma.application.findMany({
        where: {
          normalizedContentHash: normalizedContentHash
        },
        orderBy: {
          createdAt: 'desc'
        }
      })

      console.log('[REPOSITORY] Found applications by content hash:', applications.length)
      applications.forEach(app => {
        console.log('[REPOSITORY] Application:', {
          id: app.id,
          status: app.status,
          fileName: app.fileName,
          hasContentHash: !!app.normalizedContentHash
        })
      })

      return applications.map(app => this.mapPrismaApplicationToApplication(app))
    } catch (error) {
      console.error('[ApplicationsRepository] error finding applications by normalized content hash:', error)
      throw new Error(`Failed to find applications by normalized content hash: ${error instanceof Error ? error.message : 'Unknown error'}`)
    }
  }

  /**
   * Find applications by content fingerprint for duplicate checking
   */
  async findApplicationsByFingerprint(
    fingerprint: string,
    farmerId: string,
    documentType: string
  ): Promise<Application[]> {
    try {
      const applications = await prisma.application.findMany({
        where: {
          normalizedContentHash: fingerprint,
          farmerId,
          type: {
            contains: documentType.toLowerCase().replace(/[-\s]+/g, '_'),
            mode: 'insensitive'
          }
        },
        orderBy: {
          createdAt: 'desc'
        }
      })

      return applications.map(app => this.mapPrismaApplicationToApplication(app))
    } catch (error) {
      console.error('[ApplicationsRepository] error finding applications by fingerprint:', error)
      throw new Error(`Failed to find applications by fingerprint: ${error instanceof Error ? error.message : 'Unknown error'}`)
    }
  }

  /**
   * Find all applications for a farmer
   */
  async findApplicationsByFarmer(farmerId: string): Promise<Application[]> {
    try {
      const applications = await prisma.application.findMany({
        where: {
          farmerId
        },
        orderBy: {
          createdAt: 'desc'
        }
      })

      return applications.map(app => this.mapPrismaApplicationToApplication(app))
    } catch (error) {
      console.error('[ApplicationsRepository] error finding applications by farmer:', error)
      throw new Error(`Failed to find applications by farmer: ${error instanceof Error ? error.message : 'Unknown error'}`)
    }
  }

  /**
   * Find applications for farmer timeline - ordered by creation date
   */
  async findApplicationsByFarmerForTimeline(farmerId: string): Promise<Application[]> {
    try {
      const applications = await prisma.application.findMany({
        where: {
          farmerId
        },
        orderBy: {
          createdAt: 'desc'
        },
        select: {
          id: true,
          type: true,
          status: true,
          createdAt: true,
          decisionDate: true,
          notes: true,
          extractedData: true,
          fileName: true,
          fileType: true
        }
      })

      return applications.map(app => this.mapPrismaApplicationToApplication(app))
    } catch (error) {
      console.error('[ApplicationsRepository] error finding applications for farmer timeline:', error)
      throw new Error(`Failed to find applications for farmer timeline: ${error instanceof Error ? error.message : 'Unknown error'}`)
    }
  }

  /**
   * Get all versions of an application (parent and children)
   */
  async getApplicationVersions(applicationId: string): Promise<Application[]> {
    try {
      // Get the root application (either the application itself or its parent)
      const rootApp = await prisma.application.findFirst({
        where: {
          OR: [
            { id: applicationId },
            { parentApplicationId: applicationId }
          ]
        }
      })

      if (!rootApp) {
        return []
      }

      const rootId = rootApp.parentApplicationId || rootApp.id

      // Get all versions in this family
      const allVersions = await prisma.application.findMany({
        where: {
          OR: [
            { id: rootId },
            { parentApplicationId: rootId }
          ]
        },
        orderBy: {
          versionNumber: 'desc'
        }
      })

      return allVersions.map(app => this.mapPrismaApplicationToApplication(app))
    } catch (error) {
      console.error('[ApplicationsRepository] error getting application versions:', error)
      throw new Error(`Failed to get application versions: ${error instanceof Error ? error.message : 'Unknown error'}`)
    }
  }

  /**
   * Find farmer by ID
   */
  async findFarmerById(farmerId: string): Promise<any> {
    try {
      const farmer = await prisma.farmer.findUnique({
        where: { id: farmerId }
      })
      return farmer
    } catch (error) {
      console.error('[ApplicationsRepository] error finding farmer by ID:', error)
      throw new Error(`Failed to find farmer by ID: ${error instanceof Error ? error.message : 'Unknown error'}`)
    }
  }
}

export const applicationsRepository = new ApplicationsRepository()
