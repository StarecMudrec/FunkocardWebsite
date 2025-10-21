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
from models import db, AuthToken, Card, Season, Comment, AllowedUser, CardUploadMetadata  
from config import Config
from sqlalchemy import create_engine, select, and_, text
from sqlalchemy.orm import Session, sessionmaker
from sqlite3 import connect
# from telegram_client_service import sync_telegram_messages
from datetime import datetime
import subprocess
import sys

import pymysql

app = Flask(__name__)
app.config.from_object(Config)

# Configure logging
logging.basicConfig(level=logging.DEBUG)

db.init_app(app)

migrate = Migrate(app, db)


HIDDEN_CARD_NAMES = ['срать в помогатор апельсины', 'test', 'фаланга пальца']

def get_db_conn():
    """Get MySQL database connection"""
    try:
        connection = pymysql.connect(**Config.MYSQL_CONFIG)
        return connection
    except Exception as e:
        logging.error(f"Error creating MySQL connection: {e}")
        return None


def populate_all_cards_metadata():
    """Populate upload metadata using actual Telegram channel data with fallback"""
    try:
        # First, try to sync with actual Telegram messages
        logging.info("Attempting to sync with Telegram channel messages...")
        telegram_service.sync_channel_messages()
        
        # If no metadata was created/updated, try manual override
        existing_metadata_count = CardUploadMetadata.query.count()
        if existing_metadata_count == 0:
            logging.warning("Telegram sync didn't create any metadata, trying manual override")
            telegram_service.manual_date_override()
        
    except Exception as e:
        logging.error(f"Error during Telegram sync: {e}")
    
    # Always check for missing cards and provide reasonable defaults
    connection = get_db_conn()
    if not connection:
        logging.error("Cannot connect to MySQL database")
        return
        
    try:
        with connection.cursor() as cursor:
            # Get all card IDs from MySQL
            cursor.execute("SELECT id FROM files WHERE name NOT IN (%s, %s, %s)", 
                         tuple(HIDDEN_CARD_NAMES))
            all_card_ids = [row['id'] for row in cursor.fetchall()]
            
            existing_metadata_count = CardUploadMetadata.query.count()
            logging.info(f"Found {len(all_card_ids)} cards in MySQL, {existing_metadata_count} existing metadata entries")
            
            # For cards without metadata, create reasonable defaults based on card ID
            missing_count = 0
            for card_id in all_card_ids:
                existing = CardUploadMetadata.query.filter_by(card_id=card_id).first()
                if existing:
                    continue
                    
                # Create default metadata based on card ID as fallback
                # This is better than random dates but still not ideal
                if card_id >= 400:
                    upload_date = datetime(2025, 3, 1)
                    season = 3
                elif card_id >= 350:
                    upload_date = datetime(2025, 2, 1) 
                    season = 2
                elif card_id >= 300:
                    upload_date = datetime(2025, 1, 15)
                    season = 1
                elif card_id >= 200:
                    upload_date = datetime(2025, 1, 10)
                    season = 1
                else:
                    upload_date = datetime(2025, 1, 5)
                    season = 1
                
                metadata = CardUploadMetadata(
                    card_id=card_id,
                    telegram_message_id=0,  # Indicates no Telegram message found
                    upload_date=upload_date,
                    season=season
                )
                
                try:
                    db.session.add(metadata)
                    missing_count += 1
                except Exception as e:
                    logging.warning(f"Could not add metadata for card {card_id}: {e}")
            
            if missing_count > 0:
                db.session.commit()
                logging.info(f"Added default metadata for {missing_count} missing cards")
            
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error populating card metadata: {e}")
    finally:
        if connection:
            connection.close()


# Create the database tables
with app.app_context():
    try:
        db.create_all()
        logging.info("Database tables created successfully")
        
        # Only populate metadata if the table is empty or we need to refresh
        existing_count = CardUploadMetadata.query.count()
        if existing_count == 0:
            logging.info("No existing metadata found, populating...")
            populate_all_cards_metadata()
        else:
            logging.info(f"Found {existing_count} existing metadata entries")
            
    except Exception as e:
        logging.error(f"Error during database initialization: {e}")



