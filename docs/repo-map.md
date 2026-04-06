# Repo Map

> Generated automatically on 2026-04-06T04:14:59.335Z
> Do not edit manually - run `npm run repo:map`

## Project Structure

```text
frontend/
  ├── src
  │   ├── app
  │   │   └── App.tsx
  │   ├── components
  │   │   ├── application
  │   │   │   ├── ApplicationActions.tsx
  │   │   │   ├── ApplicationHeader.tsx
  │   │   │   └── ApplicationSections.tsx
  │   │   ├── common
  │   │   ├── Navigation
  │   │   │   ├── index.ts
  │   │   │   ├── MobileNavigation.tsx
  │   │   │   └── Sidebar.tsx
  │   │   └── ui
  │   │       ├── AnimatedPageWrapper.tsx
  │   │       ├── Button.tsx
  │   │       ├── Card.tsx
  │   │       ├── DataTable.tsx
  │   │       ├── EmptyState.tsx
  │   │       ├── ErrorBoundary.tsx
  │   │       ├── index.ts
  │   │       ├── LoadingState.tsx
  │   │       ├── PageHeader.tsx
  │   │       ├── SectionCard.tsx
  │   │       ├── StatCard.tsx
  │   │       ├── StatusBadge.tsx
  │   │       └── Toaster.tsx
  │   ├── constants
  │   │   └── index.ts
  │   ├── features
  │   │   └── applications
  │   │       ├── components
  │   │       │   └── FileUpload.tsx
  │   │       ├── pages
  │   │       │   └── UploadPage.tsx
  │   │       └── index.ts
  │   ├── layouts
  │   │   ├── AuthLayout.tsx
  │   │   └── DashboardLayout.tsx
  │   ├── lib
  │   │   └── utils.ts
  │   ├── pages
  │   │   ├── ApplicationDetailPage.tsx
  │   │   ├── ApplicationsPage.tsx
  │   │   ├── DashboardPage.tsx
  │   │   ├── FarmerDetailPage.tsx
  │   │   ├── FarmerRecordsPage.tsx
  │   │   ├── NotFoundPage.tsx
  │   │   └── VerificationPage.tsx
  │   ├── services
  │   │   ├── api.ts
  │   │   ├── applicationsService.ts
  │   │   ├── dashboardService.ts
  │   │   └── farmerService.ts
  │   ├── types
  │   │   └── index.ts
  │   ├── utils
  │   │   └── applicationDetailMapper.ts
  │   ├── index.css
  │   ├── main.tsx
  │   └── vite-env.d.ts
  ├── .env
  ├── index.html
  ├── package-lock.json
  ├── package.json
  ├── postcss.config.js
  ├── README.md
  ├── ROUTE_FIX_TEST.md
  ├── tailwind.config.js
  ├── tsconfig.json
  ├── tsconfig.node.json
  ├── vercel.json
  └── vite.config.ts
backend/
  ├── generated
  │   └── prisma
  │       ├── runtime
  │       │   ├── edge-esm.js
  │       │   ├── edge.js
  │       │   ├── index-browser.d.ts
  │       │   ├── index-browser.js
  │       │   ├── library.d.ts
  │       │   ├── library.js
  │       │   ├── react-native.js
  │       │   ├── wasm-compiler-edge.js
  │       │   └── wasm-engine-edge.js
  │       ├── client.d.ts
  │       ├── client.js
  │       ├── default.d.ts
  │       ├── default.js
  │       ├── edge.d.ts
  │       ├── edge.js
  │       ├── index-browser.js
  │       ├── index.d.ts
  │       ├── index.js
  │       ├── package.json
  │       ├── query_engine_bg.js
  │       ├── query_engine_bg.wasm
  │       ├── query_engine-windows.dll.node
  │       ├── query_engine-windows.dll.node.tmp17424
  │       ├── schema.prisma
  │       ├── wasm-edge-light-loader.mjs
  │       ├── wasm-worker-loader.mjs
  │       ├── wasm.d.ts
  │       └── wasm.js
  ├── logs
  │   ├── combined.log
  │   └── error.log
  ├── prisma
  │   ├── migrations
  │   │   ├── 20260402050019_init
  │   │   │   └── migration.sql
  │   │   ├── 20260402132927_add_case_grouping
  │   │   │   └── migration.sql
  │   │   └── migration_lock.toml
  │   └── schema.prisma
  ├── scripts
  │   ├── test_workflow_validation.js
  │   └── test_workflow_validation.ts
  ├── src
  │   ├── config
  │   │   ├── config.ts
  │   │   ├── database.ts
  │   │   ├── prisma.service.ts
  │   │   ├── prisma.ts
  │   │   └── supabase.ts
  │   ├── controllers
  │   ├── middlewares
  │   │   ├── asyncHandler.ts
  │   │   ├── errorHandler.ts
  │   │   ├── requestValidator.ts
  │   │   └── upload.ts
  │   ├── modules
  │   │   ├── ai-orchestrator
  │   │   │   ├── ai-orchestrator.controller.ts
  │   │   │   ├── ai-orchestrator.repository.ts
  │   │   │   ├── ai-orchestrator.routes.ts
  │   │   │   ├── ai-orchestrator.service.ts
  │   │   │   ├── ai-orchestrator.types.ts
  │   │   │   └── index.ts
  │   │   ├── applications
  │   │   │   ├── applications.controller.ts
  │   │   │   ├── applications.repository.ts
  │   │   │   ├── applications.routes.ts
  │   │   │   ├── applications.service.ts
  │   │   │   ├── applications.types.ts
  │   │   │   └── index.ts
  │   │   └── cases
  │   │       └── cases.service.ts
  │   ├── repositories
  │   ├── routes
  │   │   ├── applicationsRoutes.ts
  │   │   └── dashboardRoutes.ts
  │   ├── services
  │   ├── types
  │   │   └── index.ts
  │   ├── utils
  │   │   └── logger.ts
  │   ├── app.ts
  │   └── server.ts
  ├── .env
  ├── .gitignore
  ├── AI_MAPPING_FIX_SUMMARY.md
  ├── debug-extraction-persistence.sql
  ├── eng.traineddata
  ├── package-lock.json
  ├── package.json
  ├── README.md
  ├── test_duplicate_block.js
  ├── test_duplicate_blocking.py
  ├── test_duplicate_error_message.js
  ├── test-ai-mapping.js
  ├── test-classification-fix.js
  ├── test-server.js
  └── tsconfig.json
ai-services/
  ├── app
  │   ├── api
  │   │   ├── application_priority.py
  │   │   └── fraud_detection.py
  │   ├── core
  │   │   ├── config.py
  │   │   └── llm_client.py
  │   ├── models
  │   ├── modules
  │   │   ├── ai_assist
  │   │   │   ├── llm_assist_service.py
  │   │   │   └── llm_refinement_service.py
  │   │   ├── document_processing
  │   │   │   ├── handlers
  │   │   │   │   ├── __init__.py
  │   │   │   │   ├── base_handler.py
  │   │   │   │   ├── farmer_record_handler.py
  │   │   │   │   ├── grievance_handler.py
  │   │   │   │   ├── insurance_claim_handler.py
  │   │   │   │   ├── scheme_application_handler.py
  │   │   │   │   ├── subsidy_claim_handler.py
  │   │   │   │   └── supporting_document_handler.py
  │   │   │   ├── schema
  │   │   │   │   ├── __init__.py
  │   │   │   │   ├── document_classification.py
  │   │   │   │   └── extraction.py
  │   │   │   ├── __init__.py
  │   │   │   ├── candidate_extraction_engine.py
  │   │   │   ├── classification_service.py
  │   │   │   ├── document_processing_router.py
  │   │   │   ├── document_processing_service.py
  │   │   │   ├── document_schemas.py
  │   │   │   ├── extraction_integration_helper.py
  │   │   │   ├── extraction_router.py
  │   │   │   ├── extraction_service.py
  │   │   │   ├── field_filter.py
  │   │   │   ├── generic_extractor.py
  │   │   │   ├── layout_analyzer.py
  │   │   │   ├── ml_priority.py
  │   │   │   ├── money_extraction_validator.py
  │   │   │   ├── predictive_analytics.py
  │   │   │   ├── priority_model.pkl
  │   │   │   ├── processors.py
  │   │   │   ├── reasoning_engine.py
  │   │   │   ├── semantic_extractor.py
  │   │   │   ├── service_schema.py
  │   │   │   ├── unified_extraction_orchestrator.py
  │   │   │   ├── utils.py
  │   │   │   └── workflow_service.py
  │   │   └── intelligence
  │   │       └── intelligence_service.py
  │   ├── schemas
  │   │   └── common.py
  │   ├── services
  │   ├── utils
  │   └── main.py
  ├── data
  │   └── training
  │       └── priority_training_data.csv
  ├── docs
  │   └── document-processing-code-context.md
  ├── ml
  │   ├── feature_extractor.py
  │   ├── ml_service.py
  │   ├── model.pkl
  │   └── train_model.py
  ├── scripts
  │   ├── debug_classification.py
  │   ├── generate-code-context.py
  │   ├── test_document_pipeline.py
  │   ├── test_farmer_integration.py
  │   ├── test_intelligence_integration.py
  │   ├── test_intelligence_layer.py
  │   ├── test_intelligence_pipeline.py
  │   └── train_priority_model.py
  ├── debug_amount.py
  ├── debug_structure.py
  ├── README.md
  ├── requirements.txt
  ├── runtime.txt
  ├── test_ai_fields.py
  └── test_production_intelligence.py
shared/
  ├── constants
  │   ├── common.ts
  │   └── index.ts
  ├── types
  │   ├── ai.ts
  │   ├── classification-types.ts
  │   ├── common.ts
  │   ├── document-types.ts
  │   ├── index.ts
  │   └── ocr-types.ts
  └── README.md
docs/
  ├── PROJECT_BRAIN.md
  └── repo-map.md
```