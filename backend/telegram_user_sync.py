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

class TelegramUserSync:
    def __init__(self):
        self.api_id = os.getenv("TELEGRAM_API_ID")
        self.api_hash = os.getenv("TELEGRAM_API_HASH")
        self.session_file = 'user_session.session'  # Pre-configured session
        self.channel_username = '@funkocardsall'
        
    async def sync_messages_async(self):
        """Sync using pre-configured user session"""
        if not all([self.api_id, self.api_hash]):
            logging.error("Missing Telegram credentials")
            return False
        
        # Check if session file exists
        if not os.path.exists(self.session_file):
            logging.error(f"Session file {self.session_file} not found. Please create it first.")
            return False
        
        client = TelegramClient(
            session=self.session_file,
            api_id=int(self.api_id),
            api_hash=self.api_hash
        )
        
        try:
            # Start with existing session - no interactive auth needed
            await client.start()
            logging.info("Telegram user client started successfully")
            
            # Verify connection
            me = await client.get_me()
            logging.info(f"User connected as: {me.first_name} (@{me.username})")
            
            # Access channel
            try:
                channel = await client.get_entity(self.channel_username)
                logging.info(f"Accessing channel: {channel.title}")
            except Exception as e:
                logging.error(f"Cannot access channel {self.channel_username}: {e}")
                return False
            
            # Fetch messages - this should work with user account
            messages = []
            try:
                async for message in client.iter_messages(channel, limit=500):
                    messages.append(message)
                    if len(messages) % 50 == 0:
                        logging.info(f"Fetched {len(messages)} messages...")
                
                logging.info(f"Total messages fetched: {len(messages)}")
                
                # Process messages with database updates
                success = await self.process_messages_with_db(messages)
                return success
                
            except Exception as e:
                logging.error(f"Error fetching messages: {e}")
                return False
                
        except Exception as e:
            logging.error(f"Error in user sync: {e}")
            return False
        finally:
            await client.disconnect()
    
    async def process_messages_with_db(self, messages):
        """Process messages and update database with metadata"""
        try:
            connection = pymysql.connect(
                host='localhost',
                user='bot',
                password='xMdAUTiD',
                database='database',
                charset='utf8mb4',
                cursorclass=pymysql.cursors.DictCursor,
                port=3306
            )
            
            postgres_engine = create_engine("postgresql+psycopg2://postgres:postgres@localhost:5433/cards")
            PostgresSession = sessionmaker(bind=postgres_engine)
            postgres_session = PostgresSession()
            
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
            
            for card in all_cards:
                card_id = card['id']
                card_name = card['name']
                
                # Find matching message using improved logic
                matching_message = self.find_card_in_messages(card_name, messages)
                
                if matching_message:
                    upload_date = matching_message.date
                    message_id = matching_message.id
                    season = self.calculate_season_from_date(upload_date)
                    
                    # Update or insert metadata
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
                    logging.info(f"Matched card '{card_name}' (ID: {card_id}) with message from {upload_date}")
                    
                    if matched_count % 20 == 0:
                        postgres_session.commit()
                        logging.info(f"Committed {matched_count} matches...")
                else:
                    # No match found - set to NULL
                    existing = postgres_session.execute(
                        text("SELECT * FROM card_upload_metadata WHERE card_id = :card_id"),
                        {"card_id": card_id}
                    ).fetchone()
                    
                    if existing:
                        postgres_session.execute(
                            text("""
                                UPDATE card_upload_metadata 
                                SET telegram_message_id = NULL, 
                                    upload_date = NULL, 
                                    season = NULL 
                                WHERE card_id = :card_id
                            """),
                            {"card_id": card_id}
                        )
                    else:
                        postgres_session.execute(
                            text("""
                                INSERT INTO card_upload_metadata 
                                (card_id, telegram_message_id, upload_date, season) 
                                VALUES (:card_id, NULL, NULL, NULL)
                            """),
                            {"card_id": card_id}
                        )
                    
                    logging.info(f"No match found for card '{card_name}' (ID: {card_id}) - set to NULL")
            
            postgres_session.commit()
            logging.info(f"Sync completed: {matched_count}/{len(all_cards)} cards matched")
            return True
            
        except Exception as e:
            logging.error(f"Database error: {e}")
            return False
        finally:
            connection.close()
            postgres_session.close()
    
    def normalize_card_name(self, name):
        """Normalize card name for matching"""
        if not name:
            return ""
        # Remove content in parentheses and brackets
        name = re.sub(r'\([^)]*\)', '', name)
        name = re.sub(r'\[[^\]]*\]', '', name)
        # Convert to ASCII and lowercase
        normalized = unidecode(name).lower()
        # Remove punctuation and extra spaces
        normalized = re.sub(r'[^\w\s]', ' ', normalized)
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        return normalized
    
    def extract_card_name_from_message(self, message_text):
        """Extract card name from message text using patterns"""
        if not message_text:
            return None
            
        # Common patterns for card names in messages
        patterns = [
            # Pattern: "Card Name" or 'Card Name'
            r'["\']([^"\']+)["\']',
            # Pattern: **Card Name** (bold)
            r'\*\*([^*]+)\*\*',
            # Pattern: Card Name (at start of line or after newline)
            r'(?:^|\n)([^\n:]+?)(?:\n|$)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, message_text, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                candidate = match.strip()
                if len(candidate) > 3 and len(candidate) < 100:  # Reasonable card name length
                    return candidate
        return None
    
    def find_card_in_messages(self, card_name, messages):
        """Find the LAST message that contains this specific card"""
        normalized_card_name = self.normalize_card_name(card_name)
        matching_messages = []
        
        for message in messages:
            message_text = message.text or ""
            
            # Try to extract card name from message
            extracted_name = self.extract_card_name_from_message(message_text)
            if extracted_name:
                # Compare normalized names
                normalized_extracted = self.normalize_card_name(extracted_name)
                if normalized_extracted == normalized_card_name:
                    matching_messages.append(message)
                    continue
            
            # Fallback: check if the exact normalized card name appears in message
            # but only as a whole word to avoid partial matches
            message_words = self.normalize_card_name(message_text)
            # Use word boundaries to avoid partial matches
            if re.search(r'\b' + re.escape(normalized_card_name) + r'\b', message_words):
                matching_messages.append(message)
        
        # Return the most recent message (highest ID = most recent)
        if matching_messages:
            # Sort by message ID descending (highest ID = most recent)
            matching_messages.sort(key=lambda msg: msg.id, reverse=True)
            logging.debug(f"Found {len(matching_messages)} matches for '{card_name}', using most recent")
            return matching_messages[0]
        
        return None
    
    def calculate_season_from_date(self, upload_date):
        """Calculate season based on upload date"""
        if not upload_date:
            return None
            
        try:
            year = upload_date.year
            month = upload_date.month
            
            # Simple season calculation - adjust as needed
            if year == 2025:
                return month  # Each month is a season in 2025
            else:
                return (year - 2025) * 12 + month
        except:
            return None

def main():
    logging.info("Starting Telegram user sync...")
    sync = TelegramUserSync()
    
    try:
        success = asyncio.run(sync.sync_messages_async())
        exit(0 if success else 1)
    except Exception as e:
        logging.error(f"Sync failed: {e}")
        exit(1)

if __name__ == "__main__":
    main()