def run_telegram_user_sync():
    """Run Telegram user sync as a separate process"""
    try:
        result = subprocess.run([
            sys.executable, 'telegram_user_sync.py'
        ], capture_output=True, text=True, timeout=300)  # 5 minute timeout
        
        logging.info(f"user sync process stdout: {result.stdout}")
        if result.stderr:
            logging.error(f"user sync process stderr: {result.stderr}")
        
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        logging.error("Telegram user sync process timed out")
        return False
    except Exception as e:
        logging.error(f"Error running user sync process: {e}")
        return False
    

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


@app.route("/api/debug-telegram-sync")
def debug_telegram_sync():
    """Debug endpoint to test Telegram sync functionality"""
    try:
        from telegram_client_service import telegram_client_service
        import asyncio
        
        # Test async message fetching
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        messages = loop.run_until_complete(
            telegram_client_service.get_channel_messages(limit=50)
        )
        
        # Test card matching
        from app import get_db_conn
        connection = get_db_conn()
        test_results = []
        
        with connection.cursor() as cursor:
            cursor.execute("SELECT id, name FROM files WHERE id IN (336, 1, 100, 200, 300) ORDER BY id")
            test_cards = cursor.fetchall()
            
            for card in test_cards:
                match = telegram_client_service.find_card_in_messages(card['name'], messages)
                test_results.append({
                    'card_id': card['id'],
                    'card_name': card['name'],
                    'normalized_name': telegram_client_service.normalize_card_name(card['name']),
                    'found_in_messages': match is not None,
                    'match_date': match.date.isoformat() if match else None,
                    'match_message_id': match.id if match else None,
                    'match_text_preview': (match.text or match.message or "")[:100] + '...' if match else None
                })
        
        return jsonify({
            'total_messages_found': len(messages),
            'test_cards': test_results,
            'message_sample': [{
                'id': msg.id,
                'date': msg.date.isoformat(),
                'text': (msg.text or msg.message or "")[:200]
            } for msg in messages[:5]] if messages else []
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    

@app.route("/api/test-metadata")
def test_metadata():
    """Test endpoint to check metadata functionality"""
    try:
        # Test with card ID 336 (from your example)
        metadata = CardUploadMetadata.query.filter_by(card_id=336).first()
        
        if metadata:
            return jsonify({
                'success': True,
                'metadata': metadata.present(),
                'message': 'Metadata found for card 336'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'No metadata found for card 336'
            })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route("/api/populate-sample")
def populate_sample():
    """Endpoint to manually populate sample metadata"""
    try:
        populate_sample_metadata()
        return jsonify({'status': 'Sample data populated'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route("/api/all-metadata")
def get_all_metadata():
    """Get all metadata entries (for debugging)"""
    try:
        all_metadata = CardUploadMetadata.query.all()
        return jsonify({
            'count': len(all_metadata),
            'metadata': [m.present() for m in all_metadata]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


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


@app.route("/api/sync-telegram-messages")
def sync_telegram_messages_route():
    """Endpoint to manually trigger Telegram message synchronization"""
    try:
        success = run_telegram_user_sync()  # Changed to bot sync
        if success:
            return jsonify({"status": "sync completed successfully"}), 200
        else:
            return jsonify({"error": "Sync failed - check logs"}), 500
    except Exception as e:
        logging.error(f"Sync error: {e}")
        return jsonify({"error": "Sync failed"}), 500


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
        sort_field = request.args.get('sort', 'id')  # Default to 'id'
        sort_direction = request.args.get('direction', 'desc')
        
        # Define valid MySQL columns to prevent SQL injection
        valid_mysql_columns = ['id', 'name', 'rare', 'fame']
        
        # If sort_field is 'season', we'll handle it in Python later
        if sort_field not in valid_mysql_columns:
            sort_field = 'id'  # Fallback to ID
        
        # Define hidden categories to exclude - only Scarface remains hidden
        hidden_categories = ['Scarface - Tony Montana']
        
        with connection.cursor() as cursor:
            # Handle different category types
            if category_id == 'all':
                query = """
                    SELECT id, tg_id as photo, name, rare as rarity, fame as points 
                    FROM files 
                    WHERE rare NOT IN (%s)
                    AND name NOT IN (%s, %s, %s)
                    ORDER BY {field} {direction}
                """.format(field=sort_field, direction=sort_direction)
                cursor.execute(query, hidden_categories + HIDDEN_CARD_NAMES)
                
            elif category_id == 'shop':
                query = """
                    SELECT id, tg_id as photo, name, rare as rarity, fame as points 
                    FROM files 
                    WHERE shop != '-' AND shop IS NOT NULL
                    AND rare NOT IN (%s)
                    AND name NOT IN (%s, %s, %s)
                    ORDER BY {field} {direction}
                """.format(field=sort_field, direction=sort_direction)
                cursor.execute(query, hidden_categories + HIDDEN_CARD_NAMES)
                
            elif category_id.startswith('rarity_'):
                rarity_name = category_id.replace('rarity_', '')
                import urllib.parse
                rarity_name = urllib.parse.unquote(rarity_name)
                
                query = """
                    SELECT id, tg_id as photo, name, rare as rarity, fame as points 
                    FROM files 
                    WHERE rare = %s
                    AND name NOT IN (%s, %s, %s)
                    ORDER BY {field} {direction}
                """.format(field=sort_field, direction=sort_direction)
                cursor.execute(query, (rarity_name,) + tuple(HIDDEN_CARD_NAMES))
                
            else:
                return jsonify({'error': 'Invalid category ID'}), 400
            
            cards = [dict(row) for row in cursor.fetchall()]
            
            # Transform to match frontend expectations and add upload metadata from SQLite
            transformed_cards = []
            for card in cards:
                # Get upload metadata from SQLite (separate database)
                metadata = CardUploadMetadata.query.filter_by(card_id=card['id']).first()
                
                # Default values if no metadata
                upload_date = None
                season = 1
                
                if metadata:
                    upload_date = metadata.upload_date.isoformat() if metadata.upload_date else None
                    season = metadata.season if metadata.season else 1
                
                transformed_card = {
                    'id': card['id'],
                    'uuid': card['id'],
                    'img': card['photo'],
                    'name': card['name'],
                    'rarity': card['rarity'],
                    'category': card['rarity'],
                    'points': card['points'],
                    'upload_date': upload_date,
                    'season': season
                }
                transformed_cards.append(transformed_card)
            
            # Apply season sorting in Python if requested
            if request.args.get('sort') == 'season':
                transformed_cards.sort(key=lambda x: x.get('season', 1), 
                                     reverse=(sort_direction == 'desc'))
            
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
            cursor.execute(
                "SELECT tg_id as photo, name, rare as rarity, fame as points, shop FROM files WHERE id = %s", 
                (int(card_id),)
            )
            row = cursor.fetchone()
            
            if not row:
                return jsonify({'error': 'Card not found'}), 404
            
            hidden_categories = ['Scarface - Tony Montana']
            if row['rarity'] in hidden_categories or row['name'] in HIDDEN_CARD_NAMES:
                return jsonify({'error': 'Card not found'}), 404

            # Get upload metadata
            metadata = CardUploadMetadata.query.filter_by(card_id=int(card_id)).first()
            
            # Default values if no metadata
            upload_date = None
            season = 1
            
            if metadata:
                upload_date = metadata.upload_date.isoformat() if metadata.upload_date else None
                season = metadata.season if metadata.season else 1

            return jsonify({
                'id': card_id,
                'uuid': card_id,
                'season_id': season,
                'img': row['photo'],
                'category': row['rarity'],
                'name': row['name'],
                'description': f"Points: {row['points']}",
                'shop': row['shop'],
                'upload_date': upload_date,
                'season': season  # Make sure this is included
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
