import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'default_secret_key_expense_tracker_2026')
    
    DB_TYPE = os.getenv('DB_TYPE', 'mysql').lower()
    DB_USER = os.getenv('DB_USER', 'root')
    DB_PASSWORD = os.getenv('DB_PASSWORD', 'root')
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = os.getenv('DB_PORT', '3306')
    DB_NAME = os.getenv('DB_NAME', 'expense_tracker_db')
    SQLITE_DB_PATH = os.getenv('SQLITE_DB_PATH', 'expense_tracker.db')

    # Construct primary MySQL URI
    MYSQL_URI = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    SQLITE_URI = f"sqlite:///{SQLITE_DB_PATH}"

    # Determine default database URI
    if DB_TYPE == 'sqlite':
        SQLALCHEMY_DATABASE_URI = SQLITE_URI
    else:
        SQLALCHEMY_DATABASE_URI = MYSQL_URI

    SQLALCHEMY_TRACK_MODIFICATIONS = False
