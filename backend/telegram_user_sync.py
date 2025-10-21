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

class TelegramUserSync:
    def __init__(self):
        self.api_id = os.getenv("TELEGRAM_API_ID")
        self.api_hash = os.getenv("TELEGRAM_API_HASH")
        self.phone_number = os.getenv("TELEGRAM_PHONE_NUMBER")
        self.session_name = 'funkocards_user_session'
        self.channel_username = '@funkocardsall'
        
    async def sync_messages_async(self):
        """Sync using user account (interactive setup required first)"""
        if not all([self.api_id, self.api_hash, self.phone_number]):
            logging.error("Telegram user credentials not set")
            return False
        
        client = TelegramClient(self.session_name, int(self.api_id), self.api_hash)
        
        try:
            # This will use existing session if available
            await client.start(phone=self.phone_number)
            logging.info("Telegram user client started successfully")
            
            # Get channel and messages (user accounts can do this)
            channel = await client.get_entity(self.channel_username)
            logging.info(f"Accessing channel: {channel.title}")
            
            messages = []
            async for message in client.iter_messages(channel, limit=1000):
                messages.append(message)
                if len(messages) % 100 == 0:
                    logging.info(f"Fetched {len(messages)} messages...")
            
            logging.info(f"Total messages fetched: {len(messages)}")
            
            # Process messages and update database (similar to previous implementations)
            # ... database code here ...
            
            return True
            
        except Exception as e:
            logging.error(f"Error in user sync: {e}")
            return False
        finally:
            await client.disconnect()

def setup_user_session():
    """Run this once interactively to setup the user session"""
    sync = TelegramUserSync()
    
    async def setup():
        client = TelegramClient(sync.session_name, int(sync.api_id), sync.api_hash)
        await client.start(phone=sync.phone_number)
        print("Session setup complete!")
        await client.disconnect()
    
    asyncio.run(setup())

if __name__ == "__main__":
    # For first-time setup, run: python telegram_user_sync.py setup
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "setup":
        setup_user_session()
    else:
        sync = TelegramUserSync()
        success = asyncio.run(sync.sync_messages_async())
        exit(0 if success else 1)