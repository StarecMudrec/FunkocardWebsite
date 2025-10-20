import os
import requests
from datetime import datetime
from models import db, CardUploadMetadata
import logging
import time

class TelegramService:
    def __init__(self):
        self.bot_token = os.getenv("CARDS_BOT_TOKEN")
        self.channel_username = "@funkocardsall"
    
    def get_channel_messages(self, limit=100, offset_id=0):
        """Get messages from public channel"""
        if not self.bot_token:
            logging.error("CARDS_BOT_TOKEN not set")
            return []
        
        url = f"https://api.telegram.org/bot{self.bot_token}/getChatHistory"
        payload = {
            "chat_id": self.channel_username,
            "limit": limit
        }
        
        if offset_id > 0:
            payload["from_message_id"] = offset_id
        
        try:
            response = requests.post(url, json=payload)
            if response.status_code == 200:
                result = response.json()
                if result.get("ok"):
                    return result.get("result", [])
                else:
                    logging.error(f"Telegram API error: {result.get('description')}")
            else:
                logging.error(f"Failed to get channel messages: {response.text}")
        except Exception as e:
            logging.error(f"Error getting channel messages: {e}")
        
        return []
    
    def extract_card_id_from_message(self, message):
        """Extract card ID from message text/caption"""
        if not message:
            return None
            
        text = message.get("caption") or message.get("text", "")
        
        # Look for card ID patterns in the message
        # Common patterns: "ID: 123", "Card ID: 123", or just a number
        import re
        
        # Pattern 1: "ID: 123" or "Card ID: 123"
        id_pattern1 = re.search(r'(?:ID|Card ID)[:\s]*(\d+)', text, re.IGNORECASE)
        if id_pattern1:
            return int(id_pattern1.group(1))
        
        # Pattern 2: Just a number at the start or prominent position
        id_pattern2 = re.search(r'^\s*(\d+)\s*$', text.strip())
        if id_pattern2:
            return int(id_pattern2.group(1))
            
        # Pattern 3: Number in brackets or parentheses
        id_pattern3 = re.search(r'[\[\(](\d+)[\]\)]', text)
        if id_pattern3:
            return int(id_pattern3.group(1))
        
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
        
        all_messages = []
        offset_id = 0
        batch_size = 100
        
        # Fetch all messages from the channel
        while True:
            messages = self.get_channel_messages(limit=batch_size, offset_id=offset_id)
            if not messages:
                break
                
            all_messages.extend(messages)
            logging.info(f"Fetched {len(messages)} messages, total: {len(all_messages)}")
            
            if len(messages) < batch_size:
                break
                
            # Get the oldest message ID for next batch
            offset_id = min(msg["message_id"] for msg in messages) - 1
            time.sleep(0.5)  # Rate limiting
        
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
        
        logging.info(f"Found {len(card_metadata_map)} cards in channel messages")
        
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
        
        try:
            db.session.commit()
            logging.info(f"Sync completed: {created_count} created, {updated_count} updated")
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error saving metadata: {e}")

# Global instance
telegram_service = TelegramService()