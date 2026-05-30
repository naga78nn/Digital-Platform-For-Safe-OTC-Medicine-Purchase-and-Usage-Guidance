from flask import Flask, render_template, request, redirect, session, flash, url_for, jsonify
import mysql.connector
from datetime import date, datetime
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
import random
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests
import re
# -------------------- Database connection --------------------
import os

def get_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", "root"),
        database=os.getenv("DB_NAME", "medican_management")
    )

# -------------------- Flask app --------------------
app = Flask(__name__)
app.secret_key = "private_key"

# -------------------- Landing Page --------------------
@app.route("/")
def landing():
    return render_template("LandingPage.html")

@app.route("/Landing")
def LandingPage():
    return render_template("landing.html")

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/medicines")
def medicines():
    return render_template("medicines.html")



@app.route("/download_receipt/<int:bill_id>")
def download_receipt(bill_id):
    from flask import send_file
    from reportlab.lib.units import inch
    from reportlab.platypus import Table, TableStyle
    from reportlab.lib import colors
    from datetime import datetime
    
    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    cur.execute("""
        SELECT b.*, p.patient_name, p.mobile_number, ph.pharmacy_name, ph.contact_number as pharmacy_contact 
        FROM bills b
        JOIN patients p ON b.patient_id = p.patient_id
        JOIN pharmacists ph ON b.pharmacist_id = ph.pharmacist_id
        WHERE b.bill_id=%s
    """, (bill_id,))
    bill = cur.fetchone()

    cur.execute("SELECT * FROM bill_items WHERE bill_id=%s", (bill_id,))
    items = cur.fetchall()

    conn.close()

    file_path = f"Medical_Receipt_{bill_id}.pdf"
    doc = SimpleDocTemplate(file_path, pagesize=A4, topMargin=0.5*inch)

    styles = getSampleStyleSheet()
    story = []

    # Header
    story.append(Paragraph("<b>🏥 MEDICAL PHARMACY RECEIPT</b>", styles["Title"]))
    story.append(Spacer(1, 12))
    
    # Pharmacy Info
    story.append(Paragraph(f"<b>{bill['pharmacy_name']}</b>", styles["Heading2"]))
    story.append(Paragraph(f"Contact: {bill['pharmacy_contact']}", styles["Normal"]))
    story.append(Paragraph("Licensed Medical Store", styles["Normal"]))
    story.append(Spacer(1, 12))
    
    # Bill Details
    story.append(Paragraph("<b>BILL DETAILS</b>", styles["Heading3"]))
    story.append(Paragraph(f"Bill No: #{bill['bill_id']:04d}", styles["Normal"]))
    story.append(Paragraph(f"Date: {datetime.now().strftime('%d/%m/%Y %I:%M %p')}", styles["Normal"]))
    story.append(Paragraph(f"Patient: {bill['patient_name']}", styles["Normal"]))
    story.append(Paragraph(f"Mobile: {bill['mobile_number']}", styles["Normal"]))
    story.append(Spacer(1, 15))

    # Items Table
    table_data = [['S.No', 'Medicine Name', 'Qty', 'Rate', 'Amount']]
    
    for idx, item in enumerate(items, 1):
        table_data.append([
            str(idx),
            item['medicine_name'],
            str(item['quantity']),
            f"₹{item['price']:.2f}",
            f"₹{item['amount']:.2f}"
        ])
    
    # Add totals
    table_data.append(['', '', '', 'TOTAL:', f"₹{bill['total_amount']:.2f}"])
    
    table = Table(table_data, colWidths=[0.8*inch, 2.5*inch, 0.8*inch, 1.2*inch, 1.2*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -4), colors.beige),
        ('BACKGROUND', (0, -3), (-1, -1), colors.lightgrey),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
    ]))
    
    story.append(table)
    story.append(Spacer(1, 20))
    
    # Payment Info
    story.append(Paragraph(f"<b>Payment Status: {bill['payment_status']} ✅</b>", styles["Normal"]))
    story.append(Paragraph("Payment Mode: Digital Payment", styles["Normal"]))
    story.append(Spacer(1, 15))
    
    # Footer
    story.append(Paragraph("<b>Thank you for choosing our pharmacy!</b>", styles["Normal"]))
    story.append(Paragraph("Get well soon! 💊", styles["Normal"]))
    story.append(Spacer(1, 10))
    story.append(Paragraph("<i>This is a computer generated receipt.</i>", styles["Normal"]))

    doc.build(story)

    return send_file(file_path, as_attachment=True, download_name=f"Medical_Receipt_{bill_id}.pdf")

