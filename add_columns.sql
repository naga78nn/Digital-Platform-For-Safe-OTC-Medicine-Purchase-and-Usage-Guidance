-- Add is_prescribed column to appointments table
ALTER TABLE appointments ADD COLUMN is_prescribed TINYINT(1) DEFAULT 0;

-- Add prescribed_at column to track when prescription was created
ALTER TABLE appointments ADD COLUMN prescribed_at TIMESTAMP NULL;