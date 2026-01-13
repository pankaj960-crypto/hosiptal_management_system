# model relationships
#------------------------------------------

#-------------------------------------------

import os
import io
import random
from datetime import datetime, timedelta

from flask import (
    Flask, render_template, request, redirect, url_for, flash, session,Blueprint,
    send_file, send_from_directory
)
from config import Config
from models import db, User, Token, AdmissionInquiry, JobApplication, Student, ContactMessage, OnlineAdmission
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

# PDF
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
try:
    from PIL import Image
except ImportError:
    Image = None
from reportlab.lib.utils import ImageReader
from PIL import Image

# Twilio (optional) - imported lazily to avoid import errors
# Will be imported only when needed in send_otp_to_mobile function


app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

# Ensure upload directories exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['ONLINE_ADMISSION_UPLOAD_FOLDER'], exist_ok=True)

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

#----------------------

#--------------------------


# Doctor mapping
DOCTOR_MAP = {
    "101": "Dr. Rajesh Kumar (General Medicine)",
    "102": "Dr. Seema Singh (Pediatrics)",
    "103": "Dr. Anil Verma (Surgery)",
    "104": "Dr. Ritu Mishra (ENT)",
    "105": "Dr. Priya Gupta (Dermatology)",
    "106": "Dr. Ghulam Dastageer Ziyaur Rehman (Radiology)",
    "107": "DR KUNAL SINGH (Radiology)",
    "108": "DR SURABHI (Radiology)",
    "109": "DR PANKAJ KUMAR SAH (Radiology)",
    "110": "DR RAKESH KUMAR (Radiology)",
    "111": "DR VIJAY KUMAR YADAV (Radiology)",
    "112": "DR SAIF RAHMAN (Radiology)",
    "113": "DR PRABHAT KUMAR (Radiology)",
    "114": "DR NEHAL AHMAD (Radiology)",
    "115": "DR ANSHUPRIYA (Radiology)",
    "116": "DR PRABHAT KUMAR BHAGAT (Radiology)",
    "117": "DR ROSHAN ARA (Radiology)",
    "118": "Dr. Shoaib Alimohammed Fazlani (Radiology)",
    "119": "DR RAMESH KUMAR JAIN (Radiology)",
    "120": "DR DILIP KUMAR CHODHARY (Radiology)",
    "121": "Dr. Neha Singh (Pediatrics)",
    "122": "Dr. Taji Sarmad Mohiuddin (General Medicine)",
    "123": "Dr. Mohammad Musab Hanzala (General Surgery)",
    "124": "Dr Kumar Abhishek (Anaesthesiology)",
    "125": "Dr Tausif Azad (Anaesthesiology)",
    "126": "Dr. Atul Azad (Anaesthesiology)",
    "127": "Dr.Vinayashree B S (Anaesthesiology)",
    "128": "Dr. Ishuwan Mehta (Anaesthesiology)",
    "129": "Dr. Dharmendra Kumar (Anaesthesiology)",
    "130": "Dr. ANJALI JHA (Dermatology)",
    "131": "Dr. Abhishek Kumar (Psychiatry)",
    "132": "Dr. Shailendra Prasad Paswan (Orthopedics)",
    "133": "DR SHAHID HUSSAIN (Respiratory Medicine)"
}
DEFAULT_DOCTOR = "Dr. On-call (General)"

# ADMIN PASS (demo)
ADMIN_PASS = os.environ.get("ADMIN_PASS", "pass123")


# Twilio config (optional)



TWILIO_SID = os.environ.get("TWILIO_SID")
TWILIO_AUTH = os.environ.get("TWILIO_AUTH")
TWILIO_FROM = os.environ.get("TWILIO_FROM")  # e.g. +12025551234
DEV_SMS_BACKEND = os.environ.get("DEV_SMS_BACKEND","console")  # "console" or "twilio"
print(TWILIO_SID, TWILIO_AUTH, DEV_SMS_BACKEND)

# Migration function to add missing columns
def migrate_database():
    """Add missing columns to existing database if they don't exist"""
    from sqlalchemy import text, inspect
    
    with app.app_context():
        try:
            inspector = inspect(db.engine)
            table_names = inspector.get_table_names()
            
            # Migrate user table
            if 'user' in table_names:
                existing_columns = [col['name'] for col in inspector.get_columns('user')]
                columns_to_add = {
                    'email': 'VARCHAR(120)',
                    'neet': 'VARCHAR(120)',
                    'course': 'VARCHAR(120)',
                    'message': 'VARCHAR(120)'
                }
                
                for col_name, col_type in columns_to_add.items():
                    if col_name not in existing_columns:
                        try:
                            with db.engine.connect() as conn:
                                conn.execute(text(f'ALTER TABLE user ADD COLUMN {col_name} {col_type}'))
                                conn.commit()
                            print(f"Added column '{col_name}' to user table")
                        except Exception as e:
                            print(f"Error adding column '{col_name}': {e}")
            
            # Migrate student table
            if 'student' in table_names:
                existing_columns = [col['name'] for col in inspector.get_columns('student')]
                if 'photo_path' not in existing_columns:
                    try:
                        with db.engine.connect() as conn:
                            conn.execute(text('ALTER TABLE student ADD COLUMN photo_path VARCHAR(255)'))
                            conn.commit()
                        print("Added column 'photo_path' to student table")
                    except Exception as e:
                        print(f"Error adding column 'photo_path' to student table: {e}")
        except Exception as e:
            print(f"Migration error: {e}")

# Ensure DB exists and run migrations
with app.app_context():
    db.create_all()
    migrate_database()

def generate_token_number():
    today = datetime.utcnow().strftime("%Y-%m-%d")
    start_today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    count = Token.query.filter(Token.created_at >= start_today).count()
    return f"{today}-{count + 1:03d}"

