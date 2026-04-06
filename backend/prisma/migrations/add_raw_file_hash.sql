-- Add rawFileHash field for exact file duplicate detection
-- This field stores the SHA256 hash of the uploaded file bytes
-- Separate from normalizedContentHash which stores content fingerprint

ALTER TABLE applications 
ADD COLUMN raw_file_hash VARCHAR(64);

-- Create index for exact file hash lookups
CREATE INDEX idx_applications_raw_file_hash ON applications(raw_file_hash);

-- Update composite duplicate check index to include both hash types
DROP INDEX IF EXISTS idx_applications_duplicate_check;
CREATE INDEX idx_applications_duplicate_check ON applications(normalized_content_hash, raw_file_hash, farmer_id, type, status);
