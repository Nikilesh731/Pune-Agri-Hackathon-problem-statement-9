import { Injectable, Logger } from '@nestjs/common';
import { prisma } from '../../config/prisma';

@Injectable()
export class CaseService {
  private readonly logger = new Logger(CaseService.name);

  constructor() {}

  public readonly CASE_TYPE_MAPPING: Record<string, string> = {
    scheme_application: 'scheme_case',
    subsidy_claim: 'subsidy_case',
    insurance_claim: 'insurance_case',
    grievance: 'grievance_case',
  };

  private readonly CASE_REQUIREMENTS: Record<string, string[]> = {
    scheme_case: ['scheme_application'],
    subsidy_case: ['subsidy_claim'],
    insurance_case: ['insurance_claim'],
    grievance_case: ['grievance'],
  };

  async resolveCase(params: {
    applicationId: string;
    farmerId?: string;
    documentType: string;
  }) {
    const { applicationId, farmerId, documentType } = params;

    if (!farmerId) {
      this.logger.warn(`No farmerId provided for application ${applicationId}`);
      return null;
    }

    const caseType = this.CASE_TYPE_MAPPING[documentType] || null;
    if (!caseType) {
      this.logger.debug(`No case mapping for document type: ${documentType}`);
      return null;
    }

    try {
      const existingCase = await this.findMatchingCase(farmerId, caseType);
      
      if (existingCase) {
        await this.attachApplicationToCase(applicationId, existingCase.id);
        this.logger.log(`Attached application ${applicationId} to existing case ${existingCase.id}`);
        return existingCase;
      } else {
        const newCase = await this.createCase(farmerId, caseType, documentType);
        await this.attachApplicationToCase(applicationId, newCase.id);
        this.logger.log(`Created new case ${newCase.id} and attached application ${applicationId}`);
        return newCase;
      }
    } catch (error) {
      this.logger.error(`Error resolving case for application ${applicationId}:`, error);
      throw error;
    }
  }

  async findMatchingCase(farmerId: string, caseType: string) {
    return prisma.case.findFirst({
      where: {
        farmerId,
        caseType,
        status: {
          not: 'resolved',
        },
      },
      orderBy: {
        createdAt: 'desc',
      },
    });
  }

  private async createCase(farmerId: string, caseType: string, documentType: string) {
    const title = `${caseType.replace('_', ' ').toUpperCase()} - ${new Date().toISOString().split('T')[0]}`;
    
    return prisma.case.create({
      data: {
        farmerId,
        caseType,
        status: 'open',
        title,
        summary: `Case created for ${documentType}`,
      },
    });
  }

  private async attachApplicationToCase(applicationId: string, caseId: string) {
    return prisma.application.update({
      where: { id: applicationId },
      data: { caseId },
    });
  }

  getMissingDocuments(caseType: string, documentsInCase: string[]): string[] {
    const requiredDocuments = this.CASE_REQUIREMENTS[caseType] || [];
    return requiredDocuments.filter((doc: string) => !documentsInCase.includes(doc));
  }

  async getCaseSummary(caseId: string) {
    return prisma.case.findUnique({
      where: { id: caseId },
      select: {
        id: true,
        caseType: true,
        status: true
      }
    });
  }

  async getCaseWithApplications(caseId: string) {
    return prisma.case.findUnique({
      where: { id: caseId },
      include: {
        applications: {
          select: {
            id: true,
            type: true,
            status: true,
            createdAt: true,
            extractedData: true,
          },
        },
        farmer: {
          select: {
            id: true,
            name: true,
            aadhaarNumber: true,
            mobileNumber: true,
          },
        },
      },
    });
  }

  async getCasesByFarmer(farmerId: string) {
    return prisma.case.findMany({
      where: { farmerId },
      include: {
        applications: {
          select: {
            id: true,
            type: true,
            status: true,
            createdAt: true,
          },
        },
      },
      orderBy: {
        createdAt: 'desc',
      },
    });
  }

  async getCaseHistoryForApplication(applicationId: string) {
    // Get the application with case info
    const application = await prisma.application.findUnique({
      where: { id: applicationId },
      select: {
        id: true,
        farmerId: true,
        caseId: true,
        type: true,
        status: true,
        createdAt: true
      }
    });

    if (!application) {
      return [];
    }

    if (!application.caseId || !application.farmerId) {
      // No case associated, return just this application
      return [{
        document_type: application.type,
        status: application.status,
        created_at: application.createdAt
      }];
    }

    // Get all applications for the same case
    const caseWithApplications = await prisma.case.findUnique({
      where: { id: application.caseId },
      include: {
        applications: {
          select: {
            id: true,
            type: true,
            status: true,
            createdAt: true,
            decisionDate: true
          },
          orderBy: {
            createdAt: 'asc'
          }
        }
      }
    });

    if (!caseWithApplications) {
      return [{
        document_type: application.type,
        status: application.status,
        created_at: application.createdAt
      }];
    }

    // Format as case history
    return caseWithApplications.applications.map(app => ({
      document_type: app.type,
      status: app.status,
      created_at: app.createdAt,
      decision_date: app.decisionDate
    }));
  }
}