def generate_student_id():
    """Generate unique student ID in format STUYYYYNNN"""
    year = datetime.utcnow().strftime("%Y")
    # Find the highest number for this year
    prefix = f"STU{year}"
    existing = Student.query.filter(Student.student_id.like(f"{prefix}%")).all()
    if existing:
        # Extract numbers and find max
        numbers = []
        for student in existing:
            try:
                num = int(student.student_id.replace(prefix, ""))
                numbers.append(num)
            except ValueError:
                continue
        next_num = max(numbers) + 1 if numbers else 1
    else:
        next_num = 1
    return f"{prefix}{next_num:03d}"
#----------------------------------------------otp---------------
def normalize_mobile(mobile: str) -> str:
    """Ensure E.164 format. Default India +91."""
    mobile = mobile.strip()

    # Already has +country code
    if mobile.startswith("+"):
        return mobile

    # Remove leading zero
    if mobile.startswith("0"):
        mobile = mobile[1:]

    # Default to India
    return "+91" + mobile

def create_and_store_otp(mobile: str):
    """Generate OTP, store in session, exp 5 min"""
    otp = f"{random.randint(100000, 999999)}"
    expiry = datetime.utcnow() + timedelta(minutes=5)

    session["otp_info"] = {
        "mobile": normalize_mobile(mobile),
        "otp": otp,
        "expires_at": expiry.isoformat(),
    }

    return otp, expiry


def send_otp_to_mobile(mobile: str, otp: str):
    """Send OTP using Twilio or fallback to console/dev mode"""
    mobile = normalize_mobile(mobile)

    # Debug visibility
    print("SEND OTP →", mobile, otp)

    # Check if 'to' and 'from' numbers are the same (Twilio restriction)
    if TWILIO_FROM and mobile == TWILIO_FROM:
        print(f"[DEV MODE] Cannot send SMS: 'To' and 'From' numbers are the same ({mobile})")
        print(f"[DEV MODE] OTP for {mobile} = {otp}")
        flash("SMS sending skipped (same number). Using DEV OTP instead.", "info")
        flash(f"TEST OTP (FALLBACK): {otp}", "info")
        return True, "Dev mode – same number restriction"

    # -------- DEV MODE: shows OTP on browser --------
    # DEV mode only prints to console — NO flash on page
    if DEV_SMS_BACKEND == "console" or not (TWILIO_SID and TWILIO_AUTH and TWILIO_FROM):
        print(f"[DEV MODE] OTP for {mobile} = {otp}")
        return True, "Dev mode – OTP printed to console"

    # -------- REAL TWILIO SMS ----------
    try:
        # Lazy import to avoid import errors if Twilio is corrupted
        try:
            from twilio.rest import Client as TwilioClient
        except ImportError as import_err:
            print(f"Twilio import error: {import_err}")
            print(f"[DEV MODE] OTP for {mobile} = {otp} (Twilio not available)")
            flash("SMS sending failed. Using DEV OTP instead.", "warning")
            flash(f"TEST OTP (FALLBACK): {otp}", "info")
            return False, f"Twilio import error: {import_err}"
        
        twilio_client = TwilioClient(TWILIO_SID, TWILIO_AUTH)

        message = twilio_client.messages.create(
            body=f"Your OTP for Madhubani Medical login is {otp}. It expires in 5 minutes.",
            from_=TWILIO_FROM,
            to=mobile,
        )

        print("Twilio SID:", message.sid)
        return True, f"Sent via Twilio {message.sid}"

    except Exception as e:
        error_str = str(e)
        print("Twilio ERROR:", e)
        print(f"[DEV MODE] OTP for {mobile} = {otp} (Twilio error)")
        
        # Check for specific Twilio errors
        if "cannot be the same" in error_str or "21266" in error_str:
            flash("SMS sending failed: Cannot send to the same number as sender. Using DEV OTP instead.", "warning")
        else:
            flash("SMS sending failed. Using DEV OTP instead.", "warning")
        
        flash(f"TEST OTP (FALLBACK): {otp}", "info")
        return False, f"Twilio error {e}"
# ---------------- ROUTES ----------------

@app.route("/")
def home():
    return render_template("home.html")
@app.route("/about")
def about():
    return render_template("about.html")
@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        phone = request.form.get("phone", "").strip()
        message = request.form.get("message", "").strip()

        if not name or not email or not message:
            flash("Name, email, and message are required.", "warning")
            return redirect(url_for("contact"))

        contact_msg = ContactMessage(
            name=name,
            email=email,
            phone=phone,
            message=message
        )
        db.session.add(contact_msg)
        db.session.commit()
        flash("Message sent successfully!", "success")
        return redirect(url_for("contact"))

    return render_template("contact.html")
@app.route("/academics")
def academics():
    return render_template("academics.html")
@app.route("/admission")
def admission():
    return render_template("admission.html")

@app.route("/career")
def career():
    return render_template("career.html")
@app.route("/faculty")
def faculty():
    return render_template("faculty.html")
@app.route("/gallery")
def gallery():
    return render_template("gallery.html")
@app.route("/hospitals")
def hospitals():
    return render_template("hospitals.html")
@app.route("/student")
def student():
    return render_template("student.html")

@app.route("/student/login", methods=["GET", "POST"])
def student_login():
    """Student login page"""
    if request.method == "POST":
        student_id = request.form.get("student_id").strip()
        password = request.form.get("password")
        student = Student.query.filter_by(student_id=student_id).first()
        if student and check_password_hash(student.password_hash, password):
            session["student_id"] = student.id
            session["student_name"] = student.name
            flash("Logged in successfully.", "success")
            return redirect(url_for("student_dashboard"))
        else:
            flash("Invalid student ID or password.", "danger")
    return render_template("student_login.html")

@app.route("/student/dashboard")
def student_dashboard():
    """Student dashboard - requires student login"""
    if "student_id" not in session:
        flash("Please login first.", "warning")
        return redirect(url_for("student_login"))
    
    student = Student.query.get(session["student_id"])
    return render_template("student_dashboard.html", student=student)

@app.route("/student/logout")
def student_logout():
    """Student logout"""
    session.pop("student_id", None)
    session.pop("student_name", None)
    flash("Logged out successfully.", "info")
    return redirect(url_for("student"))

@app.route("/students")
def students():
    return render_template("student_list.html")
