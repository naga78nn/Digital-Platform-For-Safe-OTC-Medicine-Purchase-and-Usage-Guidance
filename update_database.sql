-- Add payment_status column to bills table
ALTER TABLE bills ADD COLUMN payment_status VARCHAR(20) DEFAULT 'Pending';

-- Add bill_id column to orders table
ALTER TABLE orders ADD COLUMN bill_id INT;

-- Add foreign key constraint
ALTER TABLE orders ADD FOREIGN KEY (bill_id) REFERENCES bills(bill_id);

-- Add is_prescribed column to appointments table
ALTER TABLE appointments ADD COLUMN is_prescribed TINYINT(1) DEFAULT 0;

-- Add prescribed_at column to track when prescription was created
ALTER TABLE appointments ADD COLUMN prescribed_at TIMESTAMP NULL;
-- Add price column to prescription_items table
ALTER TABLE prescription_items ADD COLUMN price DECIMAL(10,2) DEFAULT 0.00;