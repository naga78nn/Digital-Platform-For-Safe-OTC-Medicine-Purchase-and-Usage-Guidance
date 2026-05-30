-- Add specialization column to doctors table
ALTER TABLE doctors ADD COLUMN specialization VARCHAR(100) DEFAULT 'General Medicine';