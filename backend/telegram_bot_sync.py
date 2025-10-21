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

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class TelegramBotSync:
    def __init__(self):
        self.api_id = os.getenv("TELEGRAM_API_ID")
        self.api_hash = os.getenv("TELEGRAM_API_HASH")
        self.bot_token = os.getenv("CARDS_BOT_TOKEN")
        self.channel_username = '@funkocardsall'
        
    async def sync_messages_async(self):
        """Sync using bot token (non-interactive)"""
        if not all([self.api_id, self.api_hash, self.bot_token]):
            logging.error("Missing Telegram bot credentials")
            return False
        
        # Use bot token directly - no phone number or interactive auth needed
        client = TelegramClient(
            session='bot_session', 
            api_id=int(self.api_id), 
            api_hash=self.api_hash
        )
        
        try:
            # Start with bot token - this should work without interactive input
            await client.start(bot_token=self.bot_token)
            logging.info("Telegram bot client started successfully")
            
            # Verify connection
            me = await client.get_me()
            logging.info(f"Bot connected as: @{me.username}")
            
            # Try to access the channel
            try:
                channel = await client.get_entity(self.channel_username)
                logging.info(f"Accessing channel: {channel.title}")
            except Exception as e:
                logging.error(f"Cannot access channel {self.channel_username}: {e}")
                logging.error("Make sure the bot is added to the channel as an admin")
                return False
            
            # Fetch messages from the channel
            messages = []
            try:
                async for message in client.iter_messages(channel, limit=500):
                    messages.append(message)
                    if len(messages) % 50 == 0:
                        logging.info(f"Fetched {len(messages)} messages...")
                
                logging.info(f"Total messages fetched: {len(messages)}")
                
                # Process the messages (your existing logic here)
                processed_count = await self.process_messages(messages)
                logging.info(f"Processed {processed_count} messages")
                
                return True
                
            except Exception as e:
                logging.error(f"Error fetching messages: {e}")
                return False
                
        except Exception as e:
            logging.error(f"Error in bot sync: {e}")
            return False
        finally:
            await client.disconnect()
    
    async def process_messages(self, messages):
        """Process messages and update database"""
        # Your existing message processing logic here
        logging.info(f"Processing {len(messages)} messages")
        return len(messages)

def main():
    """Main function"""
    logging.info("Starting Telegram bot sync...")
    sync = TelegramBotSync()
    
    try:
        success = asyncio.run(sync.sync_messages_async())
        exit(0 if success else 1)
    except Exception as e:
        logging.error(f"Sync failed: {e}")
        exit(1)

if __name__ == "__main__":
    main()