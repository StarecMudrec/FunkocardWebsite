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
    
    def normalize_card_name(self, name):
        """Normalize card name for matching - handles different formats"""
        if not name:
            return ""
        
        # Convert to lowercase and remove accents
        normalized = unidecode(name).lower()
        
        # Remove common prefixes/suffixes and special characters
        normalized = re.sub(r'[^\w\s]', ' ', normalized)
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        
        return normalized
    
    def extract_card_name_from_message(self, message_text):
        """Extract the main card name from Telegram message text"""
        if not message_text:
            return None
        
        # Pattern to match the card name format (text before numbers)
        # Example: "Coraline in Raincoat\n1492-1497" -> "Coraline in Raincoat"
        match = re.match(r'^([^\d\n]+)', message_text.strip())
        if match:
            card_name = match.group(1).strip()
            return self.normalize_card_name(card_name)
        
        return None
    
    def find_card_in_messages(self, card_name, messages):
        """Find a card by name in the channel messages using improved matching"""
        if not card_name or not messages:
            return None
        
        normalized_card_name = self.normalize_card_name(card_name)
        logging.debug(f"Searching for card: '{card_name}' (normalized: '{normalized_card_name}')")
        
        best_match = None
        best_score = 0
        
        for message in messages:
            message_text = message.get("caption") or message.get("text", "")
            if not message_text:
                continue
            
            # Extract card name from message
            message_card_name = self.extract_card_name_from_message(message_text)
            if not message_card_name:
                continue
            
            # Exact match
            if normalized_card_name == message_card_name:
                logging.debug(f"Exact match found for '{card_name}' in message")
                return message
            
            # Calculate word-based similarity
            card_words = set(normalized_card_name.split())
            message_words = set(message_card_name.split())
            
            if card_words:
                common_words = card_words.intersection(message_words)
                similarity = len(common_words) / len(card_words)
                
                if similarity > best_score:
                    best_score = similarity
                    best_match = message
        
        # Use fuzzy match if good enough
        if best_match and best_score >= 0.7:  # 70% word match
            message_text = best_match.get("caption") or best_match.get("text", "")
            extracted_name = self.extract_card_name_from_message(message_text)
            logging.debug(f"Fuzzy match found for '{card_name}' (score: {best_score:.2f}) as '{extracted_name}'")
            return best_match
        
        logging.debug(f"No match found for card: '{card_name}'")
        return None
    
    def calculate_season_from_date(self, upload_date):
        """Calculate season based on actual upload date with proper season boundaries"""
        if not upload_date:
            return 1
        
        # Define season boundaries (adjust these based on your actual season dates)
        num_seasons = 120
        start_year = 2025

        season_boundaries = [datetime(start_year + (season - 1) // 12, ((season - 1) % 12) + 1, 15) for season in range(1, num_seasons + 1)]
        
        # Find which season this date falls into
        for season_num, season_start in enumerate(season_boundaries, 1):
            if upload_date >= season_start:
                # Check if there's a next season boundary
                if season_num < len(season_boundaries):
                    season_end = season_boundaries[season_num]
                    if upload_date < season_end:
                        return season_num
                else:
                    # This is the latest season
                    return season_num
        
        # If before first season, return season 1
        return 1
    
    def calculate_season_from_card_id(self, card_id):
        """Fallback season calculation based on card ID ranges"""
        # Adjust these ranges based on your actual card ID distribution
        if card_id >= 400:
            return 3
        elif card_id >= 350:
            return 2
        elif card_id >= 300:
            return 1
        elif card_id >= 200:
            return 1
        else:
            return 1
    
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
            
            # Sort messages by date to process oldest first (more logical season assignment)
            messages.sort(key=lambda x: x.get("date", 0))
            
            # Process each card
            updated_count = 0
            created_count = 0
            not_found_count = 0
            
            for card in all_cards:
                card_id = card['id']
                card_name = card['name']
                
                # Skip if we already have good metadata for this card
                existing = CardUploadMetadata.query.filter_by(card_id=card_id).first()
                if existing and existing.telegram_message_id > 0 and existing.upload_date:
                    logging.debug(f"Card {card_id} already has good metadata, skipping")
                    continue
                
                # Find card in messages
                matching_message = self.find_card_in_messages(card_name, messages)
                
                if matching_message:
                    # Extract metadata from message
                    upload_date = datetime.fromtimestamp(matching_message["date"])
                    message_id = matching_message["message_id"]
                    
                    # Calculate season based on actual upload date
                    season = self.calculate_season_from_date(upload_date)
                    
                    if existing:
                        # Update existing record
                        existing.telegram_message_id = message_id
                        existing.upload_date = upload_date
                        existing.season = season
                        updated_count += 1
                        logging.debug(f"Updated card '{card_name}' (ID: {card_id}) - Date: {upload_date}, Season: {season}")
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
                        logging.debug(f"Created metadata for card '{card_name}' (ID: {card_id}) - Date: {upload_date}, Season: {season}")
                else:
                    not_found_count += 1
                    logging.warning(f"Card '{card_name}' (ID: {card_id}) not found in channel messages")
                    
                    # For cards not found, create fallback metadata
                    if not existing:
                        fallback_season = self.calculate_season_from_card_id(card_id)
                        fallback_date = self.get_fallback_date(card_id, fallback_season)
                        
                        new_metadata = CardUploadMetadata(
                            card_id=card_id,
                            telegram_message_id=0,  # Indicates not found in channel
                            upload_date=fallback_date,
                            season=fallback_season
                        )
                        db.session.add(new_metadata)
                        created_count += 1
                        logging.debug(f"Created fallback metadata for card '{card_name}' (ID: {card_id}) - Season: {fallback_season}")
            
            # Commit all changes
            db.session.commit()
            logging.info(f"Sync completed: {created_count} created, {updated_count} updated, {not_found_count} not found")
            
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error during sync: {e}")
        finally:
            connection.close()
    
    def get_fallback_date(self, card_id, season):
        """Get a reasonable fallback date based on season and card ID"""
        # Base dates for each season

        num_seasons=120
        start_year=2025

        season_base_dates = {
            season: datetime(start_year + (season - 1) // 12, ((season - 1) % 12) + 1, 15)
            for season in range(1, num_seasons + 1)
        }
        
        base_date = season_base_dates.get(season, datetime(2025, 1, 15))
        
        # Add some variation based on card ID to avoid all having same date
        days_variation = card_id % 30  # Spread over about a month
        
        return base_date.replace(day=min(28, 15 + (days_variation % 14)))  # Keep within month
    
    def manual_date_override(self):
        """Manual method to set dates for specific cards"""
        logging.info("Using manual date override for specific cards")
        
        # Add specific card dates here if you know them
        # Format: card_id: (year, month, day, season)
        manual_cards = {
            # Example: 
            # 336: (2025, 2, 10, 2),
        }
        
        for card_id, date_info in manual_cards.items():
            year, month, day, season = date_info
            upload_date = datetime(year, month, day)
            
            existing = CardUploadMetadata.query.filter_by(card_id=card_id).first()
            if existing:
                existing.upload_date = upload_date
                existing.season = season
                existing.telegram_message_id = -1  # Mark as manually set
                logging.debug(f"Updated manual date for card {card_id}")
            else:
                new_metadata = CardUploadMetadata(
                    card_id=card_id,
                    telegram_message_id=-1,  # Manually set
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