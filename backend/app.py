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

import subprocess
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
    """Get MySQL connection by using MySQL client as proxy"""
    try:
        # This approach uses the fact that MySQL client can connect locally
        connection = pymysql.connect(
            host='localhost',
            user='bot',
            password='xMdAUTiD',
            database='bot',
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor,
            unix_socket='/var/run/mysqld/mysqld.sock'  # Use socket connection
        )
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

@app.route("/db-status")
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
            
            cursor.execute("SELECT COUNT(*) as count FROM cards")
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

@app.route('/card_imgs/<filename>')
def serve_card_image(filename):
    # Создаем папку если ее нет
    # os.makedirs('card_imgs', exist_ok=True)
    return send_from_directory('card_imgs', filename)

@app.route("/api/seasons")
def get_seasons():
    connection = get_db_conn()
    if not connection:
        return jsonify({'error': 'Database connection failed'}), 500
    
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT DISTINCT season FROM cards WHERE season IS NOT NULL")
            seasons = [row['season'] for row in cursor.fetchall()]
            return jsonify(sorted(seasons)), 200
    except Exception as e:
        logging.error(f"Database error: {str(e)}")
        return jsonify({'error': 'Failed to fetch seasons'}), 500
    finally:
        connection.close()

@app.route("/api/cards/<season_id>")
def get_cards(season_id):  
    connection = get_db_conn()
    if not connection:
        return jsonify({'error': 'Database connection failed'}), 500
    
    try:
        sort_field = request.args.get('sort', 'id')
        sort_direction = request.args.get('direction', 'asc')

        RARITY_ORDER = {
            'EPISODICAL': 1,
            'SECONDARY': 2,
            'FAMOUS': 3,
            'MAINCHARACTER': 4,
            'MOVIE': 5,
            'SERIES': 6,
            'ACHIEVEMENTS': 7
        }
        
        with connection.cursor() as cursor:
            if sort_field == 'rarity':
                cursor.execute(
                    "SELECT id, photo, name, rarity, points FROM cards WHERE season = %s",
                    (int(season_id),)
                )
                cards = [dict(row) for row in cursor.fetchall()]
                
                cards.sort(key=lambda x: RARITY_ORDER.get(x['rarity'], 0))
                if sort_direction.lower() == 'desc':
                    cards.reverse()
                
                return jsonify(cards), 200
            elif sort_field == 'amount':
                query = """
                    SELECT c.id, c.photo, c.name, c.rarity, c.points, COUNT(f.card_id) as amount 
                    FROM cards c
                    LEFT JOIN filmstrips f ON c.id = f.card_id
                    WHERE c.season = %s
                    GROUP BY c.id, c.photo, c.name, c.rarity, c.points
                    ORDER BY amount {}
                """.format(sort_direction)
                
                cursor.execute(query, (int(season_id),))
                cards = [dict(row) for row in cursor.fetchall()]
                return jsonify(cards), 200
            else:
                query = """
                    SELECT id, id as uuid, photo as img, name, rarity, points 
                    FROM cards 
                    WHERE season = %s
                    ORDER BY {} {}
                """.format(sort_field, sort_direction)
                
                cursor.execute(query, (int(season_id),))
                cards = [dict(row) for row in cursor.fetchall()]
                return jsonify(cards), 200
            
    except ValueError:
        return jsonify({'error': 'Invalid season ID'}), 400
    except Exception as e:
        logging.error(f"Error fetching cards: {str(e)}")
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
            cursor.execute(
                "SELECT photo, name, rarity, points, number, `drop`, event, season FROM cards WHERE id = %s", 
                (int(card_id),)
            )
            row = cursor.fetchone()
            
            if not row:
                return jsonify({'error': 'Card not found'}), 404
                
            cursor.execute(
                "SELECT COUNT(*) as count FROM filmstrips WHERE card_id = %s",
                (card_id,)
            )
            card_count = cursor.fetchone()['count']

            return jsonify({
                'id': card_id,
                'uuid': card_id,
                'season_id': row['season'],
                'img': row['photo'],
                'category': row['rarity'],
                'name': row['name'],
                'description': f"Amount: {card_count}"
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
