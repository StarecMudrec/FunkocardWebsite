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
import requests
import base64
import hashlib
from PIL import Image
import io

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class TelegramUserSync:
    def __init__(self):
        self.api_id = os.getenv("TELEGRAM_API_ID")
        self.api_hash = os.getenv("TELEGRAM_API_HASH")
        self.session_file = 'user_session.session'
        self.channel_username = '@funkocardsall'
        
    async def sync_messages_async(self):
        """Sync using pre-configured user session"""
        if not all([self.api_id, self.api_hash]):
            logging.error("Missing Telegram credentials")
            return False
        
        if not os.path.exists(self.session_file):
            logging.error(f"Session file {self.session_file} not found. Please create it first.")
            return False
        
        client = TelegramClient(
            session=self.session_file,
            api_id=int(self.api_id),
            api_hash=self.api_hash
        )
        
        try:
            await client.start()
            logging.info("Telegram user client started successfully")
            
            me = await client.get_me()
            logging.info(f"User connected as: {me.first_name} (@{me.username})")
            
            try:
                channel = await client.get_entity(self.channel_username)
                logging.info(f"Accessing channel: {channel.title}")
            except Exception as e:
                logging.error(f"Cannot access channel {self.channel_username}: {e}")
                return False
            
            # Fetch MORE messages to ensure we find the right ones
            messages = []
            try:
                async for message in client.iter_messages(channel, limit=2000):  # Increased limit
                    messages.append(message)
                    if len(messages) % 100 == 0:
                        logging.info(f"Fetched {len(messages)} messages...")
                
                logging.info(f"Total messages fetched: {len(messages)}")
                
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
        """Process messages and update database with metadata - ENHANCED VERSION"""
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
                    SELECT id, name, tg_id
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
                card_tg_id = card['tg_id']  # This is the Telegram file_id
                
                # Try multiple matching strategies
                matching_message = await self.find_card_by_multiple_strategies(
                    card_name, card_tg_id, messages, connection
                )
                
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
                    logging.info(f"✅ Matched card '{card_name}' (ID: {card_id}) with message from {upload_date}")
                    
                    if matched_count % 10 == 0:
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
                    
                    logging.info(f"❌ No match found for card '{card_name}' (ID: {card_id}) - set to NULL")
            
            postgres_session.commit()
            logging.info(f"Sync completed: {matched_count}/{len(all_cards)} cards matched")
            return True
            
        except Exception as e:
            logging.error(f"Database error: {e}")
            return False
        finally:
            connection.close()
            postgres_session.close()
    
    async def find_card_by_multiple_strategies(self, card_name, card_tg_id, messages, connection):
        """Try multiple strategies to find the card in Telegram messages"""
        # Strategy 1: Exact name matching (your existing method)
        exact_match = await self.find_card_exact_match(card_name, messages)
        if exact_match:
            logging.debug(f"Found '{card_name}' via exact name match")
            return exact_match
        
        # Strategy 2: Check if we can get file info and match by media
        if card_tg_id and card_tg_id != 'None':
            file_match = await self.find_card_by_file_id(card_tg_id, messages, connection)
            if file_match:
                logging.debug(f"Found '{card_name}' via file ID match")
                return file_match
        
        # Strategy 3: Fuzzy name matching for difficult cases
        fuzzy_match = await self.find_card_fuzzy_match(card_name, messages)
        if fuzzy_match:
            logging.debug(f"Found '{card_name}' via fuzzy name match")
            return fuzzy_match
        
        return None
    
    async def find_card_exact_match(self, card_name, messages):
        """STRICT exact matching for card names"""
        if not card_name:
            return None
        
        # Create multiple search patterns for the exact card name
        search_patterns = self.create_exact_search_patterns(card_name)
        
        matching_messages = []
        
        for message in messages:
            if not message.text:
                continue
                
            message_text = message.text
            
            # Check each search pattern for exact match
            for pattern in search_patterns:
                if self.is_exact_match(pattern, message_text, card_name):
                    matching_messages.append(message)
                    break  # Found a match, no need to check other patterns
        
        # Return the most recent matching message
        if matching_messages:
            matching_messages.sort(key=lambda msg: msg.date, reverse=True)
            return matching_messages[0]
        
        return None
    
    def create_exact_search_patterns(self, card_name):
        """Create multiple exact search patterns for a card name"""
        patterns = []
        
        # Pattern 1: Exact card name as it appears in database
        patterns.append(card_name)
        
        # Pattern 2: Normalized version (no special chars, lowercase)
        normalized = self.normalize_for_exact_match(card_name)
        patterns.append(normalized)
        
        # Pattern 3: Remove any text in parentheses for matching
        without_parentheses = re.sub(r'\([^)]*\)', '', card_name).strip()
        if without_parentheses and without_parentheses != card_name:
            patterns.append(without_parentheses)
            patterns.append(self.normalize_for_exact_match(without_parentheses))
        
        # Remove duplicates and empty patterns
        patterns = [p for p in patterns if p and len(p) > 2]
        patterns = list(dict.fromkeys(patterns))  # Remove duplicates while preserving order
        
        logging.debug(f"Search patterns for '{card_name}': {patterns}")
        return patterns
    
    def normalize_for_exact_match(self, text):
        """Normalize text for exact matching - less aggressive than before"""
        if not text:
            return ""
        
        # Convert to lowercase
        normalized = text.lower()
        
        # Remove extra spaces but keep punctuation (cards might have punctuation in names)
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        
        return normalized
    
    def is_exact_match(self, search_pattern, message_text, original_card_name):
        """Check if the search pattern exactly matches in the message text"""
        if not search_pattern or not message_text:
            return False
        
        # Convert both to lowercase for case-insensitive comparison
        pattern_lower = search_pattern.lower()
        message_lower = message_text.lower()
        
        # Strategy 1: Exact string contains (most common case)
        if pattern_lower in message_lower:
            # Additional verification: check if it's not just a partial match
            words_in_pattern = set(pattern_lower.split())
            words_in_message = set(message_lower.split())
            
            # If the pattern has multiple words, require at least 2/3 of them to match
            if len(words_in_pattern) > 1:
                common_words = words_in_pattern.intersection(words_in_message)
                if len(common_words) >= max(2, len(words_in_pattern) * 0.6):
                    return True
            else:
                # Single word pattern - be more strict
                # Check if it's surrounded by word boundaries or punctuation
                import re
                word_boundary_pattern = r'\b' + re.escape(pattern_lower) + r'\b'
                if re.search(word_boundary_pattern, message_lower):
                    return True
        
        # Strategy 2: Check for the card name as a standalone line or after common prefixes
        common_prefixes = ['card:', 'card -', 'new card:', 'card name:', 'name:']
        for prefix in common_prefixes:
            if f"{prefix} {pattern_lower}" in message_lower:
                return True
            if f"{prefix}{pattern_lower}" in message_lower:
                return True
        
        # Strategy 3: Check if message starts with card name (common in card announcements)
        if message_lower.startswith(pattern_lower):
            return True
        
        # Strategy 4: Check for quoted card name (often used in announcements)
        if f"\"{pattern_lower}\"" in message_lower:
            return True
        if f"'{pattern_lower}'" in message_lower:
            return True
        
        return False
    
    async def find_card_by_file_id(self, card_tg_id, messages, connection):
        """Try to find card by matching Telegram file IDs"""
        try:
            # Get file info from Telegram API
            TOKEN = os.getenv("CARDS_BOT_TOKEN")
            if not TOKEN:
                logging.warning("CARDS_BOT_TOKEN not available for file matching")
                return None
            
            api_url = f"https://api.telegram.org/bot{TOKEN}/getFile?file_id={card_tg_id}"
            response = requests.get(api_url)
            
            if response.status_code != 200:
                return None
            
            file_info = response.json()
            if not file_info.get("ok"):
                return None
            
            file_path = file_info.get("result", {}).get("file_path")
            if not file_path:
                return None
            
            # Download the file to get its hash/signature
            file_url = f"https://api.telegram.org/file/bot{TOKEN}/{file_path}"
            file_response = requests.get(file_url)
            
            if file_response.status_code != 200:
                return None
            
            # Calculate file hash for comparison
            file_content = file_response.content
            file_hash = hashlib.md5(file_content).hexdigest()
            file_size = len(file_content)
            
            logging.debug(f"Card file: {file_path}, Hash: {file_hash}, Size: {file_size}")
            
            # Now search through messages for matching media
            for message in messages:
                if message.media:
                    try:
                        # Get media info from message
                        media_file = await self.get_media_file_info(message, TOKEN)
                        if media_file and media_file.get('hash') == file_hash:
                            logging.info(f"✅ Media hash match found for card {card_tg_id}")
                            return message
                    except Exception as e:
                        logging.debug(f"Error checking media in message {message.id}: {e}")
                        continue
            
            return None
            
        except Exception as e:
            logging.error(f"Error in file ID matching for {card_tg_id}: {e}")
            return None
    
    async def get_media_file_info(self, message, token):
        """Extract file info from message media"""
        try:
            if hasattr(message.media, 'document'):
                # Document (could be image/video)
                document = message.media.document
                file_size = document.size
                # For hash, we'd need to download, but that's expensive
                # Instead, use file_unique_id as a signature
                return {
                    'size': file_size,
                    'unique_id': getattr(document, 'file_unique_id', None)
                }
            elif hasattr(message.media, 'photo'):
                # Photo
                photo = message.media.photo
                file_size = photo.sizes[-1].size if photo.sizes else 0
                return {
                    'size': file_size,
                    'unique_id': getattr(photo, 'file_unique_id', None)
                }
        except Exception as e:
            logging.debug(f"Error extracting media info: {e}")
        
        return None
    
    async def find_card_fuzzy_match(self, card_name, messages):
        """Fuzzy matching for card names that don't match exactly"""
        try:
            from fuzzywuzzy import fuzz
        except ImportError:
            logging.warning("fuzzywuzzy not installed, skipping fuzzy matching")
            return None
        
        best_match = None
        best_score = 0
        
        normalized_card_name = self.normalize_for_fuzzy_match(card_name)
        
        for message in messages:
            if not message.text:
                continue
                
            message_text = message.text
            normalized_message = self.normalize_for_fuzzy_match(message_text)
            
            # Calculate similarity score
            score = fuzz.partial_ratio(normalized_card_name, normalized_message)
            
            # Also check if card name appears as a standalone word
            words_in_message = set(normalized_message.split())
            words_in_card = set(normalized_card_name.split())
            
            common_words = words_in_card.intersection(words_in_message)
            if len(common_words) >= max(2, len(words_in_card) * 0.5):
                score = max(score, 80)  # Boost score for significant word overlap
            
            if score > best_score and score > 70:  # Threshold for fuzzy matching
                best_score = score
                best_match = message
        
        if best_match:
            logging.info(f"Fuzzy match: '{card_name}' with score {best_score}")
        
        return best_match
    
    def normalize_for_fuzzy_match(self, text):
        """Normalize text for fuzzy matching"""
        if not text:
            return ""
        
        # Convert to lowercase
        normalized = text.lower()
        
        # Remove special characters but keep spaces
        normalized = re.sub(r'[^\w\s]', '', normalized)
        
        # Remove extra spaces
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        
        return normalized
    
    def calculate_season_from_date(self, upload_date):
        """Calculate season based on upload date"""
        if not upload_date:
            return None
            
        try:
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
    logging.info("Starting enhanced Telegram user sync with multiple matching strategies...")
    sync = TelegramUserSync()
    
    try:
        success = asyncio.run(sync.sync_messages_async())
        if success:
            logging.info("Enhanced sync completed successfully")
        else:
            logging.error("Enhanced sync failed")
        exit(0 if success else 1)
    except Exception as e:
        logging.error(f"Enhanced sync failed: {e}")
        exit(1)

if __name__ == "__main__":
    main()