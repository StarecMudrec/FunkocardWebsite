import os
import hmac
from hashlib import sha256
import uuid  # For generating unique tokens

from flask import Flask, render_template, request, redirect, url_for, make_response, jsonify, send_from_directory, session
from flask_migrate import Migrate
import requests  # Import the requests library
# import jwt
from joserfc.errors import JoseError
import logging
from flask_sqlalchemy import SQLAlchemy  # Database integration
from models import db, AuthToken, Card, Season, Comment, AllowedUser
from config import Config
from sqlalchemy import create_engine, select, and_, text
from sqlalchemy.orm import Session, sessionmaker
from sqlite3 import connect

import sqlite3
from datetime import datetime
import asyncio
from telethon import TelegramClient
from telethon.tl.types import MessageMediaPhoto, MessageMediaDocument

import pymysql

app = Flask(__name__)
app.config.from_object(Config)

# Configure logging
logging.basicConfig(level=logging.DEBUG)

db.init_app(app)

migrate = Migrate(app, db)

# Create the database tables
with app.app_context():
    db.create_all()



# Add this after your existing imports and before route definitions

def init_upload_dates_db():
    """Initialize SQLite database for storing upload dates"""
    try:
        conn = sqlite3.connect('card_upload_dates.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS card_upload_dates (
                card_id INTEGER PRIMARY KEY,
                message_id INTEGER,
                upload_date TIMESTAMP,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create index for faster lookups
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_card_id ON card_upload_dates(card_id)
        ''')
        
        conn.commit()
        logging.info("SQLite upload dates database initialized successfully")
        conn.close()
    except Exception as e:
        logging.error(f"Error initializing upload dates database: {e}")


init_upload_dates_db()

def get_upload_dates_conn():
    """Get SQLite database connection with error handling"""
    try:
        return sqlite3.connect('card_upload_dates.db')
    except Exception as e:
        logging.error(f"Error connecting to upload dates database: {e}")
        # Try to reinitialize the database
        init_upload_dates_db()
        return sqlite3.connect('card_upload_dates.db')

def store_upload_date(card_id, message_id, upload_date):
    """Store upload date in SQLite database"""
    conn = get_upload_dates_conn()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT OR REPLACE INTO card_upload_dates 
            (card_id, message_id, upload_date, last_updated) 
            VALUES (?, ?, ?, ?)
        ''', (card_id, message_id, upload_date, datetime.now()))
        
        conn.commit()
        logging.debug(f"Stored upload date for card {card_id}")
        return True
    except Exception as e:
        logging.error(f"Error storing upload date: {e}")
        return False
    finally:
        conn.close()

def get_upload_date(card_id):
    """Get upload date from SQLite database"""
    conn = get_upload_dates_conn()
    cursor = conn.cursor()
    
    try:
        # Check if table exists, create if not
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='card_upload_dates'")
        if not cursor.fetchone():
            init_upload_dates_db()
        
        cursor.execute(
            'SELECT upload_date FROM card_upload_dates WHERE card_id = ?', 
            (card_id,)
        )
        result = cursor.fetchone()
        return result[0] if result else None
    except Exception as e:
        logging.error(f"Error getting upload date: {e}")
        return None
    finally:
        conn.close()

def get_all_upload_dates():
    """Get all upload dates for batch operations"""
    conn = get_upload_dates_conn()
    cursor = conn.cursor()
    
    try:
        cursor.execute('SELECT card_id, upload_date FROM card_upload_dates')
        return {row[0]: row[1] for row in cursor.fetchall()}
    except Exception as e:
        logging.error(f"Error getting all upload dates: {e}")
        return {}
    finally:
        conn.close()

async def fetch_telegram_message_dates(channel_username, limit=1000):
    """
    Fetch message dates from Telegram channel
    Requires these environment variables:
    - TELEGRAM_API_ID: From https://my.telegram.org/apps
    - TELEGRAM_API_HASH: From https://my.telegram.org/apps  
    - TELEGRAM_PHONE_NUMBER: Your phone number
    """
    api_id = int(os.getenv('TELEGRAM_API_ID'))
    api_hash = os.getenv('TELEGRAM_API_HASH')
    phone_number = os.getenv('TELEGRAM_PHONE_NUMBER')
    
    if not all([api_id, api_hash, phone_number]):
        logging.error("Telegram API credentials not set")
        return {}
    
    client = TelegramClient('session_name', api_id, api_hash)
    await client.start(phone=phone_number)
    
    try:
        channel = await client.get_entity(channel_username)
        message_dates = {}
        
        async for message in client.iter_messages(channel, limit=limit):
            if message.media and message.id:
                # Store message ID and date
                message_dates[message.id] = message.date
        
        logging.info(f"Fetched {len(message_dates)} message dates from Telegram")
        return message_dates
    except Exception as e:
        logging.error(f"Error fetching Telegram messages: {e}")
        return {}
    finally:
        await client.disconnect()