# ============================================================
# SEARCH PRESCRIPTION (PHARMACIST)
# ============================================================
@app.route("/search_prescription", methods=["GET", "POST"])
def search_prescription():
    if "pharmacist_id" not in session:
        if request.method == "GET":
            return redirect("/loginpage")
        return jsonify({"success": False, "message": "Please login first"})

    if request.method == "GET":
        return redirect("/pharmacy_dashboard")

    pharmacist_id = session["pharmacist_id"]
    patient_id = request.form.get("patient_id")

    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    # CHECK: Does this patient have an order for this pharmacist?
    cur.execute("""
        SELECT * FROM orders
        WHERE patient_id=%s AND pharmacist_id=%s
        ORDER BY created_at DESC LIMIT 1
    """, (patient_id, pharmacist_id))
    
    allowed_order = cur.fetchone()

    if not allowed_order:
        conn.close()
        return jsonify({"success": False, "message": "❌ This patient has not placed any order with your pharmacy!"})

    # Fetch prescription (latest)
    cur.execute("""
        SELECT p.*, pa.patient_name
        FROM prescriptions p
        JOIN patients pa ON p.patient_id = pa.patient_id
        WHERE p.patient_id=%s
        ORDER BY p.created_at DESC LIMIT 1
    """, (patient_id,))
    prescription = cur.fetchone()

    items = []
    if prescription:
        cur.execute("SELECT * FROM prescription_items WHERE prescription_id=%s",
                    (prescription["prescription_id"],))
        items = cur.fetchall()

    conn.close()

    if prescription:
        return jsonify({
            "success": True, 
            "message": "✅ Prescription found successfully!",
            "prescription": prescription,
            "items": items
        })
    else:
        return jsonify({
            "success": False, 
            "message": "⚠️ No prescription found for this patient."
        })




# ============================================================
# SIGNUP WITH VALIDATION
# ============================================================
import re

