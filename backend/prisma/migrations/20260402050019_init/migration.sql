-- CreateEnum
CREATE TYPE "ApplicationStatus" AS ENUM ('UPLOADED', 'PROCESSING', 'PROCESSED', 'NEEDS_REVIEW', 'PENDING', 'UNDER_REVIEW', 'APPROVED', 'REJECTED', 'REQUIRES_ACTION');

-- CreateEnum
CREATE TYPE "DocumentType" AS ENUM ('ID_PROOF', 'ADDRESS_PROOF', 'LAND_RECORD', 'INCOME_CERTIFICATE', 'BANK_STATEMENT', 'CROP_INSURANCE', 'OTHER');

-- CreateEnum
CREATE TYPE "FraudCaseStatus" AS ENUM ('PENDING_REVIEW', 'UNDER_INVESTIGATION', 'CONFIRMED_FRAUD', 'FALSE_POSITIVE', 'RESOLVED');

-- CreateEnum
CREATE TYPE "FraudRiskLevel" AS ENUM ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL');

-- CreateTable
CREATE TABLE "farmers" (
    "id" UUID NOT NULL DEFAULT gen_random_uuid(),
    "name" VARCHAR(255),
    "aadhaar_number" VARCHAR(20),
    "mobile_number" VARCHAR(20),
    "address" TEXT,
    "village" VARCHAR(255),
    "district" VARCHAR(255),
    "state" VARCHAR(255),
    "created_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "farmers_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "applications" (
    "id" UUID NOT NULL DEFAULT gen_random_uuid(),
    "applicant_id" VARCHAR(255) NOT NULL,
    "scheme_id" VARCHAR(255) NOT NULL,
    "type" VARCHAR(100) NOT NULL,
    "status" "ApplicationStatus" NOT NULL DEFAULT 'UPLOADED',
    "priority_score" INTEGER,
    "reviewer_id" VARCHAR(255),
    "review_date" TIMESTAMPTZ(6),
    "decision_date" TIMESTAMPTZ(6),
    "file_name" VARCHAR(500),
    "file_url" TEXT,
    "file_size" BIGINT,
    "file_type" VARCHAR(100),
    "personal_info" JSONB NOT NULL,
    "farm_info" JSONB,
    "documents" JSONB NOT NULL,
    "extracted_data" JSONB,
    "ai_summary" TEXT,
    "fraud_risk_score" DOUBLE PRECISION,
    "fraud_flags" JSONB,
    "verification_recommendation" TEXT,
    "ai_processing_status" VARCHAR(50),
    "ocr_processed_at" TIMESTAMPTZ(6),
    "ai_processed_at" TIMESTAMPTZ(6),
    "confidence" DOUBLE PRECISION,
    "notes" TEXT,
    "submission_date" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "created_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "farmer_id" UUID,

    CONSTRAINT "applications_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "documents" (
    "id" UUID NOT NULL DEFAULT gen_random_uuid(),
    "application_id" UUID NOT NULL,
    "type" "DocumentType" NOT NULL,
    "file_name" VARCHAR(500) NOT NULL,
    "file_url" TEXT NOT NULL,
    "file_size" BIGINT,
    "mime_type" VARCHAR(100),
    "confidence" DOUBLE PRECISION,
    "extracted_data" JSONB,
    "is_verified" BOOLEAN NOT NULL DEFAULT false,
    "verified_at" TIMESTAMPTZ(6),
    "verified_by" VARCHAR(255),
    "created_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "documents_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "fraud_cases" (
    "id" UUID NOT NULL DEFAULT gen_random_uuid(),
    "application_id" UUID NOT NULL,
    "riskLevel" "FraudRiskLevel" NOT NULL,
    "score" DOUBLE PRECISION NOT NULL,
    "indicators" JSONB NOT NULL,
    "status" "FraudCaseStatus" NOT NULL DEFAULT 'PENDING_REVIEW',
    "description" TEXT,
    "investigation_notes" JSONB,
    "assigned_to" VARCHAR(255),
    "resolved_at" TIMESTAMPTZ(6),
    "resolution" TEXT,
    "resolution_time" DOUBLE PRECISION,
    "created_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "fraud_cases_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "officers" (
    "id" UUID NOT NULL DEFAULT gen_random_uuid(),
    "first_name" VARCHAR(100) NOT NULL,
    "last_name" VARCHAR(100) NOT NULL,
    "email" VARCHAR(255) NOT NULL,
    "phone" VARCHAR(20),
    "badge_number" VARCHAR(50) NOT NULL,
    "department_id" UUID,
    "is_active" BOOLEAN NOT NULL DEFAULT true,
    "role" VARCHAR(50),
    "created_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "officers_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "departments" (
    "id" UUID NOT NULL DEFAULT gen_random_uuid(),
    "name" VARCHAR(100) NOT NULL,
    "code" VARCHAR(20) NOT NULL,
    "description" TEXT,
    "head_officer_id" UUID,
    "is_active" BOOLEAN NOT NULL DEFAULT true,
    "created_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "departments_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE UNIQUE INDEX "farmers_aadhaar_number_key" ON "farmers"("aadhaar_number");

-- CreateIndex
CREATE INDEX "idx_farmers_aadhaar_number" ON "farmers"("aadhaar_number");

-- CreateIndex
CREATE INDEX "idx_farmers_mobile_number" ON "farmers"("mobile_number");

-- CreateIndex
CREATE INDEX "idx_farmers_village" ON "farmers"("village");

-- CreateIndex
CREATE INDEX "idx_applications_applicant_id" ON "applications"("applicant_id");

-- CreateIndex
CREATE INDEX "idx_applications_scheme_id" ON "applications"("scheme_id");

-- CreateIndex
CREATE INDEX "idx_applications_status" ON "applications"("status");

-- CreateIndex
CREATE INDEX "idx_applications_submission_date" ON "applications"("submission_date");

-- CreateIndex
CREATE INDEX "idx_applications_priority_score" ON "applications"("priority_score");

-- CreateIndex
CREATE INDEX "idx_applications_reviewer_id" ON "applications"("reviewer_id");

-- CreateIndex
CREATE INDEX "idx_applications_farmer_id" ON "applications"("farmer_id");

-- CreateIndex
CREATE INDEX "idx_documents_application_id" ON "documents"("application_id");

-- CreateIndex
CREATE INDEX "idx_documents_type" ON "documents"("type");

-- CreateIndex
CREATE INDEX "idx_documents_is_verified" ON "documents"("is_verified");

-- CreateIndex
CREATE INDEX "idx_fraud_cases_application_id" ON "fraud_cases"("application_id");

-- CreateIndex
CREATE INDEX "idx_fraud_cases_risk_level" ON "fraud_cases"("riskLevel");

-- CreateIndex
CREATE INDEX "idx_fraud_cases_status" ON "fraud_cases"("status");

-- CreateIndex
CREATE UNIQUE INDEX "officers_email_key" ON "officers"("email");

-- CreateIndex
CREATE UNIQUE INDEX "officers_badge_number_key" ON "officers"("badge_number");

-- CreateIndex
CREATE INDEX "idx_officers_department_id" ON "officers"("department_id");

-- CreateIndex
CREATE INDEX "idx_officers_is_active" ON "officers"("is_active");

-- CreateIndex
CREATE UNIQUE INDEX "departments_code_key" ON "departments"("code");

-- CreateIndex
CREATE INDEX "idx_departments_head_officer_id" ON "departments"("head_officer_id");

-- CreateIndex
CREATE INDEX "idx_departments_is_active" ON "departments"("is_active");

-- AddForeignKey
ALTER TABLE "applications" ADD CONSTRAINT "applications_farmer_id_fkey" FOREIGN KEY ("farmer_id") REFERENCES "farmers"("id") ON DELETE SET NULL ON UPDATE CASCADE;
