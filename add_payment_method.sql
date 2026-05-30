-- Add payment_method column to bills table
ALTER TABLE bills ADD COLUMN payment_method VARCHAR(20) DEFAULT 'Cash';