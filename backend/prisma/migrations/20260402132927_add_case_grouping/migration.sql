-- AlterTable
ALTER TABLE "applications" ADD COLUMN     "case_id" UUID;

-- CreateTable
CREATE TABLE "cases" (
    "id" UUID NOT NULL DEFAULT gen_random_uuid(),
    "farmer_id" UUID,
    "case_type" VARCHAR(100) NOT NULL,
    "status" VARCHAR(50) NOT NULL DEFAULT 'open',
    "title" VARCHAR(500),
    "summary" TEXT,
    "created_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "cases_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE INDEX "idx_cases_farmer_id" ON "cases"("farmer_id");

-- CreateIndex
CREATE INDEX "idx_cases_case_type" ON "cases"("case_type");

-- CreateIndex
CREATE INDEX "idx_cases_status" ON "cases"("status");

-- CreateIndex
CREATE INDEX "idx_applications_case_id" ON "applications"("case_id");

-- AddForeignKey
ALTER TABLE "cases" ADD CONSTRAINT "cases_farmer_id_fkey" FOREIGN KEY ("farmer_id") REFERENCES "farmers"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "applications" ADD CONSTRAINT "applications_case_id_fkey" FOREIGN KEY ("case_id") REFERENCES "cases"("id") ON DELETE SET NULL ON UPDATE CASCADE;
