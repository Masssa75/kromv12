#!/usr/bin/env python3
"""
Test the Telegram notification for token discovery
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

# Get Telegram credentials (using ATH bot for now)
bot_token = os.getenv('TELEGRAM_BOT_TOKEN_ATH')
chat_id = os.getenv('TELEGRAM_GROUP_ID_ATH')

if not bot_token or not chat_id:
    print("❌ Missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID in .env")
    exit(1)

# Create test message
message = """🌐 <b>TEST: New Token with Website/Socials!</b>

<b>Token:</b> TEST (SOLANA)
<b>Liquidity:</b> $250K

<b>Found:</b>
🔗 Website: https://example.com
🐦 Twitter: https://x.com/example
💬 Telegram: https://t.me/example

📊 <a href="https://dexscreener.com/solana/test">View on DexScreener</a>

<i>This is a test notification from the token discovery system.</i>"""

# Send notification
url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
payload = {
    "chat_id": chat_id,
    "text": message,
    "parse_mode": "HTML",
    "disable_web_page_preview": False
}

response = requests.post(url, json=payload)

if response.ok:
    print(f"✅ Test notification sent successfully!")
    print(f"Response: {response.json()}")
else:
    print(f"❌ Failed to send notification")
    print(f"Error: {response.text}")