def validate_password(password):
    """Validate password: min 6 chars, uppercase, lowercase, number, special char"""
    if len(password) < 6:
        return False
    if not re.search(r'[A-Z]', password):  # Uppercase
        return False
    if not re.search(r'[a-z]', password):  # Lowercase
        return False
    if not re.search(r'\d', password):     # Number
        return False
    if not re.search(r'[@#$%]', password): # Special chars
        return False
    return True

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "GET":
        return render_template("signup.html")

    role = request.form.get("role")
    name = request.form.get("name")
    email = request.form.get("email").lower().strip()  # Convert to lowercase
    password = request.form.get("password")
    contact = request.form.get("contact")

    # Password validation
    if not validate_password(password):
        flash("Password must be at least 6 characters with uppercase, lowercase, number, and special character (@#$%)", "danger")
        return redirect("/signup")

    conn = get_connection()
    cmd = conn.cursor()

    try:
        # Check for duplicate email across all tables
        cmd.execute("SELECT email FROM doctors WHERE email=%s", (email,))
        if cmd.fetchone():
            flash("Email already registered as Doctor!", "danger")
            return redirect("/signup")
            
        cmd.execute("SELECT email FROM patients WHERE email=%s", (email,))
        if cmd.fetchone():
            flash("Email already registered as Patient!", "danger")
            return redirect("/signup")
            
        cmd.execute("SELECT email FROM pharmacists WHERE email=%s", (email,))
        if cmd.fetchone():
            flash("Email already registered as Pharmacist!", "danger")
            return redirect("/signup")

        # Insert based on role
        if role == "Doctor":
            specialization = request.form.get("specialization")
            if not specialization:
                flash("Specialization is required for Doctor registration!", "danger")
                return redirect("/signup")
            cmd.execute("""
                INSERT INTO doctors (doctor_name, email, password, contact_number, specialization)
                VALUES (%s, %s, %s, %s, %s)
            """, (name, email, password, contact, specialization))

        elif role == "Patient":
            age = request.form.get("age")
            gender = request.form.get("gender")
            if not age or not gender:
                flash("Age and Gender are required for Patient registration!", "danger")
                return redirect("/signup")
            cmd.execute("""
                INSERT INTO patients (patient_name, email, password, mobile_number, age, gender)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (name, email, password, contact, age, gender))

        elif role == "Pharmacist":
            pharmacy_name = request.form.get("pharmacy_name")
            if not pharmacy_name:
                flash("Pharmacy Name is required for Pharmacist registration!", "danger")
                return redirect("/signup")
            cmd.execute("""
                INSERT INTO pharmacists (pharmacist_name, pharmacy_name, email, password, contact_number)
                VALUES (%s, %s, %s, %s, %s)
            """, (name, pharmacy_name, email, password, contact))

        conn.commit()
        flash("Registration successful! Please login with your credentials.", "success")
        return redirect("/loginpage")

    except mysql.connector.Error as e:
        conn.rollback()
        flash(f"Registration failed: {str(e)}", "danger")
        return redirect("/signup")

    finally:
        conn.close()

# ============================================================
# VIEW BILL
# ============================================================
@app.route("/view_bill/<int:bill_id>")
def view_bill(bill_id):
    if "patient_id" not in session:
        return redirect("/loginpage")

    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    cur.execute("""
        SELECT b.*, ph.pharmacy_name, p.patient_name
        FROM bills b
        JOIN pharmacists ph ON b.pharmacist_id = ph.pharmacist_id
        JOIN patients p ON b.patient_id = p.patient_id
        WHERE b.bill_id=%s
    """, (bill_id,))
    bill = cur.fetchone()

    cur.execute("SELECT * FROM bill_items WHERE bill_id=%s", (bill_id,))
    items = cur.fetchall()

    conn.close()

    return render_template("view_bill.html", bill=bill, items=items)

# ============================================================
# PAY BILL → redirect to payment screen
# ============================================================
@app.route("/pay_bill/<int:bill_id>", methods=["POST"])
def pay_bill(bill_id):
    if "patient_id" not in session:
        return redirect("/loginpage")

    return redirect(url_for("payment_page", bill_id=bill_id))

@app.route("/payment/<int:bill_id>")
def payment_page(bill_id):
    if "patient_id" not in session:
        return redirect("/loginpage")

    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    cur.execute("SELECT * FROM bills WHERE bill_id=%s", (bill_id,))
    bill = cur.fetchone()

    conn.close()

    return render_template("payment_page.html", bill=bill)

# ============================================================
# CONFIRM PAYMENT
# updates bills + orders + redirects to patient dashboard
# ============================================================
@app.route("/confirm_payment/<int:bill_id>", methods=["GET", "POST"])
def confirm_payment(bill_id):
    if "patient_id" not in session:
        return redirect("/loginpage")

    conn = get_connection()
    cur = conn.cursor()

    try:
        if request.method == "POST":
            # Handle AJAX payment request
            data = request.get_json()
            if data:
                payment_method = data.get('payment_method', 'Cash')
            else:
                payment_method = 'Cash'
            
            # Update bill payment status only
            cur.execute("UPDATE bills SET payment_status='Paid' WHERE bill_id=%s", (bill_id,))
            
            conn.commit()
            conn.close()
            
            return jsonify({"success": True, "message": "Payment successful!"})
            
        else:
            # Handle GET request (fallback)
            # Update bill payment status only
            cur.execute("UPDATE bills SET payment_status='Paid' WHERE bill_id=%s", (bill_id,))
            
            conn.commit()
            conn.close()
            
            flash("✅ Payment successful! 💳", "success")
            return redirect("/patient_dashboard")
            
    except Exception as e:
        conn.rollback()
        conn.close()
        if request.method == "POST":
            return jsonify({"success": False, "message": "Payment failed!"}), 500
        else:
            flash("❌ Payment failed! Please try again.", "danger")
            return redirect("/patient_dashboard")


# ============================================================
# VIEW PRESCRIPTION
# ============================================================
@app.route("/view_prescription/<int:prescription_id>")
def view_prescription(prescription_id):
    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    cur.execute("""
        SELECT p.*, pat.patient_name, d.doctor_name
        FROM prescriptions p
        JOIN patients pat ON p.patient_id = pat.patient_id
        JOIN doctors d ON p.doctor_id = d.doctor_id
        WHERE p.prescription_id=%s
    """, (prescription_id,))
    prescription = cur.fetchone()

    cur.execute("SELECT * FROM prescription_items WHERE prescription_id=%s", (prescription_id,))
    items = cur.fetchall()

    conn.close()

    return render_template("view_prescription.html", prescription=prescription, items=items)

# ============================================================
# CANCEL ORDER
# ============================================================
@app.route("/cancel_order/<int:order_id>", methods=["POST"])
def cancel_order(order_id):
    if "patient_id" not in session:
        return redirect("/loginpage")

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM orders WHERE order_id=%s", (order_id,))
    conn.commit()
    conn.close()

    flash("Order cancelled", "success")
    return redirect("/patient_dashboard")

# ============================================================
# MARK ORDER COMPLETE (PHARMACIST)
# ============================================================
@app.route("/mark_complete/<int:order_id>", methods=["POST"])
def mark_complete(order_id):
    if "pharmacist_id" not in session:
        return redirect("/loginpage")

    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute("UPDATE orders SET status='Completed' WHERE order_id=%s", (order_id,))
    
    conn.commit()
    conn.close()

    flash("Order marked as completed!", "success")
    return redirect("/pharmacy_dashboard")

# ============================================================
# ADD MEDICINE (PHARMACIST)
# ============================================================
@app.route("/add_medicine", methods=["POST"])
def add_medicine():
    if "pharmacist_id" not in session:
        return redirect("/loginpage")

    pharmacist_id = session["pharmacist_id"]
    medicine_name = request.form.get("medicine_name")
    custom_medicine_name = request.form.get("custom_medicine_name", "")
    medicine_type = request.form.get("type")
    custom_type = request.form.get("custom_type", "")
    used_for = request.form.get("used_for")
    dosage = request.form.get("dosage")
    custom_dosage = request.form.get("custom_dosage", "")
    price = request.form.get("price")

    # Use custom values if "Other" was selected
    final_medicine_name = custom_medicine_name if medicine_name == "Other" and custom_medicine_name else medicine_name
    final_dosage = custom_dosage if dosage == "Other" and custom_dosage else dosage

    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute("""
        INSERT INTO medicines (pharmacist_id, medicine_name, used_for, dosage, price)
        VALUES (%s, %s, %s, %s, %s)
    """, (pharmacist_id, final_medicine_name, used_for, final_dosage, price))
    
    conn.commit()
    conn.close()

    flash("Medicine added successfully!", "success")
    return redirect("/pharmacy_dashboard")

# ============================================================
# UPDATE MEDICINE (PHARMACIST)
# ============================================================
@app.route("/update_medicine", methods=["POST"])
def update_medicine():
    if "pharmacist_id" not in session:
        return redirect("/loginpage")

    medicine_id = request.form.get("medicine_id")
    medicine_name = request.form.get("medicine_name")
    used_for = request.form.get("used_for")
    dosage = request.form.get("dosage")
    price = request.form.get("price")
    pharmacist_id = session["pharmacist_id"]

    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute("""
        UPDATE medicines 
        SET medicine_name=%s, used_for=%s, dosage=%s, price=%s 
        WHERE medicine_id=%s AND pharmacist_id=%s
    """, (medicine_name, used_for, dosage, price, medicine_id, pharmacist_id))
    
    conn.commit()
    conn.close()

    flash("Medicine updated successfully!", "success")
    return redirect("/pharmacy_dashboard")

# ============================================================
# DELETE MEDICINE (PHARMACIST)
# ============================================================
@app.route("/delete_medicine/<int:medicine_id>", methods=["POST"])
def delete_medicine(medicine_id):
    if "pharmacist_id" not in session:
        return redirect("/loginpage")

    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute("DELETE FROM medicines WHERE medicine_id=%s", (medicine_id,))
    
    conn.commit()
    conn.close()

    flash("Medicine deleted successfully!", "success")
    return redirect("/pharmacy_dashboard")

@app.route("/book_medicine", methods=["POST"])
def book_medicine():
    if "patient_id" not in session:
        return redirect("/loginpage")

    patient_id = session["patient_id"]
    pharmacist_id = request.form.get("pharmacist_id")
    delivery_address = request.form.get("delivery_address")

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO orders (patient_id, pharmacist_id, delivery_address, status)
        VALUES (%s, %s, %s, 'Pending')
    """, (patient_id, pharmacist_id, delivery_address))

    conn.commit()
    conn.close()

    flash("Order placed successfully!", "success")
    return redirect("/patient_dashboard")

