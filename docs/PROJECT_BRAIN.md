# PROJECT_BRAIN

Generated: 2026-04-03T09:25:33.993Z

## Purpose

This file is an auto-generated project summary for quickly bootstrapping a new AI/chat session with the current codebase context.

## ai-services/app

### main.py

- Path: `ai-services/app/main.py`
- Summary: FastAPI Main Application Purpose: Initialize and configure the AI services microservice
- Exports/Defines: startup_event, shutdown_event, health_check

## ai-services/app/api

### application_priority.py

- Path: `ai-services/app/api/application_priority.py`
- Summary: Application Priority Scoring API Provides priority scoring for agricultural applications
- Exports/Defines: score_application

### fraud_detection.py

- Path: `ai-services/app/api/fraud_detection.py`
- Summary: Fraud Detection API Provides fraud detection for agricultural applications
- Exports/Defines: detect_fraud

## ai-services/app/core

### config.py

- Path: `ai-services/app/core/config.py`
- Summary: Configuration Settings Purpose: Centralized configuration management for AI services
- Exports/Defines: Settings, Config

### llm_client.py

- Path: `ai-services/app/core/llm_client.py`
- Summary: Simple LLM Client for Agricultural Document Processing This client provides a simple interface to transformer-based models for generating AI analysis and insights.
- Exports/Defines: LLMClient, __init__, _initialize_model, generate_response

## ai-services/app/modules/ai_assist

### llm_assist_service.py

- Path: `ai-services/app/modules/ai_assist/llm_assist_service.py`
- Summary: LLM Assist Service for Agricultural Document Processing This service adds AI-based intelligence on top of extracted data without modifying the core extraction logic. It provides summaries, risk analysis, and decision hints.
- Exports/Defines: analyze_application, _get_required_fields, _generate_rule_based_analysis

## ai-services/app/modules/document_processing

### __init__.py

- Path: `ai-services/app/modules/document_processing/__init__.py`
- Summary: Document Processing Module Purpose: Document processing and analysis services

### classification_service.py

- Path: `ai-services/app/modules/document_processing/classification_service.py`
- Summary: Document Classification Service Purpose: Clean rule-based agricultural document classifier with standardized output
- Exports/Defines: DocumentClassificationService, __init__

### document_processing_router.py

- Path: `ai-services/app/modules/document_processing/document_processing_router.py`
- Summary: Document Processing Router Purpose: FastAPI router for document processing functionality
- Exports/Defines: process_document, process_document_from_metadata

### document_processing_service.py

- Path: `ai-services/app/modules/document_processing/document_processing_service.py`
- Summary: Document Processing Service Purpose: Clean orchestration layer over rebuilt schema, classifier, extraction service, and processor
- Exports/Defines: DocumentProcessingService, __init__, process_document, process_batch, classify_document

### extraction_router.py

- Path: `ai-services/app/modules/document_processing/extraction_router.py`
- Summary: Document Extraction Router Purpose: Lightweight internal/testing router for direct extraction operations
- Exports/Defines: extract_document, auto_classify_and_extract

### extraction_service.py

- Path: `ai-services/app/modules/document_processing/extraction_service.py`
- Summary: Document Extraction Service Purpose: Main handler-dispatch service for document extraction
- Exports/Defines: DocumentExtractionService, __init__, _initialize_handlers, _get_handler, _import_handler

### field_filter.py

- Path: `ai-services/app/modules/document_processing/field_filter.py`
- Summary: Field Filter for Noise Reduction Purpose: Filter out low-quality and noisy extracted fields
- Exports/Defines: FieldFilter, __init__, filter_extracted_fields

### generic_extractor.py

- Path: `ai-services/app/modules/document_processing/generic_extractor.py`
- Summary: Generic Field Extractor Purpose: Extract common agricultural document fields using label-aware and boundary-aware parsing Works as a shared extractor for common fields across all document types
- Exports/Defines: GenericFieldExtractor, __init__, extract_fields

### layout_analyzer.py

