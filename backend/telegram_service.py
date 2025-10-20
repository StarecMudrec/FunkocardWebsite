import os
import requests
from datetime import datetime
from models import db, CardUploadMetadata
import logging

class TelegramService:
    def __init__(self):
        self.bot_token = os.getenv("CARDS_BOT_TOKEN")
        self.channel_username = "@funkocardsall"
    
    def fetch_channel_messages(self, limit=100, offset_id=0):
        """Fetch messages from Telegram channel"""
        if not self.bot_token:
            logging.error("CARDS_BOT_TOKEN not set")
            return []
        
        # Use getUpdates method instead of getChatHistory for public channels
        url = f"https://api.telegram.org/bot{self.bot_token}/getUpdates"
        
        try:
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                if data.get("ok"):
                    return data.get("result", [])
                else:
                    logging.error(f"Telegram API error: {data}")
                    return []
            else:
                logging.error(f"Telegram API HTTP error: {response.status_code}")
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
        text = message.get("message", {}).get("text") or message.get("message", {}).get("caption", "")
        
        if not text:
            return None
            
        # Try to find card ID patterns in the text
        import re
        
        # Pattern 1: Look for numbers that could be card IDs (3-4 digits)
        number_pattern = r'\b(\d{3,4})\b'
        number_matches = re.findall(number_pattern, text)
        
        # Pattern 2: Look for "Card #123" pattern
        card_pattern = r'[Cc]ard\s*#?\s*(\d+)'
        card_match = re.search(card_pattern, text)
        
        # Pattern 3: Look for card names that might match your database
        # You'll need to adjust this based on your actual card names
        
        # Priority: card pattern matches first
        if card_match:
            return int(card_match.group(1))
        
        # Then try number matches
        for match in number_matches:
            card_id = int(match)
            # Validate that this could be a real card ID (adjust range as needed)
            if 1 <= card_id <= 2000:  # Adjust max based on your card count
                return card_id
        
        return None
    
    def sync_channel_messages(self):
        """Sync channel messages to populate upload metadata"""
        try:
            messages = self.fetch_channel_messages(limit=100)
            logging.info(f"Fetched {len(messages)} messages from Telegram")
            
            if not messages:
                logging.warning("No messages fetched from Telegram")
                return
            
            processed_count = 0
            new_entries = 0
            
            for message_data in messages:
                message = message_data.get("message", {})
                if not message:
                    continue
                    
                card_id = self.extract_card_id_from_message(message_data)
                if card_id:
                    processed_count += 1
                    
                    # Check if we already have metadata for this card
                    existing_metadata = CardUploadMetadata.query.filter_by(card_id=card_id).first()
                    
                    if not existing_metadata:
                        # Create new metadata entry
                        upload_date = datetime.fromtimestamp(message.get("date", 0))
                        season = self.calculate_season(upload_date)
                        
                        metadata = CardUploadMetadata(
                            card_id=card_id,
                            telegram_message_id=message.get("message_id", 0),
                            upload_date=upload_date,
                            season=season
                        )
                        
                        try:
                            db.session.add(metadata)
                            new_entries += 1
                            logging.info(f"Added metadata for card {card_id} (uploaded: {upload_date}, season: {season})")
                        except Exception as e:
                            logging.error(f"Error saving metadata for card {card_id}: {e}")
            
            # Commit all changes at once
            if new_entries > 0:
                db.session.commit()
                logging.info(f"Successfully added {new_entries} new card metadata entries")
            else:
                logging.info(f"Processed {processed_count} messages, no new entries added")
                
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error during sync: {e}")

# Global instance
telegram_service = TelegramService()