@app.route("/results")
def results():
    return render_template("results.html")




@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        aadhar = request.form.get("aadhar").strip()
        name = request.form.get("name").strip()
        age = int(request.form.get("age"))
        mobile = request.form.get("mobile").strip()
        password = request.form.get("password")
        medical_problem_number = request.form.get("medical_problem_number").strip()

        if User.query.filter_by(aadhar=aadhar).first():
            flash("Aadhar already registered. Please login.", "warning")
            return redirect(url_for("login"))

        new_user = User(
            aadhar=aadhar,
            name=name,
            age=age,
            mobile=mobile,
            password_hash=generate_password_hash(password),
            medical_problem_number=medical_problem_number,
            email=None,
            neet=None,
            course=None,
            message=None
        )
        db.session.add(new_user)
        db.session.commit()
        flash("Registration successful. Please login.", "success")
        return redirect(url_for("login"))
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    # password login
    if request.method == "POST":
        aadhar = request.form.get("aadhar").strip()
        password = request.form.get("password")
        user = User.query.filter_by(aadhar=aadhar).first()
        if user and check_password_hash(user.password_hash, password):
            session["user_id"] = user.id
            session["user_name"] = user.name
            flash("Logged in successfully.", "success")
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid credentials.", "danger")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out.", "info")
    return redirect(url_for("home"))

@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        flash("Please login first.", "warning")
        return redirect(url_for("login"))
    user = User.query.get(session["user_id"])
    tokens = Token.query.filter_by(user_id=user.id).order_by(Token.created_at.desc()).all()
    return render_template("dashboard.html", user=user, tokens=tokens)

@app.route("/get-token", methods=["GET", "POST"])
def get_token():
    if "user_id" not in session:
        flash("Please login to get token.", "warning")
        return redirect(url_for("login"))
    user = User.query.get(session["user_id"])

    if request.method == "POST":
        aadhar = request.form.get("aadhar").strip()
        age = int(request.form.get("age"))
        mobile = request.form.get("mobile").strip()
        medical_problem_number = request.form.get("medical_problem_number").strip()

        if aadhar != user.aadhar:
            flash("Aadhar mismatch with logged in user.", "danger")
            return redirect(url_for("get_token"))

        doctor_name = DOCTOR_MAP.get(medical_problem_number, DEFAULT_DOCTOR)
        token_number = generate_token_number()
        token = Token(
            token_number=token_number,
            doctor_name=doctor_name,
            user_id=user.id
        )
        user.medical_problem_number = medical_problem_number
        user.age = age
        user.mobile = mobile

        db.session.add(token)
        db.session.commit()
        flash(f"Token generated: {token_number} with {doctor_name}", "success")
        return redirect(url_for("dashboard"))

    return render_template("get_token.html", user=user, doctor_map=DOCTOR_MAP)

@app.route("/record/<int:token_id>")
def view_record(token_id):
    if "user_id" not in session:
        flash("Please login to view record.", "warning")
        return redirect(url_for("login"))
    token = Token.query.get_or_404(token_id)
    if token.user_id != session["user_id"]:
        flash("Access denied.", "danger")
        return redirect(url_for("dashboard"))
    return render_template("view_record.html", token=token)

@app.route("/admin", methods=["GET", "POST"])
def admin_list():
    """Admin list page showing all tokens - requires admin password"""
    # Check if admin is authenticated in session
    if not session.get("admin_authenticated"):
        if request.method == "POST":
            admin_pwd = request.form.get("admin_pass")
            if admin_pwd == ADMIN_PASS:
                session["admin_authenticated"] = True
                flash("Admin access granted.", "success")
                return redirect(url_for("admin_list"))
            else:
                flash("Invalid admin password.", "danger")
        # Show password form
        return render_template("admin_login.html")
    
    # Admin is authenticated, show token list
    tokens = Token.query.order_by(Token.created_at.desc()).all()
    return render_template("admin_list.html", tokens=tokens)

@app.route("/admin/token/<int:token_id>/delete", methods=["POST"])
def admin_delete_token(token_id):
    """Delete a token record (admin only)"""
    if not session.get("admin_authenticated"):
        flash("Admin authentication required.", "danger")
        return redirect(url_for("admin_list"))
    token = Token.query.get_or_404(token_id)
    db.session.delete(token)
    db.session.commit()
    flash("Token deleted.", "info")
    return redirect(url_for("admin_list"))

@app.route("/admin/admissions", methods=["GET", "POST"])
def admin_admissions():
    """Admin page listing all admission inquiries - requires admin password"""
    if not session.get("admin_authenticated"):
        if request.method == "POST":
            admin_pwd = request.form.get("admin_pass")
            if admin_pwd == ADMIN_PASS:
                session["admin_authenticated"] = True
                flash("Admin access granted.", "success")
                return redirect(url_for("admin_admissions"))
            else:
                flash("Invalid admin password.", "danger")
        return render_template("admin_login.html")

    inquiries = AdmissionInquiry.query.order_by(AdmissionInquiry.created_at.desc()).all()
    return render_template("admin_admissions.html", inquiries=inquiries)

@app.route("/admin/contacts", methods=["GET", "POST"])
def admin_contacts():
    """Admin page listing all contact messages - requires admin password"""
    if not session.get("admin_authenticated"):
        if request.method == "POST":
            admin_pwd = request.form.get("admin_pass")
            if admin_pwd == ADMIN_PASS:
                session["admin_authenticated"] = True
                flash("Admin access granted.", "success")
                return redirect(url_for("admin_contacts"))
            else:
                flash("Invalid admin password.", "danger")
        return render_template("admin_login.html")

    messages = ContactMessage.query.order_by(ContactMessage.created_at.desc()).all()
    return render_template("admin_contacts.html", messages=messages)

@app.route("/admin/contact/<int:message_id>/delete", methods=["POST"])
def admin_delete_contact(message_id):
    """Delete a contact message (admin only)"""
    if not session.get("admin_authenticated"):
        flash("Admin authentication required.", "danger")
        return redirect(url_for("admin_contacts"))
    msg = ContactMessage.query.get_or_404(message_id)
    db.session.delete(msg)
    db.session.commit()
    flash("Contact message deleted.", "info")
    return redirect(url_for("admin_contacts"))

