# create_session.py
from telethon import TelegramClient
import asyncio
import os

async def setup():
    # Replace these with your actual credentials from https://my.telegram.org
    api_id = 123456  # Your actual API ID
    api_hash = 'your_actual_api_hash_here'  # Your actual API hash
    phone_number = '+1234567890'  # Your actual phone number with country code
    
    client = TelegramClient('user_session', api_id, api_hash)
    await client.start(phone=phone_number)
    print('Session created successfully!')
    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(setup())