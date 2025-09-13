import os
from hashlib import sha256
from sqlalchemy import create_engine


class Config:
    # Configuration
    JWT_SECRET_KEY = "COOL"  # Replace with your actual secret key
    BOT_TOKEN_HASH = sha256("7505659847:AAHkYpqOlCBlenERMIS3lDlefyrbC98eedk".encode())  # Replace with your actual token
    SQLALCHEMY_DATABASE_URI = "postgresql+psycopg2://postgres:postgres@db:5432/cards"  # SQLite database
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.environ.get("SECRET_KEY")
    
    # For SQLite over TCP proxy
    SQLITE_DB_PATH = "/app/db/offcardswood.db"  # Mounted path in container
    # SQLALCHEMY_BINDS = f"sqlite:///{SQLITE_DB_PATH}?mode=ro"  # Read-only mode