@app.route("/admin/admission/<int:inquiry_id>/delete", methods=["POST"])
def admin_delete_admission(inquiry_id):
    """Delete an admission inquiry (admin only)"""
    if not session.get("admin_authenticated"):
        flash("Admin authentication required.", "danger")
        return redirect(url_for("admin_admissions"))
    inquiry = AdmissionInquiry.query.get_or_404(inquiry_id)
    db.session.delete(inquiry)
    db.session.commit()
    flash("Admission inquiry deleted.", "info")
    return redirect(url_for("admin_admissions"))

@app.route("/job-apply", methods=["GET", "POST"])
def job_apply():
    """Job application form"""
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        phone = request.form.get("phone")
        job_position = request.form.get("job_position")
        department = request.form.get("department")
        experience = request.form.get("experience")
        resume_link = request.form.get("resume_link")
        cover_letter = request.form.get("cover_letter")

        application = JobApplication(
            name=name,
            email=email,
            phone=phone,
            job_position=job_position,
            department=department,
            experience=experience,
            resume_link=resume_link,
            cover_letter=cover_letter
        )
        db.session.add(application)
        db.session.commit()
        flash("Job application submitted successfully! We will contact you soon.", "success")
        return redirect(url_for("career"))
    
    # GET request - show form with job position pre-filled if provided
    job_position = request.args.get("position", "")
    return render_template("job_apply.html", job_position=job_position)

@app.route("/admin/jobs", methods=["GET", "POST"])
def admin_jobs():
    """Admin view for job applications - requires admin password"""
    if not session.get("admin_authenticated"):
        if request.method == "POST":
            admin_pwd = request.form.get("admin_pass")
            if admin_pwd == ADMIN_PASS:
                session["admin_authenticated"] = True
                flash("Admin access granted.", "success")
                return redirect(url_for("admin_jobs"))
            else:
                flash("Invalid admin password.", "danger")
        return render_template("admin_login.html")
    
    applications = JobApplication.query.order_by(JobApplication.created_at.desc()).all()
    return render_template("admin_jobs.html", applications=applications)

@app.route("/admin/job/<int:application_id>/delete", methods=["POST"])
def admin_delete_job(application_id):
    """Delete a job application (admin only)"""
    if not session.get("admin_authenticated"):
        flash("Admin authentication required.", "danger")
        return redirect(url_for("admin_jobs"))
    application = JobApplication.query.get_or_404(application_id)
    db.session.delete(application)
    db.session.commit()
    flash("Job application deleted.", "info")
    return redirect(url_for("admin_jobs"))

@app.route("/admin/students", methods=["GET", "POST"])
def admin_students():
    """Admin page listing all student registrations - requires admin password"""
    if not session.get("admin_authenticated"):
        if request.method == "POST":
            admin_pwd = request.form.get("admin_pass")
            if admin_pwd == ADMIN_PASS:
                session["admin_authenticated"] = True
                flash("Admin access granted.", "success")
                return redirect(url_for("admin_students"))
            else:
                flash("Invalid admin password.", "danger")
        return render_template("admin_login.html")

    students = Student.query.order_by(Student.created_at.desc()).all()
    return render_template("admin_students.html", students=students)

@app.route("/admin/students/register", methods=["GET", "POST"])
def admin_register_student():
    """Admin page to register a new student - requires admin password"""
    if not session.get("admin_authenticated"):
        if request.method == "POST":
            admin_pwd = request.form.get("admin_pass")
            if admin_pwd == ADMIN_PASS:
                session["admin_authenticated"] = True
                flash("Admin access granted.", "success")
                return redirect(url_for("admin_register_student"))
            else:
                flash("Invalid admin password.", "danger")
        return render_template("admin_login.html")

    if request.method == "POST":
        name = request.form.get("name").strip()
        email = request.form.get("email").strip()
        phone = request.form.get("phone").strip()
        course = request.form.get("course").strip()
        year = request.form.get("year").strip()
        password = request.form.get("password")
        student_id_input = request.form.get("student_id", "").strip()

        # Validate required fields
        if not all([name, email, phone, course, year, password]):
            flash("All fields are required.", "danger")
            return redirect(url_for("admin_register_student"))

        # Check if email already exists
        if Student.query.filter_by(email=email).first():
            flash("Email already registered.", "danger")
            return redirect(url_for("admin_register_student"))

        # Check if phone already exists
        if Student.query.filter_by(phone=phone).first():
            flash("Phone number already registered.", "danger")
            return redirect(url_for("admin_register_student"))

        # Generate or use provided student ID
        if student_id_input:
            # Check if provided student ID already exists
            if Student.query.filter_by(student_id=student_id_input).first():
                flash("Student ID already exists. Please use a different one.", "danger")
                return redirect(url_for("admin_register_student"))
            student_id = student_id_input
        else:
            student_id = generate_student_id()

        # Handle photo upload
        photo_path = None
        if 'photo' in request.files:
            file = request.files['photo']
            if file and file.filename != '' and allowed_file(file.filename):
                # Generate secure filename using student_id
                file_ext = file.filename.rsplit('.', 1)[1].lower()
                filename = f"{student_id}.{file_ext}"
                filename = secure_filename(filename)
                photo_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(photo_path)
                # Store relative path for database
                photo_path = f"uploads/students/{filename}"
            elif file and file.filename != '':
                flash("Invalid file type. Allowed types: PNG, JPG, JPEG, GIF, WEBP", "danger")
                return redirect(url_for("admin_register_student"))

        # Create new student
        new_student = Student(
            student_id=student_id,
            name=name,
            email=email,
            phone=phone,
            course=course,
            year=year,
            password_hash=generate_password_hash(password),
            photo_path=photo_path
        )
        db.session.add(new_student)
        db.session.commit()
        flash(f"Student registered successfully! Student ID: {student_id}", "success")
        return redirect(url_for("admin_students"))

    return render_template("admin_register_student.html")

