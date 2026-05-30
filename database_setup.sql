-- Medical Management System Database Setup
-- Run this file in MySQL to create all tables and sample data

CREATE DATABASE IF NOT EXISTS medican_management;
USE medican_management;

-- Drop existing tables if they exist
DROP TABLE IF EXISTS prescription_medicines;
DROP TABLE IF EXISTS prescription_items;
DROP TABLE IF EXISTS prescriptions;
DROP TABLE IF EXISTS bill_items;
DROP TABLE IF EXISTS bills;
DROP TABLE IF EXISTS medicine_orders;
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS appointments;
DROP TABLE IF EXISTS medicines;
DROP TABLE IF EXISTS patients;
DROP TABLE IF EXISTS doctors;
DROP TABLE IF EXISTS pharmacists;

-- Create all tables
CREATE TABLE patients (
    patient_id INT AUTO_INCREMENT PRIMARY KEY,
    patient_name VARCHAR(100) NOT NULL,
    mobile_number VARCHAR(15) NOT NULL,
    age INT NOT NULL,
    gender VARCHAR(10) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE doctors (
    doctor_id INT AUTO_INCREMENT PRIMARY KEY,
    doctor_name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    specialization VARCHAR(100),
    contact_number VARCHAR(15) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE pharmacists (
    pharmacist_id INT AUTO_INCREMENT PRIMARY KEY,
    pharmacist_name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    pharmacy_name VARCHAR(100) NOT NULL,
    contact_number VARCHAR(15) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE medicines (
    medicine_id INT AUTO_INCREMENT PRIMARY KEY,
    pharmacist_id INT NOT NULL,
    medicine_name VARCHAR(100) NOT NULL,
    used_for VARCHAR(100),
    dosage VARCHAR(100),
    side_effects TEXT,
    prescription_needed BOOLEAN DEFAULT TRUE,
    price DECIMAL(10,2),
    FOREIGN KEY (pharmacist_id) REFERENCES pharmacists(pharmacist_id)
);

CREATE TABLE appointments (
    appointment_id INT AUTO_INCREMENT PRIMARY KEY,
    patient_id INT NOT NULL,
    doctor_id INT NOT NULL,
    appointment_date DATE NOT NULL,
    status ENUM('Pending','Approved','Rejected','Completed') DEFAULT 'Pending',
    is_prescribed TINYINT(1) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_id) REFERENCES patients(patient_id),
    FOREIGN KEY (doctor_id) REFERENCES doctors(doctor_id)
);

CREATE TABLE prescriptions (
    prescription_id INT AUTO_INCREMENT PRIMARY KEY,
    appointment_id INT NOT NULL UNIQUE,
    patient_id INT NOT NULL,
    doctor_id INT NOT NULL,
    diagnosis VARCHAR(255),
    notes VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (appointment_id) REFERENCES appointments(appointment_id),
    FOREIGN KEY (patient_id) REFERENCES patients(patient_id),
    FOREIGN KEY (doctor_id) REFERENCES doctors(doctor_id)
);

CREATE TABLE prescription_items (
    item_id INT AUTO_INCREMENT PRIMARY KEY,
    prescription_id INT NOT NULL,
    medicine_name VARCHAR(100) NOT NULL,
    dosage VARCHAR(50) NOT NULL,
    frequency VARCHAR(50) NOT NULL,
    duration_days INT NOT NULL,
    quantity INT NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    FOREIGN KEY (prescription_id) REFERENCES prescriptions(prescription_id)
);

CREATE TABLE orders (
    order_id INT AUTO_INCREMENT PRIMARY KEY,
    patient_id INT NOT NULL,
    pharmacist_id INT NOT NULL,
    delivery_address VARCHAR(255) NOT NULL,
    status VARCHAR(50) DEFAULT 'Pending',
    bill_id INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (bill_id) REFERENCES bills(bill_id)
);

CREATE TABLE bills (
    bill_id INT AUTO_INCREMENT PRIMARY KEY,
    patient_id INT,
    pharmacist_id INT,
    total_amount DECIMAL(10,2),
    payment_status VARCHAR(20) DEFAULT 'Pending',
    pdf_path VARCHAR(200) DEFAULT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE bill_items (
    bill_item_id INT AUTO_INCREMENT PRIMARY KEY,
    bill_id INT,
    medicine_name VARCHAR(100),
    quantity INT,
    price DECIMAL(10,2),
    amount DECIMAL(10,2),
    FOREIGN KEY (bill_id) REFERENCES bills(bill_id)
);

CREATE TABLE medicine_orders (
    order_id INT AUTO_INCREMENT PRIMARY KEY,
    patient_id INT NOT NULL,
    pharmacist_id INT NOT NULL,
    prescription_id INT,
    delivery_address VARCHAR(255) NOT NULL,
    status ENUM('Pending','Accepted','Rejected','Delivered') DEFAULT 'Pending',
    bill_id INT NULL,
    order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_id) REFERENCES patients(patient_id),
    FOREIGN KEY (pharmacist_id) REFERENCES pharmacists(pharmacist_id),
    FOREIGN KEY (prescription_id) REFERENCES prescriptions(prescription_id)
);

CREATE TABLE prescription_medicines (
    medicine_id INT AUTO_INCREMENT PRIMARY KEY,
    prescription_id INT NOT NULL,
    medicine_name VARCHAR(100),
    dosage VARCHAR(50),
    frequency VARCHAR(50),
    duration VARCHAR(50),
    quantity INT,
    price DECIMAL(10,2),
    FOREIGN KEY (prescription_id) REFERENCES prescriptions(prescription_id) ON DELETE CASCADE
);

-- Insert sample data
INSERT INTO doctors (doctor_name, email, password, specialization, contact_number) VALUES
('Dr. Rajesh Kumar', 'rajesh@hospital.com', 'Doctor@123', 'Cardiologist', '9876543210'),
('Dr. Priya Sharma', 'priya@hospital.com', 'Doctor@123', 'Pediatrician', '9876543211'),
('Dr. Amit Patel', 'amit@hospital.com', 'Doctor@123', 'General Medicine', '9876543212');

INSERT INTO pharmacists (pharmacist_name, email, password, pharmacy_name, contact_number) VALUES
('Ravi Pharmacy', 'ravi@pharmacy.com', 'Pharma@123', 'City Medical Store', '9876543220'),
('Sunita Medicals', 'sunita@pharmacy.com', 'Pharma@123', 'Health Plus Pharmacy', '9876543221'),
('Kumar Pharmacy', 'kumar@pharmacy.com', 'Pharma@123', 'Life Care Medicals', '9876543222');

-- Sample medicines for each pharmacy
INSERT INTO medicines (pharmacist_id, medicine_name, used_for, dosage, price) VALUES
(1, 'Paracetamol', 'Fever, Pain Relief', '500mg', 25.00),
(1, 'Amoxicillin', 'Bacterial Infections', '250mg', 85.00),
(1, 'Crocin', 'Fever, Headache', '650mg', 30.00),
(1, 'Dolo 650', 'Fever, Body Pain', '650mg', 28.00),
(1, 'Azithromycin', 'Respiratory Infections', '500mg', 120.00),
(2, 'Cetirizine', 'Allergies', '10mg', 45.00),
(2, 'Omeprazole', 'Acidity', '20mg', 65.00),
(2, 'Metformin', 'Diabetes', '500mg', 55.00),
(2, 'Amlodipine', 'Blood Pressure', '5mg', 75.00),
(2, 'Atorvastatin', 'Cholesterol', '10mg', 95.00),
(3, 'Ibuprofen', 'Pain, Inflammation', '400mg', 40.00),
(3, 'Pantoprazole', 'Acidity', '40mg', 70.00),
(3, 'Losartan', 'Blood Pressure', '50mg', 80.00),
(3, 'Aspirin', 'Heart Health', '75mg', 35.00),
(3, 'Vitamin D3', 'Bone Health', '60000 IU', 150.00);

SHOW TABLES;
SELECT 'Database setup completed successfully!' as Status;