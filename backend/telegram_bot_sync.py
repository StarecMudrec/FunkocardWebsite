import os
import asyncio
import logging
from datetime import datetime
from telethon import TelegramClient
from unidecode import unidecode
import re
import pymysql
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Database configuration
MYSQL_CONFIG = {
    'host': 'localhost',
    'user': 'bot',
    'password': 'xMdAUTiD',
    'database': 'database',
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor,
    'port': 3306
}

POSTGRES_URI = "postgresql+psycopg2://postgres:postgres@localhost:5433/cards"

class TelegramBotSync:
    def __init__(self):
        self.api_id = os.getenv("TELEGRAM_API_ID")
        self.api_hash = os.getenv("TELEGRAM_API_HASH")
        self.bot_token = os.getenv("CARDS_BOT_TOKEN")
        self.session_name = 'funkocards_bot_session'
        self.channel_username = '@funkocardsall'
        
    def get_db_conn(self):
        """Get MySQL database connection"""
        try:
            return pymysql.connect(**MYSQL_CONFIG)
        except Exception as e:
            logging.error(f"Error creating MySQL connection: {e}")
            return None
    
    def get_postgres_session(self):
        """Get PostgreSQL session for metadata"""
        try:
            engine = create_engine(POSTGRES_URI)
            Session = sessionmaker(bind=engine)
            return Session()
        except Exception as e:
            logging.error(f"Error creating PostgreSQL session: {e}")
            return None
    
    def normalize_card_name(self, name):
        """Normalize card name for matching"""
        if not name:
            return ""
        
        # Remove content in parentheses and brackets
        name = re.sub(r'\([^)]*\)', '', name)
        name = re.sub(r'\[[^\]]*\]', '', name)
        
        normalized = unidecode(name).lower()
        normalized = re.sub(r'[^\w\s]', ' ', normalized)
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        
        return normalized
    
    def extract_card_name_from_message(self, message_text):
        """Extract card name from message text"""
        if not message_text:
            return None
        
        # Remove ID ranges like "123-456" or "123"
        text_without_ids = re.sub(r'\n?\d+(-\d+)?', '', message_text)
        
        # Remove content in parentheses
        text_clean = re.sub(r'\([^)]*\)', '', text_without_ids)
        
        # Split by common separators
        separators = ['\n', ' - ', ' – ', ' | ', ' — ']
        for sep in separators:
            if sep in text_clean:
                parts = text_clean.split(sep)
                if parts:
                    card_name = parts[0].strip()
                    if card_name:
                        return self.normalize_card_name(card_name)
        
        # If no separators, use the whole text (within reason)
        if len(text_clean.strip()) < 100:
            return self.normalize_card_name(text_clean.strip())
        
        return None
    
    def find_card_in_messages(self, card_name, messages):
        """Find card in messages with improved matching"""
        if not card_name or not messages:
            return None
        
        normalized_card_name = self.normalize_card_name(card_name)
        logging.debug(f"Searching for: '{card_name}' -> '{normalized_card_name}'")
        
        # Strategy 1: Exact match on normalized names
        for message in messages:
            message_text = message.text or ""
            extracted_name = self.extract_card_name_from_message(message_text)
            
            if extracted_name and extracted_name == normalized_card_name:
                logging.info(f"Exact match found: '{card_name}'")
                return message
        
        # Strategy 2: Check if card name contains message name or vice versa
        for message in messages:
            message_text = message.text or ""
            extracted_name = self.extract_card_name_from_message(message_text)
            
            if not extracted_name:
                continue
                
            # Check if one contains the other
            if (normalized_card_name in extracted_name or 
                extracted_name in normalized_card_name):
                logging.info(f"Containment match: '{card_name}' ~ '{extracted_name}'")
                return message
        
        # Strategy 3: Word-based matching with threshold
        best_match = None
        best_score = 0
        threshold = 0.6  # 60% word match
        
        card_words = set(normalized_card_name.split())
        
        for message in messages:
            message_text = message.text or ""
            extracted_name = self.extract_card_name_from_message(message_text)
            
            if not extracted_name:
                continue
                
            message_words = set(extracted_name.split())
            
            if card_words and message_words:
                common_words = card_words.intersection(message_words)
                similarity = len(common_words) / len(card_words)
                
                if similarity > best_score:
                    best_score = similarity
                    best_match = message
        
        if best_match and best_score >= threshold:
            message_text = best_match.text or ""
            extracted_name = self.extract_card_name_from_message(message_text)
            logging.info(f"Word match: '{card_name}' ~ '{extracted_name}' (score: {best_score:.2f})")
            return best_match
        
        logging.debug(f"No match found for: '{card_name}'")
        return None
    
    def calculate_season_from_date(self, upload_date):
        """Calculate season based on upload date"""
        if not upload_date:
            return 1
        
        year = upload_date.year
        month = upload_date.month
        
        if year == 2025:
            return month
        else:
            return (year - 2025) * 12 + month
    
    async def sync_messages_async(self):
        """Async method to sync messages using bot"""
        if not all([self.api_id, self.api_hash, self.bot_token]):
            logging.error("Telegram bot credentials not set")
            return False
        
        # Use bot token authentication
        client = TelegramClient(self.session_name, int(self.api_id), self.api_hash)
        
        try:
            await client.start(bot_token=self.bot_token)
            logging.info("Telegram bot client started successfully")
            
            # Verify we're connected
            me = await client.get_me()
            logging.info(f"Bot connected: {me.username}")
            
            # Try to access channel
            try:
                channel = await client.get_entity(self.channel_username)
                logging.info(f"Accessing channel: {channel.title}")
            except Exception as e:
                logging.error(f"Bot cannot access channel {self.channel_username}: {e}")
                logging.error("Make sure the bot is added to the channel as admin")
                return False
            
            # Fetch messages
            messages = []
            try:
                async for message in client.iter_messages(channel, limit=1000):
                    messages.append(message)
                    if len(messages) % 100 == 0:
                        logging.info(f"Fetched {len(messages)} messages...")
                
                logging.info(f"Total messages fetched: {len(messages)}")
                
                # Log a few sample messages for debugging
                for i, msg in enumerate(messages[:3]):
                    logging.info(f"Sample message {i+1}: {msg.text[:100] if msg.text else 'No text'}")
                    
            except Exception as e:
                logging.error(f"Error fetching messages: {e}")
                return False
            
            if not messages:
                logging.error("No messages fetched from channel")
                return False
            
            # Process cards
            connection = self.get_db_conn()
            if not connection:
                logging.error("Cannot connect to MySQL database")
                return False
            
            postgres_session = self.get_postgres_session()
            if not postgres_session:
                logging.error("Cannot connect to PostgreSQL database")
                return False
            
            try:
                with connection.cursor() as cursor:
                    cursor.execute("""
                        SELECT id, name 
                        FROM files 
                        WHERE name NOT IN ('срать в помогатор апельсины', 'test', 'фаланга пальца')
                        ORDER BY id
                    """)
                    all_cards = cursor.fetchall()
                
                logging.info(f"Processing {len(all_cards)} cards against {len(messages)} messages")
                
                from sqlalchemy import text
                matched_count = 0
                processed_count = 0
                
                for card in all_cards:
                    card_id = card['id']
                    card_name = card['name']
                    processed_count += 1
                    
                    if processed_count % 100 == 0:
                        logging.info(f"Processed {processed_count}/{len(all_cards)} cards...")
                    
                    # Skip if already has good metadata
                    result = postgres_session.execute(
                        text("SELECT * FROM card_upload_metadata WHERE card_id = :card_id AND telegram_message_id > 0"),
                        {"card_id": card_id}
                    ).fetchone()
                    
                    if result:
                        continue
                    
                    # Find matching message
                    matching_message = self.find_card_in_messages(card_name, messages)
                    
                    if matching_message:
                        upload_date = matching_message.date
                        message_id = matching_message.id
                        season = self.calculate_season_from_date(upload_date)
                        
                        # Check if exists
                        existing = postgres_session.execute(
                            text("SELECT * FROM card_upload_metadata WHERE card_id = :card_id"),
                            {"card_id": card_id}
                        ).fetchone()
                        
                        if existing:
                            postgres_session.execute(
                                text("""
                                    UPDATE card_upload_metadata 
                                    SET telegram_message_id = :message_id, 
                                        upload_date = :upload_date, 
                                        season = :season 
                                    WHERE card_id = :card_id
                                """),
                                {
                                    "message_id": message_id,
                                    "upload_date": upload_date,
                                    "season": season,
                                    "card_id": card_id
                                }
                            )
                        else:
                            postgres_session.execute(
                                text("""
                                    INSERT INTO card_upload_metadata 
                                    (card_id, telegram_message_id, upload_date, season) 
                                    VALUES (:card_id, :message_id, :upload_date, :season)
                                """),
                                {
                                    "card_id": card_id,
                                    "message_id": message_id,
                                    "upload_date": upload_date,
                                    "season": season
                                }
                            )
                        
                        matched_count += 1
                        logging.info(f"Matched: {card_name} (ID: {card_id}) -> Message {message_id}, Season {season}")
                        
                        # Commit every 20 matches to avoid large transactions
                        if matched_count % 20 == 0:
                            postgres_session.commit()
                            logging.info(f"Committed {matched_count} matches so far...")
                
                postgres_session.commit()
                logging.info(f"Sync completed: {matched_count}/{len(all_cards)} cards matched")
                return True
                
            except Exception as e:
                postgres_session.rollback()
                logging.error(f"Error during database operations: {e}")
                return False
            finally:
                connection.close()
                postgres_session.close()
            
        except Exception as e:
            logging.error(f"Error in bot sync: {e}")
            return False
        finally:
            await client.disconnect()
    
    def sync_messages(self):
        """Sync messages (wrapper for async method)"""
        try:
            return asyncio.run(self.sync_messages_async())
        except Exception as e:
            logging.error(f"Error in sync wrapper: {e}")
            return False

def main():
    """Main function to run bot sync"""
    logging.info("Starting Telegram bot sync...")
    worker = TelegramBotSync()
    success = worker.sync_messages()
    
    if success:
        logging.info("Bot sync completed successfully")
        exit(0)
    else:
        logging.error("Bot sync failed")
        exit(1)

if __name__ == "__main__":
    main()