@app.route("/admin/students/<int:student_id>/update", methods=["GET", "POST"])
def admin_update_student(student_id):
    """Admin page to update student information - requires admin password"""
    if not session.get("admin_authenticated"):
        if request.method == "POST":
            admin_pwd = request.form.get("admin_pass")
            if admin_pwd == ADMIN_PASS:
                session["admin_authenticated"] = True
                flash("Admin access granted.", "success")
                return redirect(url_for("admin_update_student", student_id=student_id))
            else:
                flash("Invalid admin password.", "danger")
        return render_template("admin_login.html")

    student = Student.query.get_or_404(student_id)

    if request.method == "POST":
        name = request.form.get("name").strip()
        email = request.form.get("email").strip()
        phone = request.form.get("phone").strip()
        course = request.form.get("course").strip()
        year = request.form.get("year").strip()
        password = request.form.get("password", "").strip()
        student_id_input = request.form.get("student_id", "").strip()

        # Validate required fields
        if not all([name, email, phone, course, year]):
            flash("All fields except password are required.", "danger")
            return redirect(url_for("admin_update_student", student_id=student_id))

        # Check if email already exists (excluding current student)
        existing_email = Student.query.filter_by(email=email).first()
        if existing_email and existing_email.id != student.id:
            flash("Email already registered to another student.", "danger")
            return redirect(url_for("admin_update_student", student_id=student_id))

        # Check if phone already exists (excluding current student)
        existing_phone = Student.query.filter_by(phone=phone).first()
        if existing_phone and existing_phone.id != student.id:
            flash("Phone number already registered to another student.", "danger")
            return redirect(url_for("admin_update_student", student_id=student_id))

        # Update student ID if provided and different
        if student_id_input and student_id_input != student.student_id:
            # Check if provided student ID already exists
            if Student.query.filter_by(student_id=student_id_input).first():
                flash("Student ID already exists. Please use a different one.", "danger")
                return redirect(url_for("admin_update_student", student_id=student_id))
            student.student_id = student_id_input

        # Update basic fields
        student.name = name
        student.email = email
        student.phone = phone
        student.course = course
        student.year = year

        # Update password if provided
        if password:
            student.password_hash = generate_password_hash(password)

        # Handle photo upload
        if 'photo' in request.files:
            file = request.files['photo']
            if file and file.filename != '' and allowed_file(file.filename):
                # Delete old photo if exists
                if student.photo_path:
                    # Extract filename from path (e.g., "uploads/students/STU2024001.jpg" -> "STU2024001.jpg")
                    old_filename = os.path.basename(student.photo_path)
                    old_photo_path = os.path.join(app.config['UPLOAD_FOLDER'], old_filename)
                    if os.path.exists(old_photo_path):
                        try:
                            os.remove(old_photo_path)
                        except Exception as e:
                            print(f"Error deleting old photo: {e}")

                # Generate secure filename using student_id
                file_ext = file.filename.rsplit('.', 1)[1].lower()
                filename = f"{student.student_id}.{file_ext}"
                filename = secure_filename(filename)
                photo_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(photo_path)
                # Store relative path for database
                student.photo_path = f"uploads/students/{filename}"
            elif file and file.filename != '':
                flash("Invalid file type. Allowed types: PNG, JPG, JPEG, GIF, WEBP", "danger")
                return redirect(url_for("admin_update_student", student_id=student_id))

        db.session.commit()
        flash(f"Student updated successfully! Student ID: {student.student_id}", "success")
        return redirect(url_for("admin_students"))

    return render_template("admin_update_student.html", student=student)

@app.route("/static/uploads/students/<filename>")
def student_photo(filename):
    """Serve student photos"""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route("/admin/student/<int:student_id>/delete", methods=["POST"])
def admin_delete_student(student_id):
    """Delete a student registration (admin only)"""
    if not session.get("admin_authenticated"):
        flash("Admin authentication required.", "danger")
        return redirect(url_for("admin_students"))
    student = Student.query.get_or_404(student_id)
    db.session.delete(student)
    db.session.commit()
    flash("Student registration deleted.", "info")
    return redirect(url_for("admin_students"))

@app.route("/admin/logout")
def admin_logout():
    """Logout from admin session"""
    session.pop("admin_authenticated", None)
    flash("Admin session ended.", "info")
    return redirect(url_for("home"))

@app.route("/admin/update/<int:token_id>", methods=["GET", "POST"])
def admin_update(token_id):
    token = Token.query.get_or_404(token_id)

    if request.method == "POST":
        admin_pwd = request.form.get("admin_pass")
        if admin_pwd != ADMIN_PASS:
            flash("Invalid admin password.", "danger")
            return redirect(url_for("admin_update", token_id=token_id))
        diagnosis = request.form.get("diagnosis")
        prescription = request.form.get("prescription")
        token.diagnosis = diagnosis
        token.prescription = prescription
        token.status = "completed"
        db.session.commit()
        flash("Record updated. User can now view diagnosis & prescription.", "success")
        return redirect(url_for("admin_update", token_id=token_id))

    return render_template("admin_update.html", token=token)

# ---------- OTP Login ----------

@app.route("/otp-login", methods=["GET", "POST"])
def otp_login():
    if request.method == "POST":
        mobile = request.form.get("mobile").strip()
        user = User.query.filter_by(mobile=mobile).first()
        if not user:
            flash("No user found with that mobile number. Please register first.", "warning")
            return redirect(url_for("register"))

        otp, expiry = create_and_store_otp(mobile)
        ok, info = send_otp_to_mobile(mobile, otp)
        if ok:
            flash(f"OTP sent to {mobile}. It will expire in 5 minutes. ({info})", "info")
            return redirect(url_for("otp_verify"))
        else:
            flash(f"Failed to send OTP: {info}", "danger")
    return render_template("otp_login.html")

