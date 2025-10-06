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

@app.route("/api/test_bot_token")
def test_bot_token():
    """Test if the bot token is working"""
    TOKEN = os.getenv("CARDS_BOT_TOKEN")
    if not TOKEN:
        return jsonify({"error": "CARDS_BOT_TOKEN not set"}), 500
    
    try:
        # Test the token by getting bot info
        api_url = f"https://api.telegram.org/bot{TOKEN}/getMe"
        response = requests.get(api_url, timeout=10)
        
        if response.status_code == 200:
            bot_info = response.json()
            if bot_info.get("ok"):
                return jsonify({
                    "status": "success",
                    "bot_username": bot_info["result"]["username"],
                    "bot_name": bot_info["result"]["first_name"]
                })
            else:
                return jsonify({
                    "status": "error",
                    "error": "Invalid token",
                    "details": bot_info.get("description", "Unknown error")
                }), 400
        else:
            return jsonify({
                "status": "error",
                "error": f"HTTP {response.status_code}",
                "details": response.text
            }), 400
            
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500

@app.route('/api/card_image/<path:file_id>')
def serve_card_image(file_id):
    """Serve card images from local cache, downloading from Telegram if not cached"""
    TOKEN = os.getenv("CARDS_BOT_TOKEN")
    
    if not TOKEN:
        logging.error("CARDS_BOT_TOKEN environment variable is not set")
        return send_from_directory('public', 'placeholder.jpg')
    
    # Validate file_id format
    if not file_id or len(file_id) < 10:
        logging.warning(f"Invalid file_id format: {file_id}")
        return send_from_directory('public', 'placeholder.jpg')
    
    # Create cache directory if it doesn't exist
    cache_dir = 'backend/card_images'
    os.makedirs(cache_dir, exist_ok=True)
    
    # Define local cache file path
    import hashlib
    safe_filename = hashlib.md5(file_id.encode()).hexdigest() + '.jpg'
    cache_file = os.path.join(cache_dir, safe_filename)
    
    # Check if image is already cached
    if os.path.exists(cache_file):
        try:
            # Verify the cached file is valid
            file_size = os.path.getsize(cache_file)
            if file_size > 100:  # Basic validation - file should be more than 100 bytes
                logging.debug(f"Serving cached image for {file_id}")
                return send_from_directory(cache_dir, safe_filename)
            else:
                logging.warning(f"Cached file too small, re-downloading: {file_id}")
                os.remove(cache_file)  # Remove invalid cache
        except Exception as e:
            logging.warning(f"Error with cached image for {file_id}: {str(e)}")
    
    try:
        logging.debug(f"Fetching file info from Telegram API for: {file_id}")
        
        # First, get file path from Telegram API
        api_url = f"https://api.telegram.org/bot{TOKEN}/getFile?file_id={file_id}"
        response = requests.get(api_url, timeout=10)
        
        if response.status_code != 200:
            logging.warning(f"Failed to get file info for file_id {file_id}: Status {response.status_code}")
            return send_from_directory('public', 'placeholder.jpg')
        
        file_info = response.json()
        logging.debug(f"Telegram API response: {file_info}")
        
        if not file_info.get("ok"):
            error_description = file_info.get('description', 'Unknown error')
            logging.warning(f"Telegram API error for file_id {file_id}: {error_description}")
            return send_from_directory('public', 'placeholder.jpg')
        
        file_path = file_info.get("result", {}).get("file_path")
        if not file_path:
            logging.warning(f"file_path not found for file_id {file_id}")
            return send_from_directory('public', 'placeholder.jpg')
        
        # Download the file from Telegram
        file_url = f"https://api.telegram.org/file/bot{TOKEN}/{file_path}"
        logging.debug(f"Downloading file from: {file_url}")
        
        file_response = requests.get(file_url, timeout=30, stream=True)
        
        if file_response.status_code != 200:
            logging.warning(f"Failed to download file for file_id {file_id}: Status {file_response.status_code}")
            return send_from_directory('public', 'placeholder.jpg')
        
        # Validate the downloaded content
        content_type = file_response.headers.get('Content-Type', '')
        content_length = file_response.headers.get('Content-Length', '0')
        
        if not content_type.startswith('image/') or int(content_length) < 100:
            logging.warning(f"Invalid image content for file_id {file_id}: {content_type}, size: {content_length}")
            return send_from_directory('public', 'placeholder.jpg')
        
        # Cache the image locally for future requests
        try:
            with open(cache_file, 'wb') as f:
                for chunk in file_response.iter_content(chunk_size=8192):
                    f.write(chunk)
            logging.debug(f"Cached image for file_id {file_id} as {safe_filename}")
        except Exception as e:
            logging.warning(f"Failed to cache image for {file_id}: {str(e)}")
        
        # Return the image with appropriate headers
        response = make_response(file_response.content)
        response.headers.set('Content-Type', content_type)
        response.headers.set('Cache-Control', 'public, max-age=3600')
        response.headers.set('Content-Length', content_length)
        logging.debug(f"Successfully served image for {file_id}")
        return response
        
    except requests.exceptions.Timeout:
        logging.error(f"Timeout while fetching image for file_id {file_id}")
        return send_from_directory('public', 'placeholder.jpg')
    except requests.exceptions.RequestException as e:
        logging.error(f"Request error while fetching image for file_id {file_id}: {str(e)}")
        return send_from_directory('public', 'placeholder.jpg')
    except Exception as e:
        logging.error(f"Unexpected error serving card image for {file_id}: {str(e)}")
        return send_from_directory('public', 'placeholder.jpg')

