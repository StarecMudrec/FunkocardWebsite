import os
import requests
from datetime import datetime
from models import db, CardUploadMetadata
import logging

class TelegramService:
    def __init__(self):
        self.bot_token = os.getenv("CARDS_BOT_TOKEN")
        self.channel_username = "@funkocardsall"
    
    def fetch_channel_messages(self, limit=1000, offset_id=0):
        """Fetch messages from Telegram channel"""
        if not self.bot_token:
            logging.error("CARDS_BOT_TOKEN not set")
            return []
        
        url = f"https://api.telegram.org/bot{self.bot_token}/getChatHistory"
        payload = {
            "chat_id": self.channel_username,
            "limit": limit,
            "offset_id": offset_id
        }
        
        try:
            response = requests.post(url, json=payload)
            if response.status_code == 200:
                return response.json().get("result", [])
            else:
                logging.error(f"Telegram API error: {response.text}")
                return []
        except Exception as e:
            logging.error(f"Error fetching channel messages: {e}")
            return []
    
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
    
    def extract_card_id_from_message(self, message):
        """Extract card ID from message text/caption"""
        if not message:
            return None
        
        # Look for card ID in message text/caption
        text = message.get("text") or message.get("caption", "")
        
        # Try to find card ID patterns in the text
        # You might need to adjust this based on how card IDs are displayed in your channel
        import re
        
        # Pattern for numeric card IDs
        numeric_pattern = r'Card\s*#?(\d+)'
        numeric_match = re.search(numeric_pattern, text, re.IGNORECASE)
        if numeric_match:
            return int(numeric_match.group(1))
        
        # Add more patterns as needed based on your channel's format
        
        return None
    
    def sync_channel_messages(self):
        """Sync channel messages to populate upload metadata"""
        messages = self.fetch_channel_messages(limit=1000)
        
        for message in messages:
            card_id = self.extract_card_id_from_message(message)
            if card_id:
                # Check if we already have metadata for this card
                existing_metadata = CardUploadMetadata.query.filter_by(card_id=card_id).first()
                
                if not existing_metadata:
                    # Create new metadata entry
                    upload_date = datetime.fromtimestamp(message["date"])
                    season = self.calculate_season(upload_date)
                    
                    metadata = CardUploadMetadata(
                        card_id=card_id,
                        telegram_message_id=message["message_id"],
                        upload_date=upload_date,
                        season=season
                    )
                    
                    try:
                        db.session.add(metadata)
                        db.session.commit()
                        logging.info(f"Added metadata for card {card_id}")
                    except Exception as e:
                        db.session.rollback()
                        logging.error(f"Error saving metadata for card {card_id}: {e}")

# Global instance
telegram_service = TelegramService()