@app.route("/otp-verify", methods=["GET", "POST"])
def otp_verify():
    otp_info = session.get('otp_info')
    if not otp_info:
        flash("No OTP session found. Please request OTP again.", "warning")
        return redirect(url_for("otp_login"))

    if request.method == "POST":
        entered = request.form.get("otp").strip()
        stored = otp_info.get('otp')
        expires_at = datetime.fromisoformat(otp_info.get('expires_at'))
        mobile = otp_info.get('mobile')

        if datetime.utcnow() > expires_at:
            session.pop('otp_info', None)
            flash("OTP expired. Please request again.", "danger")
            return redirect(url_for("otp_login"))

        if entered == stored:
            user = User.query.filter_by(mobile=mobile).first()
            if not user:
                flash("User not found for this mobile.", "danger")
                return redirect(url_for("register"))
            session.pop('otp_info', None)
            session['user_id'] = user.id
            session['user_name'] = user.name
            flash("Logged in via OTP.", "success")
            return redirect(url_for("dashboard"))
        else:
            flash("Incorrect OTP. Try again.", "danger")

    return render_template("otp_verify.html")
# ---------- PDF Prescription ----------

@app.route("/prescription/<int:token_id>/pdf")
def prescription_pdf(token_id):
    token = Token.query.get_or_404(token_id)

    if "user_id" not in session or session["user_id"] != token.user_id:
        flash("Access denied for PDF. Please login as the patient.", "danger")
        return redirect(url_for("login"))

    if token.status != "completed":
        flash("Prescription not available until appointment is completed by doctor.", "warning")
        return redirect(url_for("view_record", token_id=token_id))

    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    p.setFont("Helvetica-Bold", 16)
    p.drawString(40, height - 60, "Madhubani Medical College & Hospital")
    p.setFont("Helvetica", 10)
    p.drawString(40, height - 78, "Madhubani, Bihar | Hospital Reception: 9570142222")

    p.setFont("Helvetica-Bold", 12)
    p.drawString(40, height - 110, f"Patient: {token.user.name} (Aadhar: {token.user.aadhar})")
    p.setFont("Helvetica", 11)
    p.drawString(40, height - 128, f"Age: {token.user.age} • Mobile: {token.user.mobile}")
    p.drawString(40, height - 144, f"Token: {token.token_number} • Doctor: {token.doctor_name}")
    p.drawString(40, height - 160, f"Date: {token.created_at.strftime('%d-%m-%Y %H:%M')}")

    p.setFont("Helvetica-Bold", 12)
    p.drawString(40, height - 190, "Diagnosis:")
    p.setFont("Helvetica", 11)
    y = height - 208
    for line in (token.diagnosis or "No diagnosis provided.").split("\n"):
        p.drawString(45, y, line)
        y -= 16

    y -= 8
    p.setFont("Helvetica-Bold", 12)
    p.drawString(40, y, "Prescription / Medicines:")
    y -= 18
    p.setFont("Helvetica", 11)
    for line in (token.prescription or "No prescription provided.").split("\n"):
        p.drawString(45, y, line)
        y -= 16
        if y < 80:
            p.showPage()
            y = height - 80

    if y < 160:
        p.showPage()
        y = height - 80
    p.setFont("Helvetica", 10)
    p.drawString(40, 60, "Doctor Signature: ______________________")
    p.drawString(40, 46, "Contact: Hospital Reception 9570142222")

    p.showPage()
    p.save()
    buffer.seek(0)

    return send_file(buffer, as_attachment=True,
                     download_name=f"prescription_{token.token_number}.pdf",
                     mimetype='application/pdf')

# --------------- helpers used earlier ----------------

def create_and_store_otp(mobile: str):
    # generate 6-digit OTP
    otp = str(random.randint(100000, 999999))

    # expiry time 5 minutes from now
    expires_at = datetime.utcnow() + timedelta(minutes=5)

    # store in session
    session['otp_info'] = {
        "mobile": mobile,
        "otp": otp,
        "expires_at": expires_at.isoformat()
    }

    return otp, expires_at



@app.route("/admission_inquire", methods=["GET", "POST"])
def admission_inquire():
    """Collect admission inquiries and store separately from users."""
    if request.method == "POST":
        name = request.form.get("name")
        phone = request.form.get("phone")
        email = request.form.get("email")
        neet_score = request.form.get("neet_score")
        course = request.form.get("course")
        message = request.form.get("message")

        inquiry = AdmissionInquiry(
            name=name,
            phone=phone,
            email=email,
            neet_score=neet_score,
            course=course,
            message=message,
        )
        db.session.add(inquiry)
        db.session.commit()
        flash("Admission inquiry submitted successfully.", "success")
        return redirect(url_for("admission_inquire"))

    return render_template("admission_inquiri.html")