@app.route("/api/categories")
def get_categories():
    """Get all categories: all cards, available at shop, and rarities"""
    connection = get_db_conn()
    if not connection:
        return jsonify({'error': 'Database connection failed'}), 500
    
    try:
        with connection.cursor() as cursor:
            # Get total card count (excluding Nameless 📛 and Scarface - Tony Montana)
            cursor.execute("""
                SELECT COUNT(*) as total 
                FROM files 
                WHERE rare NOT IN ('Nameless 📛', 'Scarface - Tony Montana')
            """)
            total_cards = cursor.fetchone()['total']
            
            # Get shop available count (excluding Nameless 📛 and Scarface - Tony Montana)
            cursor.execute("""
                SELECT COUNT(*) as shop_count 
                FROM files 
                WHERE shop != '-' AND shop IS NOT NULL 
                AND rare NOT IN ('Nameless 📛', 'Scarface - Tony Montana')
            """)
            shop_count = cursor.fetchone()['shop_count']
            
            # Get all rarities with counts (excluding Nameless 📛 and Scarface - Tony Montana)
            cursor.execute("""
                SELECT rare, COUNT(*) as count 
                FROM files 
                WHERE rare NOT IN ('Nameless 📛', 'Scarface - Tony Montana')
                GROUP BY rare 
                ORDER BY count DESC
            """)
            rarities_data = cursor.fetchall()
            
            # Build categories list
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
        
        with connection.cursor() as cursor:
            # Handle different category types
            if category_id == 'all':
                # Get all cards
                query = f"""
                    SELECT id, tg_id as photo, name, rare as rarity, fame as points 
                    FROM files 
                    ORDER BY {sort_field} {sort_direction}
                """
                cursor.execute(query)
                
            elif category_id == 'shop':
                # Get only cards available in shop
                query = f"""
                    SELECT id, tg_id as photo, name, rare as rarity, fame as points 
                    FROM files 
                    WHERE shop != '-' AND shop IS NOT NULL
                    ORDER BY {sort_field} {sort_direction}
                """
                cursor.execute(query)
                
            elif category_id.startswith('rarity_'):
                # Get cards by specific rarity
                rarity_name = category_id.replace('rarity_', '')
                # Handle URL encoding for special characters
                import urllib.parse
                rarity_name = urllib.parse.unquote(rarity_name)
                
                query = f"""
                    SELECT id, tg_id as photo, name, rare as rarity, fame as points 
                    FROM files 
                    WHERE rare = %s
                    ORDER BY {sort_field} {sort_direction}
                """
                cursor.execute(query, (rarity_name,))
                
            else:
                return jsonify({'error': 'Invalid category ID'}), 400
            
            cards = [dict(row) for row in cursor.fetchall()]
            
            # Transform to match frontend expectations
            transformed_cards = []
            for card in cards:
                transformed_cards.append({
                    'id': card['id'],
                    'uuid': card['id'],
                    'img': card['photo'],
                    'name': card['name'],
                    'rarity': card['rarity'],
                    'points': card['points']
                })
            
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
            # Query the files table instead of cards table
            cursor.execute(
                "SELECT tg_id as photo, name, rare as rarity, fame as points FROM files WHERE id = %s", 
                (int(card_id),)
            )
            row = cursor.fetchone()
            
            if not row:
                return jsonify({'error': 'Card not found'}), 404

            return jsonify({
                'id': card_id,
                'uuid': card_id,
                'season_id': 1,  # Default season since we don't have season data
                'img': row['photo'],
                'category': row['rarity'],
                'name': row['name'],
                'description': f"Points: {row['points']}"
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
