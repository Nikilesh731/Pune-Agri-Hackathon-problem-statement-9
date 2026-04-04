-- Test query to check extracted data persistence
-- Run this in Supabase SQL editor to debug the issue

-- 1. Check latest applications and their extracted data
SELECT 
    id,
    status,
    ai_processing_status,
    extracted_data,
    created_at,
    updated_at
FROM applications 
ORDER BY created_at DESC 
LIMIT 5;

-- 2. Check if documents table has extracted data that applications doesn't
SELECT 
    d.id as document_id,
    d.application_id,
    d.extracted_data as document_extracted_data,
    a.extracted_data as application_extracted_data,
    d.created_at
FROM documents d
LEFT JOIN applications a ON d.application_id = a.id
ORDER BY d.created_at DESC
LIMIT 5;

-- 3. Check applications that have AI processing completed but empty extracted data
SELECT 
    id,
    status,
    ai_processing_status,
    CASE 
        WHEN extracted_data IS NULL THEN 'NULL'
        WHEN extracted_data = '{}' THEN 'EMPTY_OBJECT'
        WHEN extracted_data = '[]' THEN 'EMPTY_ARRAY'
        ELSE 'HAS_DATA'
    END as extracted_data_status,
    extracted_data,
    ai_processed_at
FROM applications 
WHERE ai_processing_status = 'completed'
ORDER BY created_at DESC
LIMIT 5;