def sync_fetch_message_dates(channel_username, limit=1000):
    """Sync wrapper for the async function"""
    return asyncio.run(fetch_telegram_message_dates(channel_username, limit))

def find_card_message_mapping():
    """
    This function attempts to find a mapping between card IDs and Telegram message IDs.
    Since we don't have a direct mapping, we'll use a heuristic approach.
    You'll need to customize this based on how your cards are organized.
    """
    connection = get_db_conn()
    if not connection:
        return {}
    
    try:
        with connection.cursor() as cursor:
            # Get all cards ordered by ID (assuming newer cards have higher IDs)
            cursor.execute("SELECT id FROM files ORDER BY id")
            cards = [row['id'] for row in cursor.fetchall()]
            
            # This is a simple mapping - you might need to adjust this logic
            # Assuming card IDs roughly correspond to message order
            mapping = {}
            for i, card_id in enumerate(cards):
                # Offset might be needed if your first card isn't message 1
                mapping[card_id] = i + 1  # Message IDs usually start from 1
            
            return mapping
            
    except Exception as e:
        logging.error(f"Error creating card mapping: {e}")
        return {}
    finally:
        connection.close()

def calculate_season_from_date(upload_date):
    """
    Calculate season based on upload date
    Season 1: January 2025
    Season 2: February 2025
    And so on...
    """
    if not upload_date:
        return 1  # Default season if no date available
    
    # Convert to datetime object if it's a string
    if isinstance(upload_date, str):
        try:
            upload_date = datetime.fromisoformat(upload_date.replace('Z', '+00:00'))
        except:
            return 1
    
    # Calculate season based on month difference from January 2025
    base_year = 2025
    base_month = 1  # January
    
    year = upload_date.year
    month = upload_date.month
    
    # Calculate season number
    season = (year - base_year) * 12 + (month - base_month) + 1
    
    # Ensure season is at least 1
    return max(1, season)

def get_season_for_card(card_id):
    """Get season for a specific card"""
    upload_date = get_upload_date(card_id)
    return calculate_season_from_date(upload_date)

def get_seasons_for_cards(card_ids):
    """Get seasons for multiple cards efficiently"""
    upload_dates = get_all_upload_dates()
    seasons = {}
    
    for card_id in card_ids:
        upload_date = upload_dates.get(card_id)
        seasons[card_id] = calculate_season_from_date(upload_date)
    
    return seasons




def get_db_conn():
    """Get MySQL database connection"""
    try:
        connection = pymysql.connect(**Config.MYSQL_CONFIG)
        return connection
    except Exception as e:
        logging.error(f"Error creating MySQL connection: {e}")
        return None

@app.route('/placeholder.jpg')
def serve_placeholder():
    return send_from_directory('public', 'placeholder.jpg')

# Authentication Helper Function
def is_authenticated(request, session):
    token = request.args.get("token") or request.cookies.get("token")
    if not token:
        logging.debug("No token found in request")
        return False, None

    try:
        print(token)
        auth_token = AuthToken.query.filter_by(token=token).first()
        if auth_token is None:
            logging.debug("Token not found in database")
            return False, None

        # Optionally store user_id in session for easier access later
        session['user_id'] = auth_token.user_id

        logging.debug("Token is valid (database check)")
        # In a real app, you might fetch more user info here
        # For now, we just return the user_id from the token
        return True, auth_token.user_id

    except Exception as e:
        logging.exception(f"Authentication error: {e}")
        return False, None

