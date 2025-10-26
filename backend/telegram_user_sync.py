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
                
                # Find matching message using improved search
                matching_message = await self.find_card_in_messages_advanced(card_name, messages)
                
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
    
    async def find_card_in_messages_advanced(self, card_name, messages):
        """Advanced card matching that searches for the card name in messages"""
        if not card_name:
            return None
        
        # Normalize the card name for better matching
        normalized_card_name = self.normalize_card_name(card_name)
        
        # Try different matching strategies
        matching_messages = []
        
        for message in messages:
            if not message.text:
                continue
                
            message_text = message.text.lower()
            normalized_message = self.normalize_card_name(message_text)
            
            # Strategy 1: Exact match of normalized names
            if normalized_card_name in normalized_message:
                matching_messages.append(message)
                continue
                
            # Strategy 2: Word-by-word matching (more flexible)
            card_words = set(normalized_card_name.split())
            message_words = set(normalized_message.split())
            
            # If most words match, consider it a match
            common_words = card_words.intersection(message_words)
            if len(common_words) >= max(1, len(card_words) * 0.7):  # At least 70% match or 1 word
                matching_messages.append(message)
                continue
                
            # Strategy 3: Check if card name appears as a substring in message
            # Remove common words that might cause false positives
            clean_card_name = self.remove_common_words(normalized_card_name)
            if clean_card_name and clean_card_name in normalized_message:
                matching_messages.append(message)
        
        # Return the most recent matching message (highest message ID usually means most recent)
        if matching_messages:
            # Sort by message date (newest first) and return the most recent
            matching_messages.sort(key=lambda msg: msg.date, reverse=True)
            return matching_messages[0]
        
        return None
    
    def normalize_card_name(self, text):
        """Normalize text for better matching"""
        if not text:
            return ""
        
        # Convert to lowercase and remove accents
        normalized = unidecode(text.lower())
        
        # Remove content in parentheses and brackets
        normalized = re.sub(r'\([^)]*\)', '', normalized)
        normalized = re.sub(r'\[[^\]]*\]', '', normalized)
        
        # Remove special characters but keep spaces
        normalized = re.sub(r'[^\w\s]', ' ', normalized)
        
        # Replace multiple spaces with single space
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        
        return normalized
    
    def remove_common_words(self, text):
        """Remove common words that might cause false positives"""
        if not text:
            return ""
        
        common_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 
            'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
            'should', 'may', 'might', 'must', 'can', 'card', 'cards', 'new', 'rare'
        }
        
        words = text.split()
        filtered_words = [word for word in words if word not in common_words and len(word) > 2]
        
        return ' '.join(filtered_words)
    
    def calculate_season_from_date(self, upload_date):
        """Calculate season based on upload date"""
        if not upload_date:
            return None
            
        try:
            # Your existing season logic
            year = upload_date.year
            month = upload_date.month
            
            if year == 2025:
                return month
            else:
                return (year - 2025) * 12 + month
        except Exception as e:
            logging.error(f"Error calculating season for date {upload_date}: {e}")
            return None

def main():
    logging.info("Starting Telegram user sync...")
    sync = TelegramUserSync()
    
    try:
        success = asyncio.run(sync.sync_messages_async())
        if success:
            logging.info("Sync completed successfully")
        else:
            logging.error("Sync failed")
        exit(0 if success else 1)
    except Exception as e:
        logging.error(f"Sync failed: {e}")
        exit(1)

if __name__ == "__main__":
    main()