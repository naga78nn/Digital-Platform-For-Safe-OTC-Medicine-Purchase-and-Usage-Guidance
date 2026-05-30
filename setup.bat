@echo off
echo 🏥 Medical Management System - Laptop Setup
echo ==========================================

echo 📦 Installing Python dependencies...
pip install flask mysql-connector-python reportlab requests

echo 🗄️ Setting up MySQL database...
echo Please enter your MySQL root password when prompted:
mysql -u root -p -e "CREATE DATABASE IF NOT EXISTS medican_management;"
mysql -u root -p medican_management < database_setup.sql

echo ✅ Setup completed successfully!
echo 🚀 Starting the application...
echo Open http://localhost:5555 in your browser
echo Press Ctrl+C to stop the server

python app.py

pause