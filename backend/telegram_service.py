import os
import requests
from datetime import datetime
from models import db, CardUploadMetadata
import logging
import time
import re

class TelegramService:
    def __init__(self):
        self.bot_token = os.getenv("CARDS_BOT_TOKEN")
        self.channel_username = "@funkocardsall"
    
    def get_channel_messages_web(self, limit=100):
        """Get messages from public channel using web scraping approach"""
        if not self.bot_token:
            logging.error("CARDS_BOT_TOKEN not set")
            return []
        
        # For public channels, we need to use a different approach
        # This method uses the getUpdates method which works for public channels
        # that the bot is subscribed to
        
        url = f"https://api.telegram.org/bot{self.bot_token}/getUpdates"
        payload = {
            "offset": 0,
            "limit": limit,
            "timeout": 10
        }
        
        try:
            response = requests.post(url, json=payload, timeout=30)
            if response.status_code == 200:
                result = response.json()
                if result.get("ok"):
                    updates = result.get("result", [])
                    
                    # Filter for channel posts
                    channel_messages = []
                    for update in updates:
                        if 'channel_post' in update:
                            channel_messages.append(update['channel_post'])
                    
                    logging.info(f"Found {len(channel_messages)} channel messages via getUpdates")
                    return channel_messages
                else:
                    logging.error(f"Telegram API error: {result.get('description')}")
            else:
                logging.error(f"Failed to get channel messages: {response.text}")
        except Exception as e:
            logging.error(f"Error getting channel messages: {e}")
        
        return []
    
    def get_channel_messages_alternative(self):
        """Alternative method using forward_from_chat approach"""
        if not self.bot_token:
            logging.error("CARDS_BOT_TOKEN not set")
            return []
        
        # This method requires the bot to be in the channel and have access
        # We'll try to get recent messages
        
        url = f"https://api.telegram.org/bot{self.bot_token}/getChat"
        payload = {
            "chat_id": self.channel_username
        }
        
        try:
            response = requests.post(url, json=payload)
            if response.status_code == 200:
                chat_info = response.json()
                logging.info(f"Channel info: {chat_info}")
                
                # If we can get chat info, try to get messages
                # This might not work for all public channels
                messages_url = f"https://api.telegram.org/bot{self.bot_token}/getChatHistory"
                messages_payload = {
                    "chat_id": self.channel_username,
                    "limit": 50
                }
                
                messages_response = requests.post(messages_url, json=messages_payload)
                if messages_response.status_code == 200:
                    messages_result = messages_response.json()
                    if messages_result.get("ok"):
                        return messages_result.get("result", [])
            else:
                logging.error(f"Failed to get channel info: {response.text}")
        except Exception as e:
            logging.error(f"Error in alternative method: {e}")
        
        return []
    
    def extract_card_id_from_message(self, message):
        """Extract card ID from message text/caption with improved patterns"""
        if not message:
            return None
            
        text = message.get("caption") or message.get("text", "")
        
        if not text:
            return None
        
        # More robust card ID extraction patterns
        patterns = [
            r'(?:ID|Card ID|Card)[:\s]*#?(\d+)',  # "ID: 123", "Card ID: 123", "Card: 123"
            r'^\s*#?(\d+)\s*$',  # Just a number at start/end
            r'[\[\(]#?(\d+)[\]\)]',  # Number in brackets/parentheses
            r'\b(\d{2,4})\b',  # 2-4 digit numbers (common card IDs)
            r'Card\s+#?(\d+)',  # "Card 123"
            r'#(\d+)',  # Hashtag format #123
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    card_id = int(match.group(1))
                    # Validate reasonable card ID range (adjust based on your data)
                    if 1 <= card_id <= 1000:  # Adjust max based on your card count
                        logging.debug(f"Found card ID {card_id} with pattern: {pattern}")
                        return card_id
                except ValueError:
                    continue
        
        # If no pattern matches, try to find any number that could be a card ID
        all_numbers = re.findall(r'\b(\d{2,4})\b', text)
        for num in all_numbers:
            try:
                card_id = int(num)
                if 1 <= card_id <= 1000:  # Adjust based on your card range
                    logging.debug(f"Found potential card ID {card_id} from text numbers")
                    return card_id
            except ValueError:
                continue
        
        return None
    
    def calculate_season(self, upload_date):
        """Calculate season based on upload date (1st season = Jan 2025)"""
        if not upload_date:
            return 1
        
        # Season 1: January 2025, Season 2: February 2025, etc.
        year = upload_date.year
        month = upload_date.month
        
        # Calculate season: (year - 2025) * 12 + month
        season = (year - 2025) * 12 + month
        
        # Ensure season is at least 1
        return max(1, season)
    
    def sync_channel_messages(self):
        """Sync actual channel messages and extract card metadata"""
        if not self.bot_token:
            logging.error("CARDS_BOT_TOKEN not set")
            return
        
        logging.info("Starting Telegram channel message sync...")
        
        # Try different methods to get messages
        all_messages = []
        
        # Method 1: getUpdates (works if bot is in channel)
        logging.info("Trying getUpdates method...")
        messages_method1 = self.get_channel_messages_web(limit=200)
        all_messages.extend(messages_method1)
        
        # Method 2: Alternative approach
        if not all_messages:
            logging.info("Trying alternative method...")
            messages_method2 = self.get_channel_messages_alternative()
            all_messages.extend(messages_method2)
        
        if not all_messages:
            logging.warning("No messages could be retrieved from Telegram channel")
            logging.warning("This might be because:")
            logging.warning("1. The bot is not in the channel")
            logging.warning("2. The channel is private and bot is not admin")
            logging.warning("3. There are no recent messages")
            return
        
        logging.info(f"Total messages fetched: {len(all_messages)}")
        
        # Process messages to extract card metadata
        card_metadata_map = {}
        
        for message in all_messages:
            card_id = self.extract_card_id_from_message(message)
            if card_id:
                # Convert timestamp to datetime
                upload_date = datetime.fromtimestamp(message["date"])
                message_id = message["message_id"]
                
                # Calculate season
                season = self.calculate_season(upload_date)
                
                card_metadata_map[card_id] = {
                    "telegram_message_id": message_id,
                    "upload_date": upload_date,
                    "season": season
                }
                
                logging.debug(f"Found card {card_id} in message {message_id} - Date: {upload_date}, Season: {season}")
        
        logging.info(f"Found {len(card_metadata_map)} cards in channel messages")
        
        if not card_metadata_map:
            logging.warning("No card IDs could be extracted from messages")
            logging.warning("Check if message format contains card IDs")
            return
        
        # Update database with actual metadata
        updated_count = 0
        created_count = 0
        
        for card_id, metadata in card_metadata_map.items():
            existing = CardUploadMetadata.query.filter_by(card_id=card_id).first()
            
            if existing:
                # Update existing record
                existing.telegram_message_id = metadata["telegram_message_id"]
                existing.upload_date = metadata["upload_date"]
                existing.season = metadata["season"]
                updated_count += 1
                logging.debug(f"Updated metadata for card {card_id}")
            else:
                # Create new record
                new_metadata = CardUploadMetadata(
                    card_id=card_id,
                    telegram_message_id=metadata["telegram_message_id"],
                    upload_date=metadata["upload_date"],
                    season=metadata["season"]
                )
                db.session.add(new_metadata)
                created_count += 1
                logging.debug(f"Created metadata for card {card_id}")
        
        try:
            db.session.commit()
            logging.info(f"Sync completed: {created_count} created, {updated_count} updated")
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error saving metadata: {e}")
    
    def manual_date_override(self):
        """Manual method to set dates based on known card information"""
        logging.info("Using manual date override for known cards")
        
        # This is a temporary solution - you should replace these with actual dates
        # from your Telegram channel. Format: {card_id: (year, month, day), ...}
        manual_dates = {
            # Add your actual card dates here based on Telegram message dates
            # Example: 
            # 1: (2025, 1, 15),
            # 2: (2025, 1, 16),
            # ...
        }
        
        for card_id, date_info in manual_dates.items():
            year, month, day = date_info
            upload_date = datetime(year, month, day)
            season = self.calculate_season(upload_date)
            
            existing = CardUploadMetadata.query.filter_by(card_id=card_id).first()
            if existing:
                existing.upload_date = upload_date
                existing.season = season
            else:
                new_metadata = CardUploadMetadata(
                    card_id=card_id,
                    telegram_message_id=0,  # Unknown message ID
                    upload_date=upload_date,
                    season=season
                )
                db.session.add(new_metadata)
        
        try:
            db.session.commit()
            logging.info("Manual date override completed")
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error in manual date override: {e}")

# Global instance
telegram_service = TelegramService()