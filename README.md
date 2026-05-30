# 🏥 Medical Management System

A comprehensive web-based healthcare management platform built with Flask and MySQL, designed to streamline medical services including patient appointments, prescriptions, pharmacy management, and billing.

## ✨ Features

### 👥 Multi-Role System
- **Patients**: Book appointments, view prescriptions, order medicines
- **Doctors**: Manage appointments, create prescriptions, view history
- **Pharmacists**: Manage medicines, generate bills, handle orders

### 🔐 Authentication & Security
- Secure login/signup with password validation
- Email-based OTP password reset system
- Role-based access control
- Session management

### 📅 Appointment Management
- Patient appointment booking with date validation
- Doctor approval/decline system
- Real-time status updates
- Appointment history tracking

### 💊 Prescription System
- Digital prescription creation with dropdown selections
- Medicine dosage, frequency, and duration tracking
- Prescription history and editing capabilities
- Patient prescription viewing

### 🏪 Pharmacy Management
- Medicine inventory management
- Patient prescription search with security validation
- Bill generation with itemized details
- Order fulfillment tracking

### 💳 Payment Gateway
- Multiple payment methods (UPI, Card, Cash)
- QR code scanner integration
- PDF receipt generation
- Payment status tracking

## 🛠️ Tech Stack

- **Backend**: Python Flask
- **Database**: MySQL
- **Frontend**: HTML5, CSS3, JavaScript
- **PDF Generation**: ReportLab
- **Email Service**: Brevo API, EmailJS
- **Styling**: Custom CSS with responsive design

## 📋 Prerequisites

- Python 3.7+
- MySQL Server 8.0+
- Git
- Web browser

## 🚀 Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd medical-management-system
   ```

2. **Install Python dependencies**
   ```bash
   pip install flask mysql-connector-python reportlab requests
   ```

3. **Set up MySQL database**
   ```sql
   CREATE DATABASE medican_management;
   USE medican_management;
   ```
  **sql tables**
  

4. **Import database schema**
   - Run the SQL commands from the database setup section below

5. **Configure database connection**
   - Update database credentials in `app.py` if needed:
   ```python
   def get_connection():
       return mysql.connector.connect(
           host="localhost",
           user="root",
           password="root",
           database="medican_management"
       )
   ```

6. **Run the application**
   ```bash
   python app.py
   ```

7. **Access the application**
   - Open browser and navigate to `http://localhost:5555`

## 🗄️ Database Schema

### Core Tables
- `patients` - Patient information and credentials
- `doctors` - Doctor profiles and specializations
- `pharmacists` - Pharmacy and pharmacist details
- `appointments` - Appointment bookings and status
- `prescriptions` - Digital prescriptions
- `prescription_items` - Individual medicine details
- `medicines` - Pharmacy inventory
- `orders` - Medicine orders from patients
- `bills` - Generated bills and payment status
- `bill_items` - Itemized bill details

**mysql tables**
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


### Key Relationships
- Patients ↔ Appointments ↔ Doctors
- Appointments → Prescriptions → Prescription Items
- Patients → Orders → Pharmacists
- Orders → Bills → Bill Items

## 🎯 User Workflows

### Patient Journey
1. **Registration** → Login → Dashboard
2. **Book Appointment** → Select doctor and date
3. **Wait for Approval** → Doctor approves/declines
4. **Receive Prescription** → After doctor consultation
5. **Order Medicines** → From available pharmacies
6. **Make Payment** → Complete order with receipt

### Doctor Journey
1. **Login** → Dashboard → View pending appointments
2. **Approve/Decline** → Manage appointment requests
3. **Create Prescription** → Add medicines and dosages
4. **View History** → Track prescribed appointments

### Pharmacist Journey
1. **Login** → Dashboard → Manage inventory
2. **Add Medicines** → Update stock and prices
3. **Process Orders** → Search patient prescriptions
4. **Generate Bills** → Create itemized invoices
5. **Track Payments** → Monitor order completion

## 🔧 Key Features Implementation

### Password Security
- Minimum 6 characters with uppercase, lowercase, numbers, and special characters
- Email lowercase conversion for consistency
- Secure session management

### OTP System
- Integration with Brevo and EmailJS APIs
- Fallback demo mode for development
- 6-digit OTP generation and validation

### Payment Processing
- Multi-method payment gateway
- QR code integration for digital payments
- Automated PDF receipt generation
- Payment status tracking

### Responsive Design
- Mobile-friendly interface
- Consistent teal color theme (#0f766e)
- Professional medical styling
- Interactive dropdown menus

## 📱 Screenshots & Demo

### Landing Page
- Role selection (Patient/Doctor/Pharmacist)
- Clean, professional medical theme

### Dashboards
- **Patient**: Appointment booking, prescription viewing, order management
- **Doctor**: Appointment management, prescription creation, history
- **Pharmacist**: Inventory management, order processing, billing

### Key Pages
- Secure login/signup with validation
- Interactive prescription creation
- Payment gateway with multiple options
- PDF receipt generation

## 🔒 Security Features

- Role-based access control
- Session timeout management
- SQL injection prevention
- Password strength validation
- Email verification for password reset

## 🚀 Deployment

### **Quick Deploy Options**

#### **1. Heroku (Recommended)**
```bash
# Install dependencies
pip install gunicorn

# Deploy
heroku create your-medical-app
heroku addons:create cleardb:ignite
heroku config:set FLASK_ENV=production
git add .
git commit -m "Deploy to Heroku"
git push heroku main
```

#### **2. Railway**
```bash
# Push to GitHub, connect Railway
# Automatic deployment with railway.json
```

#### **3. Docker**
```bash
docker-compose up -d
```

#### **4. VPS/Server**
```bash
# Ubuntu setup
sudo apt update && sudo apt install python3-pip mysql-server nginx
pip3 install -r requirements.txt
gunicorn --bind 0.0.0.0:5000 app:app
```

### **Environment Variables**
```bash
DB_HOST=your-database-host
DB_USER=your-database-user
DB_PASSWORD=your-database-password
DB_NAME=medican_management
PORT=5555
FLASK_ENV=production
```

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👨‍💻 Developer

**Naga Lakshmi Kuppala**
- Email: nagalakshmikuppalampc2020@gmail.com
- GitHub: [(https://github.com/naga78nn)]

## 🙏 Acknowledgments

- Flask community for excellent documentation
- MySQL for robust database management
- ReportLab for PDF generation capabilities
- Medical professionals for workflow insights

---

**© 2026 Digital Health Care System. All Rights Reserved.**

*Built with ❤️ for better healthcare management*