- Path: `ai-services/app/modules/document_processing/layout_analyzer.py`
- Summary: Layout Analyzer for Document Generalization Purpose: Extract semantic structure from diverse document layouts without rigid field boundaries
- Exports/Defines: LayoutType, SemanticBlock, LayoutAnalyzer, __init__

### predictive_analytics.py

- Path: `ai-services/app/modules/document_processing/predictive_analytics.py`
- Summary: Predictive Analytics for Agricultural Documents Purpose: Advanced predictive insights and trend analysis
- Exports/Defines: PredictionType, Prediction, PredictiveAnalytics, __init__

### processors.py

- Path: `ai-services/app/modules/document_processing/processors.py`
- Summary: Document Processors - Production Workflow Engine Contains document processing logic and workflow management for agriculture document-processing pipeline
- Exports/Defines: DocumentProcessor, __init__, process_document_workflow

### reasoning_engine.py

- Path: `ai-services/app/modules/document_processing/reasoning_engine.py`
- Summary: Reasoning Engine for Enhanced Decision Support Purpose: Advanced reasoning and decision support for agricultural documents
- Exports/Defines: ReasoningType, ReasoningInsight, ReasoningEngine, __init__

### semantic_extractor.py

- Path: `ai-services/app/modules/document_processing/semantic_extractor.py`
- Summary: Semantic Extractor for Enhanced Document Intelligence Purpose: Advanced extraction using semantic understanding and context awareness
- Exports/Defines: SemanticField, SemanticExtractor, __init__, extract_semantic_fields

### service_schema.py

- Path: `ai-services/app/modules/document_processing/service_schema.py`
- Summary: No top-level summary comment found.
- Exports/Defines: DocumentProcessingRequest, ExtractedFieldData, RiskFlag, DecisionSupport, ProcessedDocumentData, DocumentProcessingResult

### utils.py

- Path: `ai-services/app/modules/document_processing/utils.py`
- Summary: Document Processing Utilities Clean shared helper module for normalization, boundary-aware extraction, validation, and field normalization in the document-processing pipeline.
- Exports/Defines: normalize_ocr_text, is_missing_value

## ai-services/app/modules/document_processing/handlers

### __init__.py

- Path: `ai-services/app/modules/document_processing/handlers/__init__.py`
- Summary: No top-level summary comment found.

### base_handler.py

- Path: `ai-services/app/modules/document_processing/handlers/base_handler.py`
- Summary: Base Document Handler Purpose: Abstract base class for all document type handlers in the rebuilt extraction pipeline
- Exports/Defines: for, BaseHandler, __init__, get_document_type, extract_fields, build_field

### farmer_record_handler.py

- Path: `ai-services/app/modules/document_processing/handlers/farmer_record_handler.py`
- Summary: Farmer Record Handler Purpose: Extract fields from farmer registration and profile documents
- Exports/Defines: FarmerRecordHandler, __init__, get_document_type, extract_fields

### grievance_handler.py

- Path: `ai-services/app/modules/document_processing/handlers/grievance_handler.py`
- Summary: Grievance Handler Purpose: Extract fields from grievance letters and complaints
- Exports/Defines: GrievanceHandler, __init__, get_document_type, extract_fields

### insurance_claim_handler.py

- Path: `ai-services/app/modules/document_processing/handlers/insurance_claim_handler.py`
- Summary: No top-level summary comment found.
- Exports/Defines: InsuranceClaimHandler, __init__, get_document_type, extract_fields

### scheme_application_handler.py

- Path: `ai-services/app/modules/document_processing/handlers/scheme_application_handler.py`
- Summary: Scheme Application Handler Purpose: Extract fields from scheme application documents
- Exports/Defines: SchemeApplicationHandler, __init__, get_document_type, extract_fields

### subsidy_claim_handler.py

- Path: `ai-services/app/modules/document_processing/handlers/subsidy_claim_handler.py`
- Summary: No top-level summary comment found.
- Exports/Defines: SubsidyClaimHandler, __init__, get_document_type, extract_fields, _extract_farmer_name

### supporting_document_handler.py

