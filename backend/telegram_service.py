import os
import requests
from datetime import datetime
from models import db, CardUploadMetadata
import logging
import time
import re
from unidecode import unidecode

class TelegramService:
    def __init__(self):
        self.bot_token = os.getenv("CARDS_BOT_TOKEN")
        self.channel_username = "@funkocardsall"
    
    def get_all_channel_messages(self):
        """Get all messages from the channel using the correct approach"""
        if not self.bot_token:
            logging.error("CARDS_BOT_TOKEN not set")
            return []
        
        # Method 1: Try using getChatHistory (if bot is admin in channel)
        all_messages = []
        from_id = 0
        limit = 100
        
        logging.info("Attempting to fetch channel messages using getChatHistory...")
        
        while True:
            url = f"https://api.telegram.org/bot{self.bot_token}/getChatHistory"
            payload = {
                "chat_id": self.channel_username,
                "from_message_id": from_id,
                "limit": limit
            }
            
            try:
                response = requests.post(url, json=payload, timeout=30)
                if response.status_code == 200:
                    result = response.json()
                    if result.get("ok"):
                        messages = result.get("result", {}).get("messages", [])
                        
                        if not messages:
                            break
                        
                        all_messages.extend(messages)
                        logging.info(f"Fetched {len(messages)} messages, total: {len(all_messages)}")
                        
                        # Update from_id to get next batch
                        from_id = messages[-1]["id"]
                        
                        # Small delay to avoid rate limiting
                        time.sleep(0.2)
                    else:
                        error_msg = result.get('description', 'Unknown error')
                        logging.error(f"Telegram API error: {error_msg}")
                        
                        # If method fails, try alternative approach
                        if "method not found" in error_msg.lower():
                            logging.info("getChatHistory not available, trying alternative method...")
                            return self.get_messages_alternative_method()
                        break
                else:
                    logging.error(f"Failed to get messages: {response.text}")
                    break
                    
            except Exception as e:
                logging.error(f"Error fetching messages: {e}")
                break
        
        logging.info(f"Total channel messages fetched: {len(all_messages)}")
        return all_messages
    
    def get_messages_alternative_method(self):
        """Alternative method using exportChatInviteLink + public channel access"""
        logging.info("Using alternative method to fetch messages...")
        
        # Since your channel is public (@funkocardsall), we can try a different approach
        # This would require the bot to be in the channel and have appropriate permissions
        
        all_messages = []
        offset_id = 0
        limit = 100
        
        # This is a simplified approach - you might need to adjust based on your channel setup
        for i in range(10):  # Safety limit of 1000 messages
            url = f"https://api.telegram.org/bot{self.bot_token}/getUpdates"
            payload = {
                "offset": offset_id,
                "limit": limit,
                "timeout": 1
            }
            
            try:
                response = requests.post(url, json=payload, timeout=30)
                if response.status_code == 200:
                    result = response.json()
                    if result.get("ok"):
                        updates = result.get("result", [])
                        
                        if not updates:
                            break
                        
                        channel_messages = []
                        for update in updates:
                            if 'channel_post' in update:
                                message = update['channel_post']
                                channel_messages.append(message)
                                offset_id = update['update_id'] + 1
                        
                        all_messages.extend(channel_messages)
                        logging.info(f"Batch {i+1}: Found {len(channel_messages)} channel messages")
                        
                        if len(updates) < limit:
                            break
                            
                        time.sleep(0.1)
                    else:
                        break
                else:
                    break
            except Exception as e:
                logging.error(f"Error in alternative method: {e}")
                break
        
        logging.info(f"Alternative method found {len(all_messages)} messages")
        return all_messages
    
    def normalize_card_name(self, name):
        """Improved card name normalization"""
        if not name:
            return ""
        
        # Convert to lowercase and remove accents
        normalized = unidecode(name).lower()
        
        # Remove special characters but keep spaces
        normalized = re.sub(r'[^\w\s]', '', normalized)
        
        # Replace multiple spaces with single space
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        
        return normalized
    
    def extract_card_name_from_message(self, message_text):
        """Improved card name extraction from Telegram messages"""
        if not message_text:
            return None
        
        # Common patterns in Telegram card posts:
        # 1. "Card Name\n123-456" 
        # 2. "Card Name - Description\n123-456"
        # 3. Just "Card Name"
        
        # Remove ID ranges like "123-456"
        text_without_ids = re.sub(r'\n?\d+-\d+', '', message_text)
        
        # Remove any remaining numbers and special markers
        text_clean = re.sub(r'\b\d+\b', '', text_without_ids)
        
        # Split by common separators and take first part
        separators = ['\n', ' - ', ' – ', ' | ']
        for sep in separators:
            if sep in text_clean:
                card_name = text_clean.split(sep)[0].strip()
                if card_name:
                    return self.normalize_card_name(card_name)
        
        # If no separators, use the whole text (within reason)
        if len(text_clean.strip()) < 100:  # Reasonable card name length
            return self.normalize_card_name(text_clean.strip())
        
        return None
    
    def find_card_in_messages(self, card_name, messages):
        """Improved card matching with better logging"""
        if not card_name or not messages:
            return None
        
        normalized_card_name = self.normalize_card_name(card_name)
        logging.info(f"Searching for card: '{card_name}' (normalized: '{normalized_card_name}')")
        
        # Try exact match first
        for message in messages:
            message_text = message.get("caption") or message.get("text", "")
            if not message_text:
                continue
            
            extracted_name = self.extract_card_name_from_message(message_text)
            if extracted_name and extracted_name == normalized_card_name:
                logging.info(f"Exact match found for '{card_name}'")
                return message
        
        # Try partial match
        for message in messages:
            message_text = message.get("caption") or message.get("text", "")
            if not message_text:
                continue
            
            extracted_name = self.extract_card_name_from_message(message_text)
            if not extracted_name:
                continue
            
            # Check if our card name contains the extracted name or vice versa
            if (normalized_card_name in extracted_name or 
                extracted_name in normalized_card_name):
                logging.info(f"Partial match: '{card_name}' ~ '{extracted_name}'")
                return message
            
            # Check word overlap
            card_words = set(normalized_card_name.split())
            message_words = set(extracted_name.split())
            
            if card_words and message_words:
                common_words = card_words.intersection(message_words)
                if len(common_words) >= min(2, len(card_words)):
                    logging.info(f"Word match: '{card_name}' ~ '{extracted_name}' (common: {common_words})")
                    return message
        
        logging.warning(f"No match found for card: '{card_name}'")
        return None
    
    def calculate_season_from_date(self, upload_date):
        """Simplified season calculation based on actual dates"""
        if not upload_date:
            return 1
        
        # Simple monthly seasons starting from January 2025
        year = upload_date.year
        month = upload_date.month
        
        if year == 2025:
            return month  # January = Season 1, February = Season 2, etc.
        else:
            # For future years: 12 months per year
            return (year - 2025) * 12 + month
    
    def sync_channel_messages(self):
        """Improved sync with better error handling and logging"""
        if not self.bot_token:
            logging.error("CARDS_BOT_TOKEN not set")
            return False
        
        logging.info("Starting improved Telegram channel message sync...")
        
        # Get all cards from MySQL database
        from app import get_db_conn
        connection = get_db_conn()
        if not connection:
            logging.error("Cannot connect to MySQL database")
            return False
        
        try:
            with connection.cursor() as cursor:
                # Get all cards (id and name)
                cursor.execute("""
                    SELECT id, name 
                    FROM files 
                    WHERE name NOT IN ('срать в помогатор апельсины', 'test', 'фаланга пальца')
                    ORDER BY id
                """)
                all_cards = cursor.fetchall()
                
            logging.info(f"Found {len(all_cards)} cards in database to sync")
            
            # Get all channel messages
            messages = self.get_all_channel_messages()
            if not messages:
                logging.warning("No messages retrieved from channel")
                return False
            
            logging.info(f"Processing {len(messages)} channel messages")
            
            # Process each card
            processed_count = 0
            matched_count = 0
            
            for card in all_cards:
                card_id = card['id']
                card_name = card['name']
                processed_count += 1
                
                if processed_count % 50 == 0:
                    logging.info(f"Processed {processed_count}/{len(all_cards)} cards...")
                
                # Find card in messages
                matching_message = self.find_card_in_messages(card_name, messages)
                
                if matching_message:
                    # Extract metadata from message
                    upload_date = datetime.fromtimestamp(matching_message["date"])
                    message_id = matching_message["id"]
                    season = self.calculate_season_from_date(upload_date)
                    
                    # Check if we already have metadata for this card
                    existing = CardUploadMetadata.query.filter_by(card_id=card_id).first()
                    
                    if existing:
                        # Update existing
                        existing.telegram_message_id = message_id
                        existing.upload_date = upload_date
                        existing.season = season
                        logging.debug(f"Updated: {card_name} (ID: {card_id}) - {upload_date}, Season {season}")
                    else:
                        # Create new
                        new_metadata = CardUploadMetadata(
                            card_id=card_id,
                            telegram_message_id=message_id,
                            upload_date=upload_date,
                            season=season
                        )
                        db.session.add(new_metadata)
                        logging.info(f"Created: {card_name} (ID: {card_id}) - {upload_date}, Season {season}")
                    
                    matched_count += 1
                    
                    # Commit every 10 matches to avoid large transactions
                    if matched_count % 10 == 0:
                        db.session.commit()
                        logging.debug(f"Committed {matched_count} matches so far...")
            
            # Final commit
            db.session.commit()
            logging.info(f"Sync completed: {matched_count}/{len(all_cards)} cards matched with messages")
            return True
            
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error during sync: {e}")
            return False
        finally:
            connection.close()

# Global instance
telegram_service = TelegramService()