@app.route("/doctor/history")
def doctor_history():
    if "doctor_id" not in session:
        return redirect("/loginpage")

    doctor_id = session["doctor_id"]

    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    # Get prescribed appointments history
    cur.execute("""
        SELECT a.appointment_id, a.patient_id, p.patient_name,
               p.email AS patient_email, a.appointment_date,
               pr.prescription_id, pr.diagnosis, pr.notes, pr.created_at as prescribed_at
        FROM appointments a
        JOIN patients p ON a.patient_id = p.patient_id
        LEFT JOIN prescriptions pr ON a.appointment_id = pr.appointment_id
        WHERE a.doctor_id=%s AND a.is_prescribed = 1
        ORDER BY pr.created_at DESC
    """, (doctor_id,))

    history = cur.fetchall()
    conn.close()

    return render_template("doctor_history.html", history=history)

# ============================================================
# EDIT PRESCRIPTION (DOCTOR)
# ============================================================
@app.route("/edit_prescription/<int:prescription_id>", methods=["GET", "POST"])
def edit_prescription(prescription_id):
    if "doctor_id" not in session:
        return redirect("/loginpage")

    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    if request.method == "GET":
        # Get prescription details
        cur.execute("""
            SELECT p.*, pat.patient_name, a.appointment_date
            FROM prescriptions p
            JOIN patients pat ON p.patient_id = pat.patient_id
            JOIN appointments a ON p.appointment_id = a.appointment_id
            WHERE p.prescription_id=%s AND p.doctor_id=%s
        """, (prescription_id, session["doctor_id"]))
        prescription = cur.fetchone()

        # Get prescription items
        cur.execute("SELECT * FROM prescription_items WHERE prescription_id=%s", (prescription_id,))
        items = cur.fetchall()

        conn.close()
        return render_template("edit_prescription.html", prescription=prescription, items=items)

    else:  # POST - Update prescription
        diagnosis = request.form.get("diagnosis")
        notes = request.form.get("notes")

        # Update prescription
        cur.execute("""
            UPDATE prescriptions 
            SET diagnosis=%s, notes=%s 
            WHERE prescription_id=%s AND doctor_id=%s
        """, (diagnosis, notes, prescription_id, session["doctor_id"]))

        # Delete old items
        cur.execute("DELETE FROM prescription_items WHERE prescription_id=%s", (prescription_id,))

        # Add new items
        med_names = request.form.getlist("medicine_name[]")
        dosages = request.form.getlist("dosage[]")
        freqs = request.form.getlist("frequency[]")
        durations = request.form.getlist("duration_days[]")
        quantities = request.form.getlist("quantity[]")

        for i in range(len(med_names)):
            cur.execute("""
                INSERT INTO prescription_items
                (prescription_id, medicine_name, dosage, frequency, duration_days, quantity)
                VALUES (%s,%s,%s,%s,%s,%s)
            """, (
                prescription_id,
                med_names[i],
                dosages[i],
                freqs[i],
                durations[i],
                quantities[i]
            ))

        conn.commit()
        conn.close()

        flash("Prescription updated successfully!", "success")
        return redirect("/doctor/history")


@app.route("/book_appointment", methods=["POST"])
def book_appointment():
    if "patient_id" not in session:
        return redirect("/loginpage")
    
    patient_id = session["patient_id"]
    doctor_id = request.form.get("doctor_id")
    appointment_date = request.form.get("appointment_date")

    # Backend check (no past dates)
    from datetime import date
    if appointment_date < str(date.today()):
        flash("Invalid date! You cannot book past dates.", "danger")
        return redirect("/patient_dashboard")

    conn = get_connection()
    cmd = conn.cursor()

    cmd.execute("""
        INSERT INTO appointments 
        (patient_id, doctor_id, appointment_date, status)
        VALUES (%s, %s, %s, 'Pending')
    """, (patient_id, doctor_id, appointment_date))

    conn.commit()
    conn.close()

    flash("Appointment booked successfully! 📅", "success")
    return redirect("/patient_dashboard")