- Path: `ai-services/app/modules/document_processing/handlers/supporting_document_handler.py`
- Summary: No top-level summary comment found.
- Exports/Defines: SupportingDocumentHandler, __init__, get_document_type, extract_fields

## ai-services/app/modules/document_processing/schema

### __init__.py

- Path: `ai-services/app/modules/document_processing/schema/__init__.py`
- Summary: Document Processing Schemas Purpose: Schema definitions for document processing

### document_classification.py

- Path: `ai-services/app/modules/document_processing/schema/document_classification.py`
- Summary: Document Classification Schemas Purpose: Pydantic models for document classification
- Exports/Defines: DocumentType, ClassificationReasoning, DocumentClassificationRequest, DocumentClassificationResponse

### extraction.py

- Path: `ai-services/app/modules/document_processing/schema/extraction.py`
- Summary: Document Extraction Schemas Purpose: Pydantic models for document extraction results
- Exports/Defines: FieldConfidence, ExtractedField, ExtractionResult, DocumentExtractionRequest, DocumentExtractionResponse, BatchExtractionRequest

## ai-services/app/modules/intelligence

### intelligence_service.py

- Path: `ai-services/app/modules/intelligence/intelligence_service.py`
- Summary: Intelligence Layer for Agricultural Document Processing Built on top of existing extraction output
- Exports/Defines: IntelligenceService, generate_document_summary, generate_case_insight

## ai-services/app/schemas

### common.py

- Path: `ai-services/app/schemas/common.py`
- Summary: Common Schemas Purpose: Shared Pydantic models used across AI services
- Exports/Defines: BaseResponse, ErrorResponse, HealthResponse, ProcessingRequest, ProcessingResult, FileProcessingRequest

## backend/src

### app.ts

- Path: `backend/src/app.ts`
- Summary: Express App Configuration Purpose: Configure Express middleware and routes

### server.ts

- Path: `backend/src/server.ts`
- Summary: Server Entry Point Purpose: Initialize and start the Express server

## backend/src/config

### config.ts

- Path: `backend/src/config/config.ts`
- Summary: Application Configuration Purpose: Centralized configuration management
- Exports/Defines: config

### database.ts

- Path: `backend/src/config/database.ts`
- Summary: Database Configuration and Connection Purpose: Centralized PostgreSQL/Supabase database connection management
- Exports/Defines: DatabaseConnection

### prisma.service.ts

- Path: `backend/src/config/prisma.service.ts`
- Summary: Prisma Service Purpose: Injectable Prisma client service for NestJS using the singleton pattern
- Exports/Defines: PrismaService

### prisma.ts

- Path: `backend/src/config/prisma.ts`
- Summary: Prisma Client Configuration Purpose: Singleton-safe Prisma client setup for the application
- Exports/Defines: disconnectPrisma, checkPrismaHealth

### supabase.ts

- Path: `backend/src/config/supabase.ts`
- Summary: No top-level summary comment found.
- Exports/Defines: supabase

## backend/src/middlewares

### asyncHandler.ts

- Path: `backend/src/middlewares/asyncHandler.ts`
- Summary: Async Handler Middleware Purpose: Wrapper to handle async route errors without try-catch
- Exports/Defines: asyncHandler

### errorHandler.ts

- Path: `backend/src/middlewares/errorHandler.ts`
- Summary: Error Handler Middleware Purpose: Centralized error handling for the application
- Exports/Defines: errorHandler, createError

### requestValidator.ts

- Path: `backend/src/middlewares/requestValidator.ts`
- Summary: Request Validator Middleware Purpose: Validate incoming request data using Joi schemas
- Exports/Defines: validateRequest

### upload.ts

- Path: `backend/src/middlewares/upload.ts`
- Summary: No top-level summary comment found.
- Exports/Defines: upload

## backend/src/modules/ai-orchestrator

### ai-orchestrator.controller.ts

- Path: `backend/src/modules/ai-orchestrator/ai-orchestrator.controller.ts`
- Summary: AI Orchestrator Controller Purpose: Handle AI orchestration-related HTTP requests
- Exports/Defines: aiOrchestratorController, AIOrchestratorController

