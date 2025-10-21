import os
import asyncio
from datetime import datetime
from telethon import TelegramClient
from telethon.tl.types import MessageMediaPhoto, MessageMediaDocument
import logging
from models import db, CardUploadMetadata
from unidecode import unidecode
import re

class TelegramClientService:
    def __init__(self):
        self.api_id = os.getenv("TELEGRAM_API_ID")
        self.api_hash = os.getenv("TELEGRAM_API_HASH")
        self.session_name = 'funkocards_session'
        self.channel_username = '@funkocardsall'
        
    async def get_channel_messages(self, limit=1000):
        """Get messages from channel using Telethon"""
        if not self.api_id or not self.api_hash:
            logging.error("TELEGRAM_API_ID or TELEGRAM_API_HASH not set")
            return []
        
        client = TelegramClient(self.session_name, self.api_id, self.api_hash)
        
        try:
            await client.start()
            logging.info("Telegram client started successfully")
            
            # Get the channel entity
            channel = await client.get_entity(self.channel_username)
            logging.info(f"Connected to channel: {channel.title}")
            
            # Fetch messages
            messages = []
            async for message in client.iter_messages(channel, limit=limit):
                messages.append(message)
                if len(messages) % 100 == 0:
                    logging.info(f"Fetched {len(messages)} messages...")
            
            logging.info(f"Total messages fetched: {len(messages)}")
            return messages
            
        except Exception as e:
            logging.error(f"Error fetching messages: {e}")
            return []
        finally:
            await client.disconnect()
    
    def normalize_card_name(self, name):
        """Normalize card name for matching"""
        if not name:
            return ""
        
        normalized = unidecode(name).lower()
        normalized = re.sub(r'[^\w\s]', ' ', normalized)
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        
        return normalized
    
    def extract_card_name_from_message(self, message_text):
        """Extract card name from message text"""
        if not message_text:
            return None
        
        # Remove ID ranges like "123-456"
        text_without_ids = re.sub(r'\n?\d+-\d+', '', message_text)
        
        # Remove any remaining numbers
        text_clean = re.sub(r'\b\d+\b', '', text_without_ids)
        
        # Split by common separators
        separators = ['\n', ' - ', ' – ', ' | ']
        for sep in separators:
            if sep in text_clean:
                card_name = text_clean.split(sep)[0].strip()
                if card_name:
                    return self.normalize_card_name(card_name)
        
        # If no separators, use the whole text (within reason)
        if len(text_clean.strip()) < 100:
            return self.normalize_card_name(text_clean.strip())
        
        return None
    
    def find_card_in_messages(self, card_name, messages):
        """Find card in messages using improved matching"""
        if not card_name or not messages:
            return None
        
        normalized_card_name = self.normalize_card_name(card_name)
        logging.info(f"Searching for: '{card_name}' -> '{normalized_card_name}'")
        
        # Strategy 1: Exact match on normalized names
        for message in messages:
            message_text = message.text or message.message or ""
            extracted_name = self.extract_card_name_from_message(message_text)
            
            if extracted_name and extracted_name == normalized_card_name:
                logging.info(f"Exact match found: '{card_name}'")
                return message
        
        # Strategy 2: Partial match (card name contains message name or vice versa)
        for message in messages:
            message_text = message.text or message.message or ""
            extracted_name = self.extract_card_name_from_message(message_text)
            
            if not extracted_name:
                continue
                
            if (normalized_card_name in extracted_name or 
                extracted_name in normalized_card_name):
                logging.info(f"Partial match: '{card_name}' ~ '{extracted_name}'")
                return message
        
        # Strategy 3: Word-based matching
        best_match = None
        best_score = 0
        
        card_words = set(normalized_card_name.split())
        
        for message in messages:
            message_text = message.text or message.message or ""
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
        
        if best_match and best_score >= 0.5:  # 50% word match
            message_text = best_match.text or best_match.message or ""
            extracted_name = self.extract_card_name_from_message(message_text)
            logging.info(f"Word match: '{card_name}' ~ '{extracted_name}' (score: {best_score:.2f})")
            return best_match
        
        logging.warning(f"No match found for: '{card_name}'")
        return None
    
    def calculate_season_from_date(self, upload_date):
        """Calculate season based on upload date"""
        if not upload_date:
            return 1
        
        year = upload_date.year
        month = upload_date.month
        
        if year == 2025:
            return month  # January = Season 1, February = Season 2, etc.
        else:
            return (year - 2025) * 12 + month
    
    async def sync_channel_messages_async(self):
        """Main sync method using Telethon"""
        logging.info("Starting Telegram sync with Telethon...")
        
        # Get channel messages
        messages = await self.get_channel_messages(limit=2000)
        if not messages:
            logging.error("No messages fetched from channel")
            return False
        
        # Get all cards from database
        from app import get_db_conn
        connection = get_db_conn()
        if not connection:
            logging.error("Cannot connect to MySQL database")
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
            
            matched_count = 0
            
            for card in all_cards:
                card_id = card['id']
                card_name = card['name']
                
                # Skip if already has good metadata
                existing = CardUploadMetadata.query.filter_by(card_id=card_id).first()
                if existing and existing.telegram_message_id > 0:
                    continue
                
                # Find matching message
                matching_message = self.find_card_in_messages(card_name, messages)
                
                if matching_message:
                    upload_date = matching_message.date
                    message_id = matching_message.id
                    season = self.calculate_season_from_date(upload_date)
                    
                    if existing:
                        existing.telegram_message_id = message_id
                        existing.upload_date = upload_date
                        existing.season = season
                    else:
                        new_metadata = CardUploadMetadata(
                            card_id=card_id,
                            telegram_message_id=message_id,
                            upload_date=upload_date,
                            season=season
                        )
                        db.session.add(new_metadata)
                    
                    matched_count += 1
                    logging.info(f"Matched: {card_name} (ID: {card_id}) -> Message {message_id}, Season {season}")
                    
                    # Commit every 20 matches
                    if matched_count % 20 == 0:
                        db.session.commit()
                        logging.info(f"Committed {matched_count} matches...")
            
            db.session.commit()
            logging.info(f"Sync completed: {matched_count}/{len(all_cards)} cards matched")
            return True
            
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error during sync: {e}")
            return False
        finally:
            connection.close()

# Sync wrapper for Flask
def sync_telegram_messages():
    """Wrapper to run async function from sync context"""
    service = TelegramClientService()
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(service.sync_channel_messages_async())
    finally:
        loop.close()

# Global instance
telegram_client_service = TelegramClientService()