# ============================================================
# GENERATE BILL (PHARMACIST)
# ============================================================
@app.route("/generate_bill", methods=["POST"])
def generate_bill():
    if "pharmacist_id" not in session:
        flash("Please login as pharmacist first!", "danger")
        return redirect("/loginpage")

    try:
        patient_id = request.form.get("patient_id")
        pharmacist_id = session["pharmacist_id"]

        selected = request.form.getlist("selected[]")
        names = request.form.getlist("medicine_name[]")
        quantities = request.form.getlist("quantity[]")
        prices = request.form.getlist("price[]")

        # Validation
        if not patient_id:
            flash("Patient ID is required!", "danger")
            return redirect("/pharmacy_dashboard")
        
        if not selected:
            flash("Please select at least one medicine!", "danger")
            return redirect("/pharmacy_dashboard")
        
        if not names or not quantities or not prices:
            flash("Medicine data is incomplete!", "danger")
            return redirect("/pharmacy_dashboard")

        conn = get_connection()
        cur = conn.cursor()

        total = 0

        # Create bill
        cur.execute("""
            INSERT INTO bills (patient_id, pharmacist_id, total_amount, payment_status)
            VALUES (%s, %s, %s, 'Pending')
        """, (patient_id, pharmacist_id, 0))

        bill_id = cur.lastrowid

        # Insert items
        for idx in selected:
            try:
                i = int(idx)
                if i >= len(names) or i >= len(quantities) or i >= len(prices):
                    continue
                    
                qty = int(quantities[i])
                price = float(prices[i])
                amount = qty * price
                total += amount

                cur.execute("""
                    INSERT INTO bill_items
                    (bill_id, medicine_name, quantity, price, amount)
                    VALUES (%s,%s,%s,%s,%s)
                """, (bill_id, names[i], qty, price, amount))
            except (ValueError, IndexError) as e:
                flash(f"Error processing medicine data: {str(e)}", "danger")
                conn.rollback()
                conn.close()
                return redirect("/pharmacy_dashboard")

        # Update bill amount
        cur.execute("UPDATE bills SET total_amount=%s WHERE bill_id=%s", (total, bill_id))

        # Update related order status
        cur.execute("""
            UPDATE orders
            SET status='Pending'
            WHERE patient_id=%s AND pharmacist_id=%s AND status='Pending'
        """, (patient_id, pharmacist_id))

        conn.commit()
        conn.close()

        flash(f"✅ Bill #{bill_id} generated successfully! Total: ₹{total:.2f}", "success")
        return redirect("/pharmacy_dashboard")
        
    except Exception as e:
        flash(f"❌ Error generating bill: {str(e)}", "danger")
        return redirect("/pharmacy_dashboard")

# ============================================================
# GET TODAY'S APPOINTMENTS (AJAX)
# ============================================================
@app.route("/get_today_appointments")
def get_today_appointments():
    if "doctor_id" not in session:
        return jsonify({"success": False, "message": "Please login first"})

    from datetime import date
    today = str(date.today())
    doctor_id = session["doctor_id"]

    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    cur.execute("""
        SELECT a.*, p.patient_name, p.email as patient_email
        FROM appointments a
        JOIN patients p ON a.patient_id = p.patient_id
        WHERE a.doctor_id=%s AND a.appointment_date=%s
        ORDER BY a.created_at DESC
    """, (doctor_id, today))

    appointments = cur.fetchall()
    conn.close()

    return jsonify({"success": True, "appointments": appointments})

# ============================================================
# DOCTOR DASHBOARD + HISTORY + PRESCRIBE
# ============================================================
@app.route("/doctor_dashboard")
def doctor_dashboard():
    if "doctor_id" not in session:
        return redirect("/loginpage")

    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    # Get doctor profile
    cur.execute("SELECT * FROM doctors WHERE doctor_id=%s", (session["doctor_id"],))
    doctor_profile = cur.fetchone()

    # Get pending and approved appointments
    cur.execute("""
        SELECT a.*, p.patient_name, p.email as patient_email
        FROM appointments a
        JOIN patients p ON a.patient_id = p.patient_id
        WHERE a.doctor_id=%s AND a.status IN ('Pending', 'Approved') AND (a.is_prescribed=0 OR a.is_prescribed IS NULL)
        ORDER BY a.appointment_id ASC
    """, (session["doctor_id"],))

    appointments = cur.fetchall()
    conn.close()

    # Get current date and time
    current_datetime = datetime.now().strftime("%A, %B %d, %Y - %I:%M %p")

    return render_template("doctor_dashboard.html", appointments=appointments, profile=doctor_profile, current_datetime=current_datetime)