### ai-orchestrator.repository.ts

- Path: `backend/src/modules/ai-orchestrator/ai-orchestrator.repository.ts`
- Summary: AI Orchestrator Repository Purpose: Database interaction layer for AI orchestration management
- Exports/Defines: AIOrchestratorRepository

### ai-orchestrator.routes.ts

- Path: `backend/src/modules/ai-orchestrator/ai-orchestrator.routes.ts`
- Summary: AI Orchestrator Routes Purpose: Define Express routes for AI orchestration management

### ai-orchestrator.service.ts

- Path: `backend/src/modules/ai-orchestrator/ai-orchestrator.service.ts`
- Summary: AI Orchestrator Service Purpose: Business logic for AI orchestration management
- Exports/Defines: AIOrchestratorService

### ai-orchestrator.types.ts

- Path: `backend/src/modules/ai-orchestrator/ai-orchestrator.types.ts`
- Summary: AI Orchestrator Types Purpose: TypeScript interfaces and types for AI orchestration management

### index.ts

- Path: `backend/src/modules/ai-orchestrator/index.ts`
- Summary: AI Orchestrator Module Index Purpose: Export all AI orchestration-related components

## backend/src/modules/applications

### applications.controller.ts

- Path: `backend/src/modules/applications/applications.controller.ts`
- Summary: Applications Controller Purpose: Handle application-related HTTP requests
- Exports/Defines: ApplicationsController

### applications.repository.ts

- Path: `backend/src/modules/applications/applications.repository.ts`
- Summary: Applications Repository Purpose: Database interaction layer for application management using Prisma ORM
- Exports/Defines: ApplicationsRepository

### applications.routes.ts

- Path: `backend/src/modules/applications/applications.routes.ts`
- Summary: Applications Routes Purpose: Define Express routes for application management

### applications.service.ts

- Path: `backend/src/modules/applications/applications.service.ts`
- Summary: Applications Service Purpose: Business logic for application management
- Exports/Defines: ApplicationsService

### applications.types.ts

- Path: `backend/src/modules/applications/applications.types.ts`
- Summary: Applications Types Purpose: TypeScript interfaces and types for application management

### index.ts

- Path: `backend/src/modules/applications/index.ts`
- Summary: Applications Module Index Purpose: Export all application-related components

## backend/src/modules/cases

### cases.service.ts

- Path: `backend/src/modules/cases/cases.service.ts`
- Summary: No top-level summary comment found.
- Exports/Defines: CaseService

## backend/src/routes

### applicationsRoutes.ts

- Path: `backend/src/routes/applicationsRoutes.ts`
- Summary: Applications Routes Purpose: Define application-related API routes

### dashboardRoutes.ts

- Path: `backend/src/routes/dashboardRoutes.ts`
- Summary: Dashboard Routes Purpose: Define Express routes for dashboard data

## backend/src/types

### index.ts

- Path: `backend/src/types/index.ts`
- Summary: Global Type Definitions Purpose: Shared TypeScript interfaces and types used across the backend

## backend/src/utils

### logger.ts

- Path: `backend/src/utils/logger.ts`
- Summary: Logger Utility Purpose: Centralized logging configuration

## docs

### PROJECT_BRAIN.md

- Path: `docs/PROJECT_BRAIN.md`
- Summary: No top-level summary comment found.

### repo-map.md

- Path: `docs/repo-map.md`
- Summary: No top-level summary comment found.

## frontend/src

### main.tsx

- Path: `frontend/src/main.tsx`
- Summary: Main application entry point Purpose: Initialize React app and render root component

### vite-env.d.ts

- Path: `frontend/src/vite-env.d.ts`
- Summary: / <reference types="vite/client" />

## frontend/src/app

### App.tsx

- Path: `frontend/src/app/App.tsx`
- Summary: Root App Component Purpose: Main application wrapper with routing setup

## frontend/src/components/application

### ApplicationActions.tsx

