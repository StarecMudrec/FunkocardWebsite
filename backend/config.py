import os
from hashlib import sha256
from sqlalchemy import create_engine
import pymysql
import asyncio
from telethon import TelegramClient
from telethon.tl.types import MessageMediaPhoto, MessageMediaDocument
import os
from datetime import datetime

# Telegram client setup (add to config.py)
TELEGRAM_API_ID = os.environ.get("TELEGRAM_API_ID")
TELEGRAM_API_HASH = os.environ.get("TELEGRAM_API_HASH")
CHANNEL_USERNAME = "funkocardsall"

class Config:
    # Configuration
    JWT_SECRET_KEY = "COOL"  # Replace with your actual secret key
    BOT_TOKEN_HASH = sha256(os.environ.get("BOT_TOKEN_HASH").encode())  # Replace with your actual token
    SQLALCHEMY_DATABASE_URI = "postgresql+psycopg2://postgres:postgres@localhost:5433/cards"  # SQLite database
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.environ.get("SECRET_KEY")
    TELEGRAM_API_ID = os.environ.get("TELEGRAM_API_ID")
    TELEGRAM_API_HASH = os.environ.get("TELEGRAM_API_HASH")
    CHANNEL_USERNAME = "funkocardsall"

    
    MYSQL_CONFIG = {
        'host': 'localhost',  # Changed from 'host.docker.internal'
        'user': 'bot',
        'password': 'xMdAUTiD',
        'database': 'database',
        'charset': 'utf8mb4',
        'cursorclass': pymysql.cursors.DictCursor,
        'port': 3306
    }
    
    # For SQLite over TCP proxy
    SQLITE_DB_PATH = "/app/db/offcardswood.db"  # Mounted path in container
    # SQLALCHEMY_BINDS = f"sqlite:///{SQLITE_DB_PATH}?mode=ro"  # Read-only mode