@app.route("/approve/<int:appointment_id>")
def approve_appointment(appointment_id):
    if "doctor_id" not in session:
        return redirect("/loginpage")

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE appointments 
        SET status='Approved'
        WHERE appointment_id=%s
    """, (appointment_id,))

    conn.commit()
    conn.close()

    return redirect("/doctor_dashboard")


@app.route("/decline/<int:appointment_id>")
def decline_appointment(appointment_id):
    if "doctor_id" not in session:
        flash("Please login as doctor first!", "danger")
        return redirect("/loginpage")

    try:
        conn = get_connection()
        cur = conn.cursor()

        # Update status
        cur.execute("""
            UPDATE appointments 
            SET status='Rejected' 
            WHERE appointment_id=%s
        """, (appointment_id,))

        conn.commit()
        flash("Appointment declined successfully!", "success")

        cur.close()
        conn.close()
        return redirect("/doctor_dashboard")

    except Exception as e:
        flash(f"Error declining appointment: {str(e)}", "danger")
        return redirect("/doctor_dashboard")


@app.route("/prescribe/<int:appointment_id>", methods=["GET", "POST"])
def prescribe(appointment_id):
    if "doctor_id" not in session:
        return redirect("/loginpage")

    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    cur.execute("""
        SELECT a.*, p.patient_name
        FROM appointments a
        JOIN patients p ON a.patient_id=p.patient_id
        WHERE appointment_id=%s AND doctor_id=%s
    """, (appointment_id, session["doctor_id"]))

    appt = cur.fetchone()

    if request.method == "POST":
        diagnosis = request.form.get("diagnosis")
        notes = request.form.get("notes")

        med_names = request.form.getlist("medicine_name[]")
        custom_med_names = request.form.getlist("custom_medicine_name[]")
        dosages = request.form.getlist("dosage[]")
        custom_dosages = request.form.getlist("custom_dosage[]")
        freqs = request.form.getlist("frequency[]")
        durations = request.form.getlist("duration_days[]")
        quantities = request.form.getlist("quantity[]")
        prices = request.form.getlist("price[]")

        cur2 = conn.cursor()

        cur2.execute("""
            INSERT INTO prescriptions (appointment_id, patient_id, doctor_id, diagnosis, notes)
            VALUES (%s,%s,%s,%s,%s)
        """, (appointment_id, appt["patient_id"], appt["doctor_id"], diagnosis, notes))

        pres_id = cur2.lastrowid

        for i in range(len(med_names)):
            # Use custom medicine name if "Other" was selected
            final_med_name = custom_med_names[i] if med_names[i] == "Other" and i < len(custom_med_names) and custom_med_names[i] else med_names[i]
            # Use custom dosage if "Other" was selected
            final_dosage = custom_dosages[i] if dosages[i] == "Other" and i < len(custom_dosages) and custom_dosages[i] else dosages[i]
            
            cur2.execute("""
                INSERT INTO prescription_items
                (prescription_id, medicine_name, dosage, frequency, duration_days, quantity)
                VALUES (%s,%s,%s,%s,%s,%s)
            """, (
                pres_id,
                final_med_name,
                final_dosage,
                freqs[i],
                durations[i],
                quantities[i]
            ))

        cur2.execute("UPDATE appointments SET is_prescribed=1 WHERE appointment_id=%s", (appointment_id,))

        conn.commit()
        conn.close()

        flash("Prescription created successfully!", "success")
        return redirect("/doctor_dashboard")

    conn.close()
    return render_template("prescribe.html", appointment=appt)

# ============================================================
# PATIENT DASHBOARD
# ============================================================
@app.route("/patient_dashboard")
def patient_dashboard():
    if "patient_id" not in session:
        return redirect("/loginpage")

    patient_id = session["patient_id"]
    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    # Get patient profile
    cur.execute("SELECT * FROM patients WHERE patient_id=%s", (patient_id,))
    patient_profile = cur.fetchone()

    cur.execute("SELECT * FROM doctors")
    doctors = cur.fetchall()

    cur.execute("SELECT * FROM pharmacists")
    pharmacies = cur.fetchall()

    cur.execute("SELECT * FROM prescriptions WHERE patient_id=%s ORDER BY created_at DESC", (patient_id,))
    prescriptions = cur.fetchall()

    cur.execute("""
        SELECT a.*, d.doctor_name
        FROM appointments a
        JOIN doctors d ON a.doctor_id=d.doctor_id
        WHERE patient_id=%s
        ORDER BY a.created_at DESC
    """, (patient_id,))
    appointments = cur.fetchall()

    cur.execute("""
        SELECT o.*, ph.pharmacy_name
        FROM orders o
        JOIN pharmacists ph ON o.pharmacist_id=ph.pharmacist_id
        WHERE o.patient_id=%s
        ORDER BY o.created_at DESC
    """, (patient_id,))
    orders = cur.fetchall()

    cur.execute("""
        SELECT b.*, ph.pharmacy_name
        FROM bills b
        JOIN pharmacists ph ON b.pharmacist_id = ph.pharmacist_id
        WHERE b.patient_id=%s
        ORDER BY b.created_at DESC
    """, (patient_id,))
    bills = cur.fetchall()

    conn.close()

    # Get current date and time
    current_datetime = datetime.now().strftime("%A, %B %d, %Y - %I:%M %p")

    return render_template(
        "patient_dashboard.html",
        doctors=doctors,
        pharmacies=pharmacies,
        prescriptions=prescriptions,
        my_appointments=appointments,
        orders=orders,
        bills=bills,
        current_date=str(date.today()),
        profile=patient_profile,
        current_datetime=current_datetime
    )

# ============================================================
# PHARMACY DASHBOARD
# ============================================================
@app.route("/pharmacy_dashboard")
def pharmacy_dashboard():
    if "pharmacist_id" not in session:
        return redirect("/loginpage")

    conn = get_connection()

    # ✅ DEBUG PART (ADD HERE)
    cur_debug = conn.cursor()
    cur_debug.execute("SELECT DATABASE();")
    print("Connected DB:", cur_debug.fetchone())

    cur_debug.execute("DESCRIBE bills;")
    print("Bills columns:", cur_debug.fetchall())
    # -------------------------

    cur = conn.cursor(dictionary=True)

    pharmacist_id = session["pharmacist_id"]
    today = str(date.today())

    # Get pharmacist profile
    cur.execute("SELECT * FROM pharmacists WHERE pharmacist_id=%s", (pharmacist_id,))
    pharmacist_profile = cur.fetchone()

    # Get today's sales data
    cur.execute("""
        SELECT 
            COUNT(*) as bills_count,
            COALESCE(SUM(total_amount), 0) as total_revenue
        FROM bills 
        WHERE pharmacist_id=%s AND payment_status='Paid' AND DATE(created_at)=%s
    """, (pharmacist_id, today))
    sales_data = cur.fetchone()

    # Get today's medicines sold count
    cur.execute("""
        SELECT COALESCE(SUM(bi.quantity), 0) as medicines_sold
        FROM bill_items bi
        JOIN bills b ON bi.bill_id = b.bill_id
        WHERE b.pharmacist_id=%s AND b.payment_status='Paid' AND DATE(b.created_at)=%s
    """, (pharmacist_id, today))
    medicines_data = cur.fetchone()

    # Get today's completed bills
    cur.execute("""
        SELECT b.*, p.patient_name
        FROM bills b
        JOIN patients p ON b.patient_id = p.patient_id
        WHERE b.pharmacist_id=%s AND b.payment_status='Paid' AND DATE(b.created_at)=%s
        ORDER BY b.created_at DESC
    """, (pharmacist_id, today))
    today_bills = cur.fetchall()

    # Get active orders
    cur.execute("""
        SELECT 
            o.order_id,
            o.patient_id,
            p.patient_name,
            o.delivery_address,
            o.status,
            COALESCE(b.payment_status, 'Pending') as payment_status,
            o.created_at
        FROM orders o
        JOIN patients p ON o.patient_id = p.patient_id
        LEFT JOIN bills b ON b.patient_id = o.patient_id AND b.pharmacist_id = o.pharmacist_id
        WHERE o.pharmacist_id=%s AND o.status != 'Completed'
        ORDER BY o.created_at DESC
    """, (pharmacist_id,))
    orders = cur.fetchall()

    # Get medicines
    cur.execute("SELECT * FROM medicines WHERE pharmacist_id=%s", (pharmacist_id,))
    medicines = cur.fetchall()

    # Completed orders
    cur.execute("""
        SELECT 
            o.order_id,
            o.patient_id,
            p.patient_name,
            o.delivery_address,
            o.status,
            'Paid' as payment_status
        FROM orders o
        JOIN patients p ON o.patient_id = p.patient_id
        WHERE o.pharmacist_id=%s AND o.status = 'Completed'
    """, (pharmacist_id,))
    completed_orders = cur.fetchall()

    conn.close()

    current_datetime = datetime.now().strftime("%A, %B %d, %Y - %I:%M %p")

    return render_template(
        "pharmacy_dashboard.html",
        orders=orders,
        completed_orders=completed_orders,
        medicines=medicines,
        prescription=None,
        items=[],
        profile=pharmacist_profile,
        current_datetime=current_datetime,
        today_revenue=sales_data['total_revenue'],
        today_bills_count=sales_data['bills_count'],
        today_medicines_sold=medicines_data['medicines_sold'],
        today_bills=today_bills
    )

# ============================================================
# FORGOT PASSWORD WITH OTP
# ============================================================
import requests

def send_otp_email(email, otp):
    try:
        # Method 1: Brevo (Free 300 emails/day)
        brevo_url = "https://api.brevo.com/v3/smtp/email"
        brevo_headers = {
            "api-key": "xkeysib-abcd1234567890abcdef1234567890abcdef1234567890abcdef1234567890-xyz",
            "Content-Type": "application/json"
        }
        
        brevo_data = {
            "sender": {"email": "medicalsystem2024@gmail.com", "name": "Medical System"},
            "to": [{"email": email}],
            "subject": "🏥 Password Reset OTP - Medical System",
            "textContent": f"""Dear User,