@app.route("/online_admission", methods=["GET", "POST"])
def online_admission():
    if request.method == "POST":
        student_course_category = request.form.get("student_course_category")
        student_course_name = request.form.get("student_course_name")
        student_name = request.form.get("student_name")
        student_father_name = request.form.get("student_father_name")
        student_mother_name = request.form.get("student_mother_name")
        student_gender = request.form.get("student_gender")
        student_mobile = request.form.get("student_mobile")
        student_email = request.form.get("student_email")
        student_state = request.form.get("student_state")
        student_city = request.form.get("student_city")
        student_address = request.form.get("student_address")
        student_dob_raw = request.form.get("student_dob")
        student_aadhar_number = request.form.get("student_aadhar_number")

        # Handle file uploads
        upload_folder = app.config['ONLINE_ADMISSION_UPLOAD_FOLDER']
        # Ensure upload folder exists
        os.makedirs(upload_folder, exist_ok=True)
        
        # Debug: Print all files received
        print(f"Files received: {list(request.files.keys())}")
        for key in request.files:
            file = request.files[key]
            print(f"  {key}: filename='{file.filename}', content_type='{file.content_type}'")
        
        # Use aadhar number for unique prefix, or generate one if not available
        aadhar_prefix = student_aadhar_number[:4] if student_aadhar_number and len(student_aadhar_number) >= 4 else "0000"
        student_id_prefix = f"ADM{datetime.utcnow().strftime('%Y%m%d')}_{aadhar_prefix}"
        
        student_photo = None
        student_10th_marksheet = None
        student_12th_marksheet = None
        student_id_proof = None

        # Handle photo upload
        if 'student_photo' in request.files:
            file = request.files['student_photo']
            if file and file.filename and file.filename.strip() != '':
                try:
                    file_ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else 'jpg'
                    filename = f"{student_id_prefix}_photo.{file_ext}"
                    filename = secure_filename(filename)
                    filepath = os.path.join(upload_folder, filename)
                    file.save(filepath)
                    if os.path.exists(filepath):
                        student_photo = f"uploads/online_admissions/{filename}"
                        print(f"Photo saved: {student_photo}")
                except Exception as e:
                    print(f"Error saving photo: {e}")
                    flash(f"Error saving photo: {str(e)}", "warning")

        # Handle 10th marksheet upload
        if 'student_10th_marksheet' in request.files:
            file = request.files['student_10th_marksheet']
            if file and file.filename and file.filename.strip() != '':
                try:
                    file_ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else 'pdf'
                    filename = f"{student_id_prefix}_10th.{file_ext}"
                    filename = secure_filename(filename)
                    filepath = os.path.join(upload_folder, filename)
                    file.save(filepath)
                    if os.path.exists(filepath):
                        student_10th_marksheet = f"uploads/online_admissions/{filename}"
                        print(f"10th marksheet saved: {student_10th_marksheet}")
                except Exception as e:
                    print(f"Error saving 10th marksheet: {e}")
                    flash(f"Error saving 10th marksheet: {str(e)}", "warning")

        # Handle 12th marksheet upload
        if 'student_12th_marksheet' in request.files:
            file = request.files['student_12th_marksheet']
            if file and file.filename and file.filename.strip() != '':
                try:
                    file_ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else 'pdf'
                    filename = f"{student_id_prefix}_12th.{file_ext}"
                    filename = secure_filename(filename)
                    filepath = os.path.join(upload_folder, filename)
                    file.save(filepath)
                    if os.path.exists(filepath):
                        student_12th_marksheet = f"uploads/online_admissions/{filename}"
                        print(f"12th marksheet saved: {student_12th_marksheet}")
                except Exception as e:
                    print(f"Error saving 12th marksheet: {e}")
                    flash(f"Error saving 12th marksheet: {str(e)}", "warning")

        # Handle ID proof upload
        if 'student_id_proof' in request.files:
            file = request.files['student_id_proof']
            if file and file.filename and file.filename.strip() != '':
                try:
                    file_ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else 'pdf'
                    filename = f"{student_id_prefix}_idproof.{file_ext}"
                    filename = secure_filename(filename)
                    filepath = os.path.join(upload_folder, filename)
                    file.save(filepath)
                    if os.path.exists(filepath):
                        student_id_proof = f"uploads/online_admissions/{filename}"
                        print(f"ID proof saved: {student_id_proof}")
                except Exception as e:
                    print(f"Error saving ID proof: {e}")
                    flash(f"Error saving ID proof: {str(e)}", "warning")

        student_year1_year = request.form.get("student_year1_year")
        student_year1_stream = request.form.get("student_year1_stream")
        student_year1_board = request.form.get("student_year1_board")
        student_year1_result = request.form.get("student_year1_result")
        student_year2_year = request.form.get("student_year2_year")
        student_year2_stream = request.form.get("student_year2_stream")
        student_year2_board = request.form.get("student_year2_board")
        student_year2_result = request.form.get("student_year2_result")
        student_year3_year = request.form.get("student_year3_year")
        student_year3_stream = request.form.get("student_year3_stream")
        student_year3_board = request.form.get("student_year3_board")
        student_year3_result = request.form.get("student_year3_result")

        # Parse DOB to date
        student_dob = None
        if student_dob_raw:
            try:
                student_dob = datetime.strptime(student_dob_raw, "%Y-%m-%d").date()
            except ValueError:
                flash("Invalid date format for DOB.", "danger")
                return redirect(url_for("online_admission"))

        student_created_at = datetime.utcnow()
        student = OnlineAdmission(
            student_course_category=student_course_category,
            student_course_name=student_course_name,
            student_name=student_name,
            student_father_name=student_father_name,
            student_mother_name=student_mother_name,
            student_gender=student_gender,
            student_mobile=student_mobile,
            student_email=student_email,
            student_state=student_state,
            student_city=student_city,
            student_address=student_address,
            student_dob=student_dob,
            student_aadhar_number=student_aadhar_number,
            student_photo=student_photo,
            student_10th_marksheet=student_10th_marksheet,
            student_12th_marksheet=student_12th_marksheet,
            student_id_proof=student_id_proof,
            student_year1_year=student_year1_year,
            student_year1_stream=student_year1_stream,
            student_year1_board=student_year1_board,
            student_year1_result=student_year1_result,
            student_year2_year=student_year2_year,
            student_year2_stream=student_year2_stream,
            student_year2_board=student_year2_board,
            student_year2_result=student_year2_result,
            student_year3_year=student_year3_year,
            student_year3_stream=student_year3_stream,
            student_year3_board=student_year3_board,
            student_year3_result=student_year3_result,
            student_created_at=student_created_at
        )
        db.session.add(student)
        db.session.commit()
        flash("Online admission submitted successfully.", "success")
        return redirect(url_for("online_admission"))
    return render_template("online_admission.html")

@app.route("/admin/online_admissions", methods=["GET", "POST"])
def admin_online_admissions():
    """Admin view for online admissions - requires admin password"""
    if not session.get("admin_authenticated"):
        if request.method == "POST":
            admin_pwd = request.form.get("admin_pass")
            if admin_pwd == ADMIN_PASS:
                session["admin_authenticated"] = True
                flash("Admin access granted.", "success")
                return redirect(url_for("admin_online_admissions"))
            else:
                flash("Invalid admin password.", "danger")
        return render_template("admin_login.html")

    admissions = OnlineAdmission.query.order_by(OnlineAdmission.student_created_at.desc()).all()
    return render_template("admin_online_admissions.html", admissions=admissions)