- Path: `frontend/src/components/application/ApplicationActions.tsx`
- Summary: Application Actions Component Purpose: Handles application action buttons and loading states
- Exports/Defines: ApplicationActions

### ApplicationHeader.tsx

- Path: `frontend/src/components/application/ApplicationHeader.tsx`
- Summary: Application Header Component Purpose: Displays application header with navigation and status
- Exports/Defines: ApplicationHeader

### ApplicationSections.tsx

- Path: `frontend/src/components/application/ApplicationSections.tsx`
- Summary: Application Sections Component Purpose: Displays all application content sections with AI-enhanced data
- Exports/Defines: ApplicationSections

## frontend/src/components/Navigation

### index.ts

- Path: `frontend/src/components/Navigation/index.ts`
- Summary: No top-level summary comment found.

### MobileNavigation.tsx

- Path: `frontend/src/components/Navigation/MobileNavigation.tsx`
- Summary: No top-level summary comment found.
- Exports/Defines: MobileNavigation

### Sidebar.tsx

- Path: `frontend/src/components/Navigation/Sidebar.tsx`
- Summary: No top-level summary comment found.
- Exports/Defines: Sidebar

## frontend/src/components/ui

### AnimatedPageWrapper.tsx

- Path: `frontend/src/components/ui/AnimatedPageWrapper.tsx`
- Summary: No top-level summary comment found.
- Exports/Defines: AnimatedPageWrapper, AnimatedSection

### Button.tsx

- Path: `frontend/src/components/ui/Button.tsx`
- Summary: No top-level summary comment found.

### Card.tsx

- Path: `frontend/src/components/ui/Card.tsx`
- Summary: No top-level summary comment found.

### DataTable.tsx

- Path: `frontend/src/components/ui/DataTable.tsx`
- Summary: No top-level summary comment found.
- Exports/Defines: DataTable

### EmptyState.tsx

- Path: `frontend/src/components/ui/EmptyState.tsx`
- Summary: No top-level summary comment found.
- Exports/Defines: EmptyState

### ErrorBoundary.tsx

- Path: `frontend/src/components/ui/ErrorBoundary.tsx`
- Summary: No top-level summary comment found.
- Exports/Defines: ErrorBoundary

### index.ts

- Path: `frontend/src/components/ui/index.ts`
- Summary: No top-level summary comment found.

### LoadingState.tsx

- Path: `frontend/src/components/ui/LoadingState.tsx`
- Summary: No top-level summary comment found.
- Exports/Defines: LoadingState

### PageHeader.tsx

- Path: `frontend/src/components/ui/PageHeader.tsx`
- Summary: No top-level summary comment found.
- Exports/Defines: PageHeader

### SectionCard.tsx

- Path: `frontend/src/components/ui/SectionCard.tsx`
- Summary: No top-level summary comment found.
- Exports/Defines: SectionCard

### StatCard.tsx

- Path: `frontend/src/components/ui/StatCard.tsx`
- Summary: No top-level summary comment found.
- Exports/Defines: StatCard

### StatusBadge.tsx

- Path: `frontend/src/components/ui/StatusBadge.tsx`
- Summary: No top-level summary comment found.

### Toaster.tsx

- Path: `frontend/src/components/ui/Toaster.tsx`
- Summary: No top-level summary comment found.
- Exports/Defines: Toaster

## frontend/src/constants

### index.ts

- Path: `frontend/src/constants/index.ts`
- Summary: Application Constants Purpose: Centralized constants used across the application
- Exports/Defines: API_ENDPOINTS, ROUTES, STATUS_COLORS, ROLES

## frontend/src/features/applications

### index.ts

- Path: `frontend/src/features/applications/index.ts`
- Summary: Applications Feature Module Index Purpose: Export all application-related components and utilities

## frontend/src/features/applications/components

### FileUpload.tsx

- Path: `frontend/src/features/applications/components/FileUpload.tsx`
- Summary: No top-level summary comment found.
- Exports/Defines: FileUpload

## frontend/src/features/applications/pages

### UploadPage.tsx

