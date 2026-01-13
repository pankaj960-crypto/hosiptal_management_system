from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    aadhar = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(120), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    mobile = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(120), nullable=True)
    neet = db.Column(db.String(120), nullable=True)
    course = db.Column(db.String(120), nullable=True)
    message = db.Column(db.String(120), nullable=True)
    password_hash = db.Column(db.String(200), nullable=False)
    medical_problem_number = db.Column(db.String(20), nullable=True)

    tokens = db.relationship("Token", backref="user", lazy=True)

class AdmissionInquiry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(30), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    neet_score = db.Column(db.String(50), nullable=False)
    course = db.Column(db.String(120), nullable=False)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Token(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    token_number = db.Column(db.String(50), nullable=False)
    doctor_name = db.Column(db.String(120), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default="waiting")  # waiting, completed
    diagnosis = db.Column(db.Text, nullable=True)
    prescription = db.Column(db.Text, nullable=True)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class JobApplication(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(30), nullable=False)
    job_position = db.Column(db.String(200), nullable=False)
    department = db.Column(db.String(100), nullable=True)
    experience = db.Column(db.String(100), nullable=True)
    resume_link = db.Column(db.String(500), nullable=True)
    cover_letter = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class ContactMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(30), nullable=True)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(50), unique=True, nullable=False)  # e.g., "STU2024001"
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(30), nullable=False)
    course = db.Column(db.String(100), nullable=False)  # MBBS, BDS, etc.
    year = db.Column(db.String(20), nullable=False)  # 1st Year, 2nd Year, etc.
    password_hash = db.Column(db.String(200), nullable=False)
    photo_path = db.Column(db.String(255), nullable=True)  # Path to student photo
    created_at = db.Column(db.DateTime, default=datetime.utcnow)



class OnlineAdmission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_course_category = db.Column(db.String(120), nullable=False)
    student_course_name = db.Column(db.String(120), nullable=False)
    student_name = db.Column(db.String(120), nullable=False)
    student_father_name = db.Column(db.String(120), nullable=False)
    student_mother_name = db.Column(db.String(120), nullable=False)
    student_gender = db.Column(db.String(20), nullable=False)
    student_mobile = db.Column(db.String(30), nullable=False)
    student_email = db.Column(db.String(120), nullable=False)
    student_state = db.Column(db.String(120), nullable=False)
    student_city = db.Column(db.String(120), nullable=False)
    student_address = db.Column(db.Text, nullable=False)
    student_dob = db.Column(db.Date, nullable=False)
    student_aadhar_number = db.Column(db.String(20), nullable=False)
    student_photo = db.Column(db.String(255), nullable=True)
    student_10th_marksheet = db.Column(db.String(255), nullable=True)
    student_12th_marksheet = db.Column(db.String(255), nullable=True)
    student_id_proof = db.Column(db.String(255), nullable=True)
    student_year1_year = db.Column(db.String(255), nullable=False)
    student_year1_stream = db.Column(db.String(255), nullable=False)
    student_year1_board = db.Column(db.String(255), nullable=False)
    student_year1_result = db.Column(db.String(255), nullable=False)
    student_year2_year = db.Column(db.String(255), nullable=False)
    student_year2_stream = db.Column(db.String(255), nullable=False)
    student_year2_board = db.Column(db.String(255), nullable=False)
    student_year2_result = db.Column(db.String(255), nullable=False)
    student_year3_year = db.Column(db.String(255), nullable=False)
    student_year3_stream = db.Column(db.String(255), nullable=False)
    student_year3_board = db.Column(db.String(255), nullable=False)
    student_year3_result = db.Column(db.String(255), nullable=False)
    student_created_at = db.Column(db.DateTime, default=datetime.utcnow)