import os
import asyncio
import logging
from datetime import datetime
from telethon import TelegramClient
from telethon.sessions import StringSession
import pymysql
import sys

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
        """Sync using user account with better error handling"""
        if not all([self.api_id, self.api_hash, self.phone_number]):
            logging.error("Telegram user credentials not set")
            return False
        
        client = TelegramClient(self.session_name, int(self.api_id), self.api_hash)
        
        try:
            # Check if we're in an interactive environment
            if sys.stdin.isatty():
                # Interactive mode
                await client.start(phone=self.phone_number)
            else:
                # Non-interactive mode (Docker)
                try:
                    await client.start(phone=self.phone_number)
                    logging.info("Telegram client started successfully")
                except Exception as e:
                    logging.error(f"Failed to start client in non-interactive mode: {e}")
                    logging.info("Session file may need to be created interactively first")
                    return False
            
            # Rest of your sync logic...
            channel = await client.get_entity(self.channel_username)
            logging.info(f"Accessing channel: {channel.title}")
            
            messages = []
            async for message in client.iter_messages(channel, limit=1000):
                messages.append(message)
                if len(messages) % 100 == 0:
                    logging.info(f"Fetched {len(messages)} messages...")
            
            logging.info(f"Total messages fetched: {len(messages)}")
            
            # Process messages and update database
            success = await self.process_messages(messages)
            
            return success
            
        except Exception as e:
            logging.error(f"Error in user sync: {e}")
            return False
        finally:
            await client.disconnect()
    
    async def process_messages(self, messages):
        """Process messages and update database"""
        try:
            # Your database processing logic here
            logging.info(f"Processing {len(messages)} messages")
            return True
        except Exception as e:
            logging.error(f"Error processing messages: {e}")
            return False

def main():
    sync = TelegramUserSync()
    success = asyncio.run(sync.sync_messages_async())
    exit(0 if success else 1)

if __name__ == "__main__":
    main()