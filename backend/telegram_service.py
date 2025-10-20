import os
import requests
from datetime import datetime
from models import db, CardUploadMetadata
import logging

class TelegramService:
    def __init__(self):
        self.bot_token = os.getenv("CARDS_BOT_TOKEN")
        self.channel_username = "@funkocardsall"
    
    def get_channel_messages(self, limit=100):
        """Get messages from public channel using forward_from_chat method"""
        if not self.bot_token:
            logging.error("CARDS_BOT_TOKEN not set")
            return []
        
        # For public channels, we need to use a different approach
        # This is a simplified version - you might need to adjust based on your channel
        url = f"https://api.telegram.org/bot{self.bot_token}/getChat"
        payload = {
            "chat_id": self.channel_username
        }
        
        try:
            response = requests.post(url, json=payload)
            if response.status_code == 200:
                chat_info = response.json()
                logging.info(f"Channel info: {chat_info}")
            else:
                logging.error(f"Failed to get channel info: {response.text}")
        except Exception as e:
            logging.error(f"Error getting channel info: {e}")
        
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
    
    def sync_channel_messages(self):
        """Sync channel messages - currently uses manual data"""
        logging.info("Using manual data population instead of Telegram API")
        # For now, we'll rely on the manual population in app.py
        # You can enhance this later with proper Telegram channel access

# Global instance
telegram_service = TelegramService()