Your OTP for password reset is: {otp}

This OTP is valid for 10 minutes only.

Please do not share this OTP with anyone.

If you didn't request this password reset, please ignore this email.

Best regards,
Medical Management System Team"""
        }
        
        response = requests.post(brevo_url, headers=brevo_headers, json=brevo_data, timeout=10)
        if response.status_code == 201:
            return True
            
    except Exception as e:
        print(f"Brevo API failed: {e}")
    
    try:
        # Method 2: EmailJS (Free 200 emails/month)
        emailjs_url = "https://api.emailjs.com/api/v1.0/email/send"
        emailjs_data = {
            "service_id": "service_medical123",
            "template_id": "template_otp123",
            "user_id": "user_medical123",
            "template_params": {
                "to_email": email,
                "otp_code": otp,
                "user_name": "User"
            }
        }
        
        response = requests.post(emailjs_url, json=emailjs_data, timeout=10)
        if response.status_code == 200:
            return True
            
    except Exception as e:
        print(f"EmailJS failed: {e}")
    
    # All APIs failed
    return False

@app.route("/forgot_password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "GET":
        return render_template("forgot_password.html")

    email = request.form.get("email")
    role = request.form.get("role")

    conn = get_connection()
    cur = conn.cursor()

    # Check if email exists
    user_exists = False
    if role == "Doctor":
        cur.execute("SELECT doctor_id FROM doctors WHERE email=%s", (email,))
        user_exists = cur.fetchone() is not None
    elif role == "Patient":
        cur.execute("SELECT patient_id FROM patients WHERE email=%s", (email,))
        user_exists = cur.fetchone() is not None
    elif role == "Pharmacist":
        cur.execute("SELECT pharmacist_id FROM pharmacists WHERE email=%s", (email,))
        user_exists = cur.fetchone() is not None

    if not user_exists:
        flash("Email not found in selected role!", "danger")
        conn.close()
        return redirect("/forgot_password")

    # Generate OTP
    otp = random.randint(100000, 999999)
    session['reset_otp'] = otp
    session['reset_email'] = email
    session['reset_role'] = role

    # Try to send OTP email
    email_sent = send_otp_email(email, otp)
    
    if email_sent:
        flash("OTP sent to your email successfully!", "success")
    else:
        flash(f"Email service unavailable. Your OTP is: {otp} (Demo mode)", "info")
    
    conn.close()
    return redirect("/verify_otp")

@app.route("/verify_otp", methods=["GET", "POST"])
def verify_otp():
    if 'reset_otp' not in session:
        return redirect("/forgot_password")
        
    if request.method == "GET":
        return render_template("verify_otp.html")

    entered_otp = request.form.get("otp")
    new_password = request.form.get("new_password")
    confirm_password = request.form.get("confirm_password")

    if int(entered_otp) != session['reset_otp']:
        flash("Invalid OTP!", "danger")
        return redirect("/verify_otp")

    if new_password != confirm_password:
        flash("Passwords do not match!", "danger")
        return redirect("/verify_otp")

    # Update password
    conn = get_connection()
    cur = conn.cursor()

    email = session['reset_email']
    role = session['reset_role']

    if role == "Doctor":
        cur.execute("UPDATE doctors SET password=%s WHERE email=%s", (new_password, email))
    elif role == "Patient":
        cur.execute("UPDATE patients SET password=%s WHERE email=%s", (new_password, email))
    elif role == "Pharmacist":
        cur.execute("UPDATE pharmacists SET password=%s WHERE email=%s", (new_password, email))

    conn.commit()
    conn.close()

    # Clear session
    session.pop('reset_otp', None)
    session.pop('reset_email', None)
    session.pop('reset_role', None)

    flash("Password reset successfully! Please login.", "success")
    return redirect("/loginpage")

# ============================================================
# LOGIN
# ============================================================
@app.route("/loginpage", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    email = request.form.get("email").lower().strip()  # Convert to lowercase
    password = request.form.get("password")
    role = request.form.get("option")

    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    if role == "Doctor":
        cur.execute("""
            SELECT doctor_id, doctor_name
            FROM doctors WHERE email=%s AND password=%s
        """, (email, password))
        user = cur.fetchone()
        if user:
            session["doctor_id"] = user["doctor_id"]
            session["name"] = user["doctor_name"]
            flash(f"Welcome Dr. {user['doctor_name']}! Login successful.", "success")
            return redirect("/doctor_dashboard")

    if role == "Patient":
        cur.execute("""
            SELECT patient_id, patient_name
            FROM patients WHERE email=%s AND password=%s
        """, (email, password))
        user = cur.fetchone()
        if user:
            session["patient_id"] = user["patient_id"]
            session["name"] = user["patient_name"]
            flash(f"Welcome {user['patient_name']}! Login successful.", "success")
            return redirect("/patient_dashboard")

    if role == "Pharmacist":
        cur.execute("""
            SELECT pharmacist_id, pharmacist_name
            FROM pharmacists WHERE email=%s AND password=%s
        """, (email, password))
        user = cur.fetchone()
        if user:
            session["pharmacist_id"] = user["pharmacist_id"]
            session["name"] = user["pharmacist_name"]
            flash(f"Welcome {user['pharmacist_name']}! Login successful.", "success")
            return redirect("/pharmacy_dashboard")

    flash("Invalid login", "danger")
    return redirect("/loginpage")

# ============================================================
# LOGOUT
# ============================================================
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/loginpage")

# ============================================================
# RUN APP
# ============================================================
if __name__ == "__main__":
    port = int(os.getenv("PORT", 5555))
    debug = os.getenv("FLASK_ENV") != "production"
    app.run(debug=debug, host="0.0.0.0", port=port)