- Path: `frontend/src/features/applications/pages/UploadPage.tsx`
- Summary: No top-level summary comment found.
- Exports/Defines: UploadPage

## frontend/src/layouts

### AuthLayout.tsx

- Path: `frontend/src/layouts/AuthLayout.tsx`
- Summary: Auth Layout Component Purpose: Layout wrapper for authentication pages (login, register, etc.)
- Exports/Defines: AuthLayout

### DashboardLayout.tsx

- Path: `frontend/src/layouts/DashboardLayout.tsx`
- Summary: Dashboard Layout Component Purpose: Main application layout with navigation and sidebar for authenticated users - Agricultural Admin Theme
- Exports/Defines: DashboardLayout

## frontend/src/lib

### utils.ts

- Path: `frontend/src/lib/utils.ts`
- Summary: No top-level summary comment found.
- Exports/Defines: cn

## frontend/src/pages

### ApplicationDetailPage.tsx

- Path: `frontend/src/pages/ApplicationDetailPage.tsx`
- Summary: Application Detail Page Purpose: Main orchestrator for application detail view
- Exports/Defines: ApplicationDetailPage

### ApplicationsPage.tsx

- Path: `frontend/src/pages/ApplicationsPage.tsx`
- Summary: Applications Page Component Purpose: Page for managing and viewing applications
- Exports/Defines: ApplicationsPage

### DashboardPage.tsx

- Path: `frontend/src/pages/DashboardPage.tsx`
- Summary: Dashboard Page Component Purpose: Simple summary page for dashboard route
- Exports/Defines: DashboardPage

### FarmerDetailPage.tsx

- Path: `frontend/src/pages/FarmerDetailPage.tsx`
- Summary: No top-level summary comment found.
- Exports/Defines: FarmerDetailPage

### FarmerRecordsPage.tsx

- Path: `frontend/src/pages/FarmerRecordsPage.tsx`
- Summary: No top-level summary comment found.
- Exports/Defines: FarmerRecordsPage

### NotFoundPage.tsx

- Path: `frontend/src/pages/NotFoundPage.tsx`
- Summary: 404 Not Found Page Component Purpose: Fallback page for undefined routes
- Exports/Defines: NotFoundPage

### VerificationPage.tsx

- Path: `frontend/src/pages/VerificationPage.tsx`
- Summary: Verification Queue Page Purpose: Placeholder page for verification queue management
- Exports/Defines: VerificationPage

## frontend/src/services

### api.ts

- Path: `frontend/src/services/api.ts`
- Summary: API Client Service Purpose: Centralized HTTP client for backend communication
- Exports/Defines: apiClient, ApiClient

### applicationsService.ts

- Path: `frontend/src/services/applicationsService.ts`
- Summary: Applications API Service Purpose: Service layer for application-related API calls

### dashboardService.ts

- Path: `frontend/src/services/dashboardService.ts`
- Summary: Dashboard API Service Purpose: Service layer for dashboard-related API calls
- Exports/Defines: dashboardService, DashboardService

### farmerService.ts

- Path: `frontend/src/services/farmerService.ts`
- Summary: No top-level summary comment found.
- Exports/Defines: farmerService

## frontend/src/types

### index.ts

- Path: `frontend/src/types/index.ts`
- Summary: Global Type Definitions Purpose: Shared TypeScript interfaces and types used across the application

## frontend/src/utils

### applicationDetailMapper.ts

- Path: `frontend/src/utils/applicationDetailMapper.ts`
- Summary: Application Detail Mapper Purpose: Normalizes backend response shape to frontend expectations This mapper serves as the frontend adapter layer: - canonical schema is PREFERRED (first priority) - structured_data is FALLBACK (second priority) - returned extractedFields is a UI-friendly adapter shape - No legacy fallback paths - clean data flow from backend contract
- Exports/Defines: mapApplicationToUI

## scripts

### generate-repo-map.js

- Path: `scripts/generate-repo-map.js`
- Summary: No top-level summary comment found.

### project-brain.js

- Path: `scripts/project-brain.js`
- Summary: No top-level summary comment found.
