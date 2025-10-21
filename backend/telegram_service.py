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
        """Get all messages from the channel using iterative approach"""
        if not self.bot_token:
            logging.error("CARDS_BOT_TOKEN not set")
            return []
        
        all_messages = []
        offset = 0
        limit = 100
        max_messages = 1000  # Safety limit
        
        logging.info("Starting to fetch all channel messages...")
        
        while len(all_messages) < max_messages:
            url = f"https://api.telegram.org/bot{self.bot_token}/getUpdates"
            payload = {
                "offset": offset,
                "limit": limit,
                "timeout": 10
            }
            
            try:
                response = requests.post(url, json=payload, timeout=30)
                if response.status_code == 200:
                    result = response.json()
                    if result.get("ok"):
                        updates = result.get("result", [])
                        
                        if not updates:
                            break  # No more messages
                        
                        # Filter for channel posts and collect messages
                        for update in updates:
                            if 'channel_post' in update:
                                message = update['channel_post']
                                all_messages.append(message)
                                
                                # Update offset to get next batch
                                offset = update['update_id'] + 1
                        
                        logging.info(f"Fetched {len(updates)} updates, total messages: {len(all_messages)}")
                        
                        # Small delay to avoid rate limiting
                        time.sleep(0.1)
                    else:
                        logging.error(f"Telegram API error: {result.get('description')}")
                        break
                else:
                    logging.error(f"Failed to get updates: {response.text}")
                    break
                    
            except Exception as e:
                logging.error(f"Error fetching messages: {e}")
                break
        
        logging.info(f"Total channel messages fetched: {len(all_messages)}")
        return all_messages
    
    def normalize_text(self, text):
        """Normalize text for comparison - remove accents, lowercase, etc."""
        if not text:
            return ""
        
        # Convert to lowercase and remove accents
        normalized = unidecode(text).lower()
        
        # Remove extra spaces and special characters
        normalized = re.sub(r'[^\w\s]', ' ', normalized)
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        
        return normalized
    
    def find_card_in_messages(self, card_name, messages):
        """Find a card by name in the channel messages"""
        if not card_name or not messages:
            return None
        
        normalized_card_name = self.normalize_text(card_name)
        logging.debug(f"Searching for card: '{card_name}' (normalized: '{normalized_card_name}')")
        
        best_match = None
        best_score = 0
        
        for message in messages:
            message_text = message.get("caption") or message.get("text", "")
            if not message_text:
                continue
            
            normalized_message = self.normalize_text(message_text)
            
            # Simple exact match first
            if normalized_card_name in normalized_message:
                logging.debug(f"Exact match found for '{card_name}' in message: {message_text[:100]}...")
                return message
            
            # Calculate similarity score for fuzzy matching
            card_words = set(normalized_card_name.split())
            message_words = set(normalized_message.split())
            
            if card_words:
                common_words = card_words.intersection(message_words)
                similarity = len(common_words) / len(card_words)
                
                if similarity > best_score:
                    best_score = similarity
                    best_match = message
        
        # If we have a reasonably good fuzzy match, use it
        if best_match and best_score >= 0.5:  # At least 50% of words match
            message_text = best_match.get("caption") or best_match.get("text", "")
            logging.debug(f"Fuzzy match found for '{card_name}' (score: {best_score:.2f}) in message: {message_text[:100]}...")
            return best_match
        
        logging.debug(f"No match found for card: '{card_name}'")
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
    
    def get_card_upload_date(self, card_id, card_name):
        """Get the upload date for a specific card by searching in channel messages"""
        if not card_name:
            logging.warning(f"No card name provided for card ID {card_id}")
            return None
        
        logging.info(f"Searching for card '{card_name}' (ID: {card_id}) in channel messages...")
        
        # Get all channel messages
        messages = self.get_all_channel_messages()
        if not messages:
            logging.warning("No messages retrieved from channel")
            return None
        
        # Find the card in messages
        matching_message = self.find_card_in_messages(card_name, messages)
        
        if matching_message:
            # Extract date from the message
            upload_date = datetime.fromtimestamp(matching_message["date"])
            message_id = matching_message["message_id"]
            
            logging.info(f"Found card '{card_name}' in message {message_id} - Upload date: {upload_date}")
            return {
                "telegram_message_id": message_id,
                "upload_date": upload_date,
                "season": self.calculate_season(upload_date)
            }
        else:
            logging.warning(f"Could not find card '{card_name}' in any channel messages")
            return None
    
    def sync_channel_messages(self):
        """Sync card metadata by searching for card names in channel messages"""
        if not self.bot_token:
            logging.error("CARDS_BOT_TOKEN not set")
            return
        
        logging.info("Starting Telegram channel message sync by card name search...")
        
        # Get all cards from MySQL database
        from app import get_db_conn
        connection = get_db_conn()
        if not connection:
            logging.error("Cannot connect to MySQL database")
            return
        
        try:
            with connection.cursor() as cursor:
                # Get all cards (id and name)
                cursor.execute("""
                    SELECT id, name 
                    FROM files 
                    WHERE name NOT IN ('срать в помогатор апельсины', 'test', 'фаланга пальца')
                """)
                all_cards = cursor.fetchall()
                
            logging.info(f"Found {len(all_cards)} cards in database to sync")
            
            # Get all channel messages once
            messages = self.get_all_channel_messages()
            if not messages:
                logging.warning("No messages retrieved from channel, cannot sync")
                return
            
            # Process each card
            updated_count = 0
            created_count = 0
            not_found_count = 0
            
            for card in all_cards:
                card_id = card['id']
                card_name = card['name']
                
                # Skip if we already have metadata for this card
                existing = CardUploadMetadata.query.filter_by(card_id=card_id).first()
                if existing and existing.telegram_message_id > 0:
                    logging.debug(f"Card {card_id} already has metadata, skipping")
                    continue
                
                # Find card in messages
                matching_message = self.find_card_in_messages(card_name, messages)
                
                if matching_message:
                    # Extract metadata from message
                    upload_date = datetime.fromtimestamp(matching_message["date"])
                    message_id = matching_message["message_id"]
                    season = self.calculate_season(upload_date)
                    
                    if existing:
                        # Update existing record
                        existing.telegram_message_id = message_id
                        existing.upload_date = upload_date
                        existing.season = season
                        updated_count += 1
                    else:
                        # Create new record
                        new_metadata = CardUploadMetadata(
                            card_id=card_id,
                            telegram_message_id=message_id,
                            upload_date=upload_date,
                            season=season
                        )
                        db.session.add(new_metadata)
                        created_count += 1
                    
                    logging.debug(f"Synced card '{card_name}' (ID: {card_id}) - Date: {upload_date}, Season: {season}")
                else:
                    not_found_count += 1
                    logging.debug(f"Card '{card_name}' (ID: {card_id}) not found in channel messages")
            
            # Commit all changes
            db.session.commit()
            logging.info(f"Sync completed: {created_count} created, {updated_count} updated, {not_found_count} not found")
            
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error during sync: {e}")
        finally:
            connection.close()
    
    def manual_date_override(self):
        """Manual method to set dates for cards that couldn't be found automatically"""
        logging.info("Using manual date override for cards not found in channel")
        
        # This should only be used as a last resort
        # You can add specific card dates here if you know them
        manual_dates = {
            # Format: card_id: (year, month, day)
            # Example: 1: (2025, 1, 15),
        }
        
        for card_id, date_info in manual_dates.items():
            year, month, day = date_info
            upload_date = datetime(year, month, day)
            season = self.calculate_season(upload_date)
            
            existing = CardUploadMetadata.query.filter_by(card_id=card_id).first()
            if existing:
                existing.upload_date = upload_date
                existing.season = season
                logging.debug(f"Updated manual date for card {card_id}")
            else:
                new_metadata = CardUploadMetadata(
                    card_id=card_id,
                    telegram_message_id=0,  # Unknown message ID
                    upload_date=upload_date,
                    season=season
                )
                db.session.add(new_metadata)
                logging.debug(f"Created manual date for card {card_id}")
        
        try:
            db.session.commit()
            logging.info("Manual date override completed")
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error in manual date override: {e}")

# Global instance
telegram_service = TelegramService()