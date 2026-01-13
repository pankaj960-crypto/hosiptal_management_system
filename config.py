import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

def _get_database_uri():
    """Get database URI from environment or use default"""
    DATABASE_URL = os.environ.get("DATABASE_URL")
    if DATABASE_URL:
        # Render provides DATABASE_URL, convert mysql:// to mysql+mysqlconnector:// if needed
        if DATABASE_URL.startswith("mysql://"):
            return DATABASE_URL.replace("mysql://", "mysql+mysqlconnector://", 1)
        elif DATABASE_URL.startswith("postgres://"):
            # If using PostgreSQL on Render, convert to postgresql://
            return DATABASE_URL.replace("postgres://", "postgresql://", 1)
        else:
            return DATABASE_URL
    else:
        # Local development fallback
        return os.environ.get(
            "SQLALCHEMY_DATABASE_URI",
            "mysql+mysqlconnector://root:Pankaj%40449@localhost/hospital"
        )

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "change_this_secret")
    SQLALCHEMY_DATABASE_URI = _get_database_uri()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads', 'students')
    ONLINE_ADMISSION_UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads', 'online_admissions')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'pdf'}

    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = 'proy17869@gmail@gmail.com'   # change
    MAIL_PASSWORD = 'Pankaj@449'      # change