# Function to download avatar image
def download_avatar(url, user_id):
    if not url:
        return None
    avatar_dir = 'backend/avatars'
    os.makedirs(avatar_dir, exist_ok=True)
    filename = os.path.join(avatar_dir, f"{user_id}.jpg")  # Assuming avatars are JPEGs, adjust if needed
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()  # Raise an exception for bad status codes
        with open(filename, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        return filename
    except requests.exceptions.RequestException as e:
        logging.error(f"Error downloading avatar from {url}: {e}")
        return None

# Telegram OAuth Callback Route
@app.route("/auth/telegram-callback")
def telegram_callback():
    user_id = request.args.get("id", type=int)
    auth_date = request.args.get("auth_date")
    query_hash = request.args.get("hash")
    print(query_hash)

    if user_id is None or query_hash is None:
        return "Invalid request", 400

    # Extract parameters and sort them
    params = request.args.to_dict()
    data_check_string = "\n".join(sorted(f"{x}={y}" for x, y in params.items() if x not in ("hash", "next")))

    # Compute HMAC hash using BOT_TOKEN_HASH
    computed_hash = hmac.new(Config.BOT_TOKEN_HASH.digest(), data_check_string.encode(), sha256).hexdigest()

    if not hmac.compare_digest(computed_hash, query_hash):
        return "Authorization failed. Please try again", 401

    # Extract user data from Telegram
    telegram_id = request.args.get("id", type=int)
    first_name = request.args.get("first_name")
    last_name = request.args.get("last_name")
    username = request.args.get("username")
    photo_url = request.args.get("photo_url")

    # Store Telegram data in session
    session.update(telegram_id=telegram_id, telegram_first_name=first_name, telegram_last_name=last_name, telegram_username=username, telegram_photo_url=photo_url)

    # Generate a unique token and store it in the database
    db_token = str(uuid.uuid4())
    auth_token = AuthToken(token=db_token, user_id=user_id)

    try:
        db.session.add(auth_token)
        db.session.commit()
        logging.debug(f"Stored token {db_token} for user {user_id} in database")

    except Exception as e:
        db.session.rollback()
        logging.exception(f"Database error saving token: {e}")
        return "Database error", 500

    # Redirect to home, setting the token in a cookie
    response = make_response(redirect(url_for("home")))
    response.set_cookie("token", db_token, httponly=True, secure=True)
    response.set_data(f"""
      <script>
        window.parent.postMessage('auth-success', 'http://localhost:5173');
      </script>
    """)
    return response

# Logout Route (Clears the Token)
@app.route("/auth/logout", methods=['GET', 'POST'])
def logout():
    token = request.cookies.get("token")

    if token:
        try:
            auth_token = AuthToken.query.filter_by(token=token).first()
            if auth_token:
                db.session.delete(auth_token)
                db.session.commit()
                logging.debug(f"Deleted token {token} from database")

        except Exception as e:
            db.session.rollback()
            logging.exception(f"Database error deleting token: {e}")
            return "Database error", 500

    session.clear() # Clear the user's session data
    response = make_response(jsonify({'status': 'logged_out'}))
    response.delete_cookie("token")
    return response

@app.after_request
def apply_csp(response):
    response.headers['Content-Security-Policy'] = (
        "frame-ancestors 'self' https://dahole.ru; "
        "frame-src 'self' https://oauth.telegram.org;"
    )
    return response

# Main Route (Checks for Authentication)
@app.route("/")
def return_home():
    return redirect(url_for("home"))
    
# Main Route (Checks for Authentication)
@app.route("/login")
def login():
    is_auth, user_id = is_authenticated(request, session)
    if is_auth:
        return redirect(url_for("home"))
    else:
        if request.args.get('check_auth'):
            is_auth, user_id = is_authenticated(request, session)
            return jsonify({
                'type': 'auth-status',
                'isAuthenticated': is_auth,
                'userId': user_id
            }), 200

        #return render_template("login.html")


# Home Route (Protected Page)
@app.route("/home")
def home():
    is_auth, _ = is_authenticated(request, session)
    return render_template("homepage.html", is_auth=is_auth)



#API ROUTES

HIDDEN_CARD_NAMES = ['срать в помогатор апельсины', 'test', 'фаланга пальца']

@app.route("/api/db-status")
def db_status():
    connection = get_db_conn()
    if not connection:
        return jsonify({'error': 'MySQL connection failed'}), 500
    
    try:
        # PostgreSQL check (keep existing if you still need it)
        pg_version = None
        try:
            pg_version = db.session.execute(text("SELECT version()")).scalar()
        except:
            pg_version = "PostgreSQL not available"
        
        # MySQL check
        with connection.cursor() as cursor:
            cursor.execute("SELECT VERSION() as version")
            mysql_version = cursor.fetchone()['version']
            
            # Count cards from files table (since cards table doesn't exist)
            cursor.execute("SELECT COUNT(*) as count FROM files")
            cards_count = cursor.fetchone()['count']
        
        return jsonify({
            "postgres_version": pg_version,
            "mysql_version": mysql_version,
            "cards_count": cards_count
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        connection.close()


@app.route("/api/upload-dates-status")
def upload_dates_status():
    """Check if upload dates database is working"""
    try:
        conn = get_upload_dates_conn()
        cursor = conn.cursor()
        
        # Check if table exists and get row count
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='card_upload_dates'")
        table_exists = cursor.fetchone() is not None
        
        if table_exists:
            cursor.execute("SELECT COUNT(*) as count FROM card_upload_dates")
            row_count = cursor.fetchone()[0]
        else:
            row_count = 0
            
        conn.close()
        
        return jsonify({
            'status': 'healthy',
            'table_exists': table_exists,
            'stored_dates_count': row_count
        }), 200
        
    except Exception as e:
        logging.error(f"Upload dates database health check failed: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/api/card_image/<path:file_id>')
def serve_card_image(file_id):
    """Serve card images/videos from local cache, downloading from Telegram if not cached"""
    TOKEN = os.getenv("CARDS_BOT_TOKEN")
    
    if not TOKEN:
        logging.error("CARDS_BOT_TOKEN environment variable is not set!")
        return send_from_directory('public', 'placeholder.jpg')
    
    logging.debug(f"Attempting to serve media for file_id: {file_id}")
    
    # Create cache directories if they don't exist
    image_cache_dir = 'backend/card_images'
    video_cache_dir = 'backend/card_videos'
    os.makedirs(image_cache_dir, exist_ok=True)
    os.makedirs(video_cache_dir, exist_ok=True)
    
    # Check if file is already cached as image
    image_cache_file = os.path.join(image_cache_dir, f"{file_id}.jpg")
    video_cache_file = os.path.join(video_cache_dir, f"{file_id}.mp4")
    
    # Check image cache first
    if os.path.exists(image_cache_file):
        try:
            logging.debug(f"Serving from image cache: {image_cache_file}")
            return send_from_directory(image_cache_dir, f"{file_id}.jpg")
        except Exception as e:
            logging.warning(f"Error serving cached image for {file_id}: {str(e)}")
    
    # Check video cache
    if os.path.exists(video_cache_file):
        try:
            logging.debug(f"Serving from video cache: {video_cache_file}")
            response = make_response(send_from_directory(video_cache_dir, f"{file_id}.mp4"))
            response.headers.set('Content-Type', 'video/mp4')
            response.headers.set('Cache-Control', 'public, max-age=3600')
            return response
        except Exception as e:
            logging.warning(f"Error serving cached video for {file_id}: {str(e)}")
    
    try:
        # First, get file path from Telegram API
        api_url = f"https://api.telegram.org/bot{TOKEN}/getFile?file_id={file_id}"
        response = requests.get(api_url)
        
        if response.status_code != 200:
            logging.warning(f"Failed to get file info for file_id {file_id}: {response.text}")
            return send_from_directory('public', 'placeholder.jpg')
        
        file_info = response.json()
        if not file_info.get("ok"):
            error_description = file_info.get('description', 'Unknown error')
            logging.warning(f"Telegram API error for file_id {file_id}: {error_description}")
            
            if file_id.startswith('CgAC'):
                logging.info(f"File {file_id} appears to be a special type (sticker/animation), using placeholder")
            return send_from_directory('public', 'placeholder.jpg')
        
        file_path = file_info.get("result", {}).get("file_path")
        if not file_path:
            logging.warning(f"file_path not found for file_id {file_id}")
            return send_from_directory('public', 'placeholder.jpg')
        
        logging.debug(f"File path obtained: {file_path}")
        
        # Download the file from Telegram
        file_url = f"https://api.telegram.org/file/bot{TOKEN}/{file_path}"
        file_response = requests.get(file_url)
        
        if file_response.status_code != 200:
            logging.warning(f"Failed to download file for file_id {file_id}: {file_response.status_code}")
            return send_from_directory('public', 'placeholder.jpg')
        
        # Determine if this is a video file based on file path extension
        is_video = file_path.lower().endswith(('.mp4', '.mov', '.avi', '.webm'))
        
        if is_video:
            # Cache as video
            try:
                with open(video_cache_file, 'wb') as f:
                    f.write(file_response.content)
                logging.debug(f"Cached video for file_id {file_id} at {video_cache_file}")
            except Exception as e:
                logging.warning(f"Failed to cache video for {file_id}: {str(e)}")
            
            # Return the video
            response = make_response(file_response.content)
            response.headers.set('Content-Type', 'video/mp4')
            response.headers.set('Cache-Control', 'public, max-age=3600')
            logging.debug(f"Successfully served video for {file_id}")
            return response
        else:
            # Cache as image
            try:
                with open(image_cache_file, 'wb') as f:
                    f.write(file_response.content)
                logging.debug(f"Cached image for file_id {file_id} at {image_cache_file}")
            except Exception as e:
                logging.warning(f"Failed to cache image for {file_id}: {str(e)}")
            
            # Return the image
            response = make_response(file_response.content)
            response.headers.set('Content-Type', 'image/jpeg')
            response.headers.set('Cache-Control', 'public, max-age=3600')
            logging.debug(f"Successfully served image for {file_id}")
            return response
            
    except Exception as e:
        logging.error(f"Error serving card media for {file_id}: {str(e)}", exc_info=True)
        return send_from_directory('public', 'placeholder.jpg')


@app.route("/api/card_upload_date/<card_id>")
def get_card_upload_date(card_id):
    """Get upload date and season for a specific card"""
    try:
        upload_date = get_upload_date(int(card_id))
        season = calculate_season_from_date(upload_date)
        
        if upload_date:
            return jsonify({
                'card_id': card_id,
                'upload_date': upload_date,
                'season_id': season
            }), 200
        else:
            return jsonify({
                'card_id': card_id,
                'upload_date': None,
                'season_id': 1,  # Default season
                'message': 'Upload date not available'
            }), 404
    except ValueError:
        return jsonify({'error': 'Invalid card ID'}), 400
    except Exception as e:
        logging.error(f"Error getting upload date: {e}")
        return jsonify({'error': 'Failed to fetch upload date'}), 500


@app.route("/admin/fetch-upload-dates")
def admin_fetch_upload_dates():
    """Admin endpoint to fetch and store upload dates from Telegram"""
    # Add authentication check here if needed
    channel_username = request.args.get('channel', '@your_channel_username')  # Replace with your channel
    
    try:
        # Step 1: Fetch message dates from Telegram
        message_dates = sync_fetch_message_dates(channel_username, limit=2000)
        
        # Step 2: Get card to message mapping
        card_mapping = find_card_message_mapping()
        
        # Step 3: Store the dates
        stored_count = 0
        for card_id, message_id in card_mapping.items():
            if message_id in message_dates:
                if store_upload_date(card_id, message_id, message_dates[message_id]):
                    stored_count += 1
        
        return jsonify({
            'status': 'success', 
            'message': f'Stored upload dates for {stored_count} cards',
            'total_cards': len(card_mapping),
            'total_messages': len(message_dates)
        }), 200
        
    except Exception as e:
        logging.error(f"Error fetching upload dates: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route("/api/categories")
def get_categories():
    """Get all categories: all cards, available at shop, and rarities"""
    connection = get_db_conn()
    if not connection:
        return jsonify({'error': 'Database connection failed'}), 500
    
    try:
        with connection.cursor() as cursor:
            # Define hidden categories to exclude - only Scarface remains hidden
            hidden_categories = ['Scarface - Tony Montana']
            
            # Get total card count (excluding hidden categories AND hidden card names)
            cursor.execute("""
                SELECT COUNT(*) as total 
                FROM files 
                WHERE rare NOT IN (%s)
                AND name NOT IN (%s, %s, %s)
            """, hidden_categories + HIDDEN_CARD_NAMES)
            total_cards = cursor.fetchone()['total']
            
            # Get shop available count (excluding hidden categories AND hidden card names)
            cursor.execute("""
                SELECT COUNT(*) as shop_count 
                FROM files 
                WHERE shop != '-' AND shop IS NOT NULL 
                AND rare NOT IN (%s)
                AND name NOT IN (%s, %s, %s)
            """, hidden_categories + HIDDEN_CARD_NAMES)
            shop_count = cursor.fetchone()['shop_count']
            
            # Get all rarities with counts (excluding hidden categories AND hidden card names)
            cursor.execute("""
                SELECT rare, COUNT(*) as count 
                FROM files 
                WHERE rare NOT IN (%s)
                AND name NOT IN (%s, %s, %s)
                GROUP BY rare 
                ORDER BY count DESC
            """, hidden_categories + HIDDEN_CARD_NAMES)
            rarities_data = cursor.fetchall()
            
            # Build categories list (same as before)
            categories = [
                {
                    'id': 'all',
                    'name': 'All Cards',
                    'type': 'general',
                    'count': total_cards
                },
                {
                    'id': 'shop',
                    'name': 'Available at Shop', 
                    'type': 'shop',
                    'count': shop_count
                }
            ]
            
            # Add rarities as categories
            for rarity_data in rarities_data:
                categories.append({
                    'id': f"rarity_{rarity_data['rare']}",
                    'name': rarity_data['rare'],
                    'type': 'rarity',
                    'count': rarity_data['count']
                })
            
            return jsonify(categories), 200
            
    except Exception as e:
        logging.error(f"Error fetching categories: {str(e)}")
        return jsonify({'error': 'Failed to fetch categories'}), 500
    finally:
        connection.close()


@app.route("/api/cards/by-category/<category_id>")
def get_cards_by_category(category_id):
    """Get cards filtered by category (all cards, shop, or specific rarity)"""
    connection = get_db_conn()
    if not connection:
        return jsonify({'error': 'Database connection failed'}), 500
    
    try:
        sort_field = request.args.get('sort', 'id')
        sort_direction = request.args.get('direction', 'asc')
        
        # Define hidden categories to exclude - only Scarface remains hidden
        hidden_categories = ['Scarface - Tony Montana']
        
        with connection.cursor() as cursor:
            # Handle different category types
            if category_id == 'all':
                # Get all cards except hidden categories AND hidden card names
                query = f"""
                    SELECT id, tg_id as photo, name, rare as rarity, fame as points 
                    FROM files 
                    WHERE rare NOT IN (%s)
                    AND name NOT IN (%s, %s, %s)
                    ORDER BY {sort_field} {sort_direction}
                """
                cursor.execute(query, hidden_categories + HIDDEN_CARD_NAMES)
                
            elif category_id == 'shop':
                # Get only cards available in shop, excluding hidden categories AND hidden card names
                query = f"""
                    SELECT id, tg_id as photo, name, rare as rarity, fame as points 
                    FROM files 
                    WHERE shop != '-' AND shop IS NOT NULL
                    AND rare NOT IN (%s)
                    AND name NOT IN (%s, %s, %s)
                    ORDER BY {sort_field} {sort_direction}
                """
                cursor.execute(query, hidden_categories + HIDDEN_CARD_NAMES)
                
            elif category_id.startswith('rarity_'):
                # Get cards by specific rarity, excluding hidden card names
                rarity_name = category_id.replace('rarity_', '')
                # Handle URL encoding for special characters
                import urllib.parse
                rarity_name = urllib.parse.unquote(rarity_name)
                
                query = f"""
                    SELECT id, tg_id as photo, name, rare as rarity, fame as points 
                    FROM files 
                    WHERE rare = %s
                    AND name NOT IN (%s, %s, %s)
                    ORDER BY {sort_field} {sort_direction}
                """
                cursor.execute(query, (rarity_name,) + tuple(HIDDEN_CARD_NAMES))
                
            else:
                return jsonify({'error': 'Invalid category ID'}), 400
            
            cards = [dict(row) for row in cursor.fetchall()]
            
            # Get upload dates for all cards in this batch
            upload_dates = get_all_upload_dates()
            
            # Transform to match frontend expectations
            transformed_cards = []
            for card in cards:
                upload_date = upload_dates.get(card['id'])
                season = calculate_season_from_date(upload_date)
                
                transformed_card = {
                    'id': card['id'],
                    'uuid': card['id'],
                    'img': card['photo'],
                    'name': card['name'],
                    'rarity': card['rarity'],
                    'category': card['rarity'],  # This should set category to rarity
                    'points': card['points'],
                    'upload_date': upload_date,  # Add upload date
                    'season_id': season  # Add calculated season
                }
                transformed_cards.append(transformed_card)
            
            return jsonify({
                'cards': transformed_cards,
                'total_count': len(transformed_cards),
                'category_id': category_id
            }), 200
            
    except Exception as e:
        logging.error(f"Error fetching cards by category: {str(e)}")
        return jsonify({'error': 'Failed to fetch cards'}), 500
    finally:
        connection.close()


@app.route("/api/rarity_newest_cards")
def get_rarity_newest_cards():
    """Get the newest card image for each rarity category"""
    connection = get_db_conn()
    if not connection:
        return jsonify({'error': 'Database connection failed'}), 500
    
    try:
        # Define hidden categories to exclude - only Scarface remains hidden
        hidden_categories = ['Scarface - Tony Montana']
        
        with connection.cursor() as cursor:
            # Get the newest card (highest ID) for each rarity, excluding hidden card names
            cursor.execute("""
                SELECT f1.rare, f1.tg_id as photo, f1.name
                FROM files f1
                INNER JOIN (
                    SELECT rare, MAX(id) as max_id
                    FROM files 
                    WHERE rare NOT IN (%s)
                    AND name NOT IN (%s, %s, %s)
                    GROUP BY rare
                ) f2 ON f1.rare = f2.rare AND f1.id = f2.max_id
                ORDER BY f1.rare
            """, hidden_categories + HIDDEN_CARD_NAMES)
            
            newest_cards = cursor.fetchall()
            
            # Convert to dictionary with rarity as key
            result = {}
            for card in newest_cards:
                result[card['rare']] = {
                    'photo': card['photo'],
                    'name': card['name']
                }
            
            return jsonify(result), 200
            
    except Exception as e:
        logging.error(f"Error fetching newest rarity cards: {str(e)}")
        return jsonify({'error': 'Failed to fetch newest cards'}), 500
    finally:
        connection.close()


@app.route("/api/all_categories_newest_cards")
def get_all_categories_newest_cards():
    """Get the newest card image for all categories including All Cards and Shop"""
    connection = get_db_conn()
    if not connection:
        return jsonify({'error': 'Database connection failed'}), 500
    
    try:
        # Define hidden categories to exclude - only Scarface remains hidden
        hidden_categories = ['Scarface - Tony Montana']
        
        with connection.cursor() as cursor:
            result = {}
            
            # Get newest card for "All Cards" category (overall newest card), excluding hidden card names
            cursor.execute("""
                SELECT tg_id as photo, name, rare as rarity
                FROM files 
                WHERE rare NOT IN (%s)
                AND name NOT IN (%s, %s, %s)
                ORDER BY id DESC 
                LIMIT 1
            """, hidden_categories + HIDDEN_CARD_NAMES)
            
            all_cards_newest = cursor.fetchone()
            if all_cards_newest:
                result['All Cards'] = {
                    'photo': all_cards_newest['photo'],
                    'name': all_cards_newest['name']
                }
            
            # Get newest card for "Shop" category (newest card available in shop), excluding hidden card names
            cursor.execute("""
                SELECT tg_id as photo, name, rare as rarity
                FROM files 
                WHERE shop != '-' AND shop IS NOT NULL
                AND rare NOT IN (%s)
                AND name NOT IN (%s, %s, %s)
                ORDER BY id DESC 
                LIMIT 1
            """, hidden_categories + HIDDEN_CARD_NAMES)
            
            shop_newest = cursor.fetchone()
            if shop_newest:
                result['Available at Shop'] = {
                    'photo': shop_newest['photo'],
                    'name': shop_newest['name']
                }
            
            # Also include all rarity categories for consistency, excluding hidden card names
            cursor.execute("""
                SELECT f1.rare, f1.tg_id as photo, f1.name
                FROM files f1
                INNER JOIN (
                    SELECT rare, MAX(id) as max_id
                    FROM files 
                    WHERE rare NOT IN (%s)
                    AND name NOT IN (%s, %s, %s)
                    GROUP BY rare
                ) f2 ON f1.rare = f2.rare AND f1.id = f2.max_id
                ORDER BY f1.rare
            """, hidden_categories + HIDDEN_CARD_NAMES)
            
            rarity_newest_cards = cursor.fetchall()
            for card in rarity_newest_cards:
                result[card['rare']] = {
                    'photo': card['photo'],
                    'name': card['name']
                }
            
            return jsonify(result), 200
            
    except Exception as e:
        logging.error(f"Error fetching newest cards for all categories: {str(e)}")
        return jsonify({'error': 'Failed to fetch newest cards'}), 500
    finally:
        connection.close()


@app.route('/api/check_permission', methods=['GET'])
def check_permission():
    username = request.args.get('username')
    if not username:
        return jsonify({'error': 'Username not provided'}), 400

    user = AllowedUser.query.filter_by(username=username).first()
    is_allowed = user is not None

    return jsonify({'is_allowed': is_allowed})
    

@app.route("/api/card_info/<card_id>")
def get_card_info(card_id):  
    connection = get_db_conn()
    if not connection:
        return jsonify({'error': 'Database connection failed'}), 500
    
    try:
        with connection.cursor() as cursor:
            # Query the files table with shop information
            cursor.execute(
                "SELECT tg_id as photo, name, rare as rarity, fame as points, shop FROM files WHERE id = %s", 
                (int(card_id),)
            )
            row = cursor.fetchone()
            
            if not row:
                return jsonify({'error': 'Card not found'}), 404
            
            # Check if card is in hidden category OR has a hidden name
            hidden_categories = ['Scarface - Tony Montana']
            if row['rarity'] in hidden_categories or row['name'] in HIDDEN_CARD_NAMES:
                return jsonify({'error': 'Card not found'}), 404

            # Get upload date from SQLite database and calculate season
            upload_date = get_upload_date(int(card_id))
            season = calculate_season_from_date(upload_date)

            return jsonify({
                'id': card_id,
                'uuid': card_id,
                'season_id': season,  # Use calculated season instead of default
                'img': row['photo'],
                'category': row['rarity'],
                'name': row['name'],
                'description': f"Points: {row['points']}",
                'shop': row['shop'],  # Add shop information
                'upload_date': upload_date  # Add upload date
            }), 200
            
    except ValueError:
        return jsonify({'error': 'Invalid card ID'}), 400
    except Exception as e:
        logging.error(f"MySQL error: {str(e)}")
        return jsonify({'error': 'Failed to fetch card info'}), 500
    finally:
        connection.close()


@app.route("/api/season_info/<int:season_id>")  #yep
def get_season_info(season_id):  
    try:
        season_num = int(season_id)
        
        season_info = {
            'id': season_num,
            'uuid': season_num,
            'name': "Season " + str(season_num)
        }
        
        return jsonify(season_info), 200
        
    except ValueError:
        return jsonify({'error': 'Invalid season ID format'}), 400
    except Exception as e:
        logging.error(f"Error fetching season info: {e}")
        return jsonify({'error': 'Failed to fetch season info'}), 500


@app.route("/api/seasons")
def get_all_seasons():
    """Get information about all available seasons"""
    try:
        # Get all unique seasons from cards
        connection = get_db_conn()
        if not connection:
            return jsonify({'error': 'Database connection failed'}), 500
        
        with connection.cursor() as cursor:
            # Get all card IDs
            cursor.execute("SELECT id FROM files")
            card_ids = [row['id'] for row in cursor.fetchall()]
        
        # Get seasons for all cards
        seasons_data = get_seasons_for_cards(card_ids)
        unique_seasons = set(seasons_data.values())
        
        # Create season info for each unique season
        seasons_list = []
        for season_id in sorted(unique_seasons):
            # Use the existing season_info endpoint logic to get season details
            season_data = get_season_info(season_id)
            if season_data[1] == 200:  # If successful
                seasons_list.append(season_data[0].json)
        
        return jsonify(seasons_list), 200
        
    except Exception as e:
        logging.error(f"Error fetching seasons: {e}")
        return jsonify({'error': 'Failed to fetch seasons'}), 500


@app.route("/api/check_auth")
def check_auth():
    is_auth, user_id = is_authenticated(request, session)
    return jsonify({
        'isAuthenticated': is_auth,
        'userId': user_id
    }), 200


@app.route("/api/user", methods=['GET'])
def get_user_info():
    user_id = session.get('user_id')
    if user_id:
        # Retrieve Telegram user info directly from the session, using keys set in telegram_callback
        user_data = {
            "id": session.get('telegram_id'),
            "first_name": session.get('telegram_first_name'),
            "last_name": session.get('telegram_last_name'),
            "photo_url": session.get('telegram_photo_url'),
            "username": session.get('telegram_username') # Add username
        }
        return jsonify(user_data), 200
    return jsonify({'error': 'User not authenticated'}), 401


if __name__ == "__main__":
    # Ensure the database is initialized before starting the app
    init_upload_dates_db()
    app.run(debug=True, port=8000)

@app.route('/avatars/<int:user_id>')
def serve_avatar(user_id):
    avatar_dir = 'backend/avatars'
    filename = f"{user_id}.jpg" # Assuming JPG extension

    try:
        return send_from_directory(avatar_dir, filename)
    except FileNotFoundError:
        return "Avatar not found", 404

@app.route('/proxy/avatar')
def proxy_avatar():
    """Proxies avatar images from a given URL."""
    url = request.args.get('url')
    logging.debug(f"Proxying avatar from URL: {url}")
    if not url:
        return "Missing image URL", 400
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()  # Raise an HTTPError for bad responses
        # Return the image data with the appropriate content type
        return response.content, response.status_code, {'Content-Type': response.headers.get('Content-Type', 'image/jpeg')}
        response = make_response(response.content)
        response.headers['Content-Type'] = response.headers.get('Content-Type', 'image/jpeg')
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        return response
    except requests.exceptions.RequestException as e:
        logging.error(f"Error proxying avatar from {url}: {e}")
        return "Image not found or could not be downloaded.", 404