@app.route("/admin/online_admission/<int:admission_id>/delete", methods=["POST"])
def admin_delete_online_admission(admission_id):
    """Delete an online admission (admin only)"""
    if not session.get("admin_authenticated"):
        flash("Admin authentication required.", "danger")
        return redirect(url_for("admin_online_admissions"))
    admission = OnlineAdmission.query.get_or_404(admission_id)
    db.session.delete(admission)
    db.session.commit()
    flash("Online admission deleted.", "info")
    return redirect(url_for("admin_online_admissions"))

@app.route("/admin/online_admission/<int:admission_id>/pdf")
def admin_online_admission_pdf(admission_id):
    """Generate PDF for online admission with all data and documents"""
    if not session.get("admin_authenticated"):
        flash("Admin authentication required.", "danger")
        return redirect(url_for("admin_online_admissions"))
    
    admission = OnlineAdmission.query.get_or_404(admission_id)
    
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    
    # Header
    p.setFont("Helvetica-Bold", 18)
    p.drawString(40, height - 40, "Madhubani Medical College & Hospital")
    p.setFont("Helvetica", 12)
    p.drawString(40, height - 60, "Online Admission Application Form")
    p.drawString(40, height - 75, f"Application Date: {admission.student_created_at.strftime('%d-%m-%Y %H:%M')}")
    
    y = height - 100
    
    # Student Photo
    if admission.student_photo and Image:
        try:
            from config import BASE_DIR
            photo_path = os.path.join(BASE_DIR, 'static', admission.student_photo)
            if os.path.exists(photo_path):
                img = Image.open(photo_path)
                img.thumbnail((100, 100))
                p.drawImage(ImageReader(img), width - 150, y - 100, width=100, height=100)
        except Exception as e:
            print(f"Error loading photo: {e}")
            p.drawString(width - 150, y - 100, "[Photo]")
    
    # Personal Information
    p.setFont("Helvetica-Bold", 14)
    p.drawString(40, y, "Personal Information")
    y -= 25
    p.setFont("Helvetica", 11)
    
    info_lines = [
        f"Name: {admission.student_name}",
        f"Father's Name: {admission.student_father_name}",
        f"Mother's Name: {admission.student_mother_name}",
        f"Gender: {admission.student_gender}",
        f"Date of Birth: {admission.student_dob.strftime('%d-%m-%Y') if admission.student_dob else 'N/A'}",
        f"Aadhar Number: {admission.student_aadhar_number}",
        f"Mobile: {admission.student_mobile}",
        f"Email: {admission.student_email}",
    ]
    
    for line in info_lines:
        p.drawString(45, y, line)
        y -= 18
    
    # Address Information
    y -= 10
    if y < 150:
        p.showPage()
        y = height - 40
    p.setFont("Helvetica-Bold", 14)
    p.drawString(40, y, "Address Information")
    y -= 25
    p.setFont("Helvetica", 11)
    
    address_lines = [
        f"State: {admission.student_state}",
        f"City: {admission.student_city}",
        f"Address: {admission.student_address}",
    ]
    
    for line in address_lines:
        p.drawString(45, y, line)
        y -= 18
    
    # Course Information
    y -= 10
    if y < 150:
        p.showPage()
        y = height - 40
    p.setFont("Helvetica-Bold", 14)
    p.drawString(40, y, "Course Information")
    y -= 25
    p.setFont("Helvetica", 11)
    
    course_lines = [
        f"Course Category: {admission.student_course_category}",
        f"Course Name: {admission.student_course_name}",
    ]
    
    for line in course_lines:
        p.drawString(45, y, line)
        y -= 18
    
    # Academic Year Information
    y -= 10
    if y < 150:
        p.showPage()
        y = height - 40
    p.setFont("Helvetica-Bold", 14)
    p.drawString(40, y, "Academic Year Details")
    y -= 25
    p.setFont("Helvetica", 11)
    
    academic_data = [
        ("10th", admission.student_year1_year, admission.student_year1_stream, 
         admission.student_year1_board, admission.student_year1_result),
        ("12th", admission.student_year2_year, admission.student_year2_stream, 
         admission.student_year2_board, admission.student_year2_result),
        ("Other", admission.student_year3_year, admission.student_year3_stream, 
         admission.student_year3_board, admission.student_year3_result),
    ]
    
    for year_label, year_val, stream, board, result in academic_data:
        if y < 100:
            p.showPage()
            y = height - 40
        p.drawString(45, y, f"{year_label}: Year={year_val}, Stream={stream}, Board={board}, Result={result}")
        y -= 18
    
    # Documents Section
    y -= 20
    if y < 200:
        p.showPage()
        y = height - 40
    
    p.setFont("Helvetica-Bold", 14)
    p.drawString(40, y, "Attached Documents")
    y -= 25
    p.setFont("Helvetica", 10)
    
    # Check and list documents
    documents = [
        ("Student Photo", admission.student_photo),
        ("10th Marksheet", admission.student_10th_marksheet),
        ("12th Marksheet", admission.student_12th_marksheet),
        ("ID Proof", admission.student_id_proof),
    ]
    
    for doc_name, doc_path in documents:
        if y < 80:
            p.showPage()
            y = height - 40
        if doc_path:
            p.drawString(45, y, f"{doc_name}: Attached ({doc_path.split('/')[-1]})")
        else:
            p.drawString(45, y, f"{doc_name}: Not provided")
        y -= 15
    
    # Footer
    p.setFont("Helvetica", 10)
    p.drawString(40, 60, "This is a system-generated document.")
    p.drawString(40, 46, "Madhubani Medical College & Hospital | Contact: 06276-296222")
    
    p.showPage()
    p.save()
    buffer.seek(0)
    
    return send_file(buffer, as_attachment=True,
                     download_name=f"admission_{admission.student_name.replace(' ', '_')}_{admission.id}.pdf",
                     mimetype='application/pdf')

@app.route("/static/uploads/online_admissions/<filename>")
def online_admission_file(filename):
    """Serve online admission uploaded files"""
    return send_from_directory(app.config['ONLINE_ADMISSION_UPLOAD_FOLDER'], filename)

#--------------------------------------------------

#----------- Run ----------

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)
