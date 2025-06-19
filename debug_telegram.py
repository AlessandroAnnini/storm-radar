#!/usr/bin/env python3
"""Debug Telegram configuration and API"""

import requests
from src.storm_radar.config import Configuration


def debug_telegram():
    """Debug Telegram configuration"""
    config = Configuration()

    print("🔍 Debugging Telegram Configuration...")
    print(
        f"Bot Token: {config.TELEGRAM_BOT_TOKEN[:20]}..."
        if len(config.TELEGRAM_BOT_TOKEN) > 20
        else f"Bot Token: {config.TELEGRAM_BOT_TOKEN}"
    )
    print(f"Chat ID: {config.TELEGRAM_CHAT_ID}")

    # Check token format
    token_parts = config.TELEGRAM_BOT_TOKEN.split(":")
    token_valid = len(token_parts) == 2 and len(token_parts[0]) > 5 and len(token_parts[1]) > 20
    print(f"Token format valid: {token_valid}")

    # Check if chat ID is numeric
    chat_id_numeric = config.TELEGRAM_CHAT_ID.lstrip("-").isdigit()
    print(f"Chat ID numeric: {chat_id_numeric}")

    # Test bot info
    print("\n🤖 Testing bot info...")
    try:
        url = f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/getMe"
        response = requests.get(url, timeout=10)
        print(f"Bot info status: {response.status_code}")
        if response.status_code == 200:
            bot_info = response.json()
            print(f"Bot username: @{bot_info['result']['username']}")
            print(f"Bot first name: {bot_info['result']['first_name']}")
        else:
            print(f"Bot info error: {response.text}")
    except Exception as e:
        print(f"Bot info failed: {e}")

    # Test simple message
    print("\n📤 Testing simple message...")
    try:
        url = f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/sendMessage"

        # Try with simple text first
        payload = {"chat_id": config.TELEGRAM_CHAT_ID, "text": "Simple test message"}

        response = requests.post(url, json=payload, timeout=10)
        print(f"Simple message status: {response.status_code}")
        if response.status_code != 200:
            print(f"Simple message error: {response.text}")
        else:
            print("✅ Simple message sent successfully!")

    except Exception as e:
        print(f"Simple message failed: {e}")

    # Test markdown message
    print("\n📝 Testing markdown message...")
    try:
        payload = {
            "chat_id": config.TELEGRAM_CHAT_ID,
            "text": "*Bold text* and _italic text_",
            "parse_mode": "Markdown",
        }

        response = requests.post(url, json=payload, timeout=10)
        print(f"Markdown message status: {response.status_code}")
        if response.status_code != 200:
            print(f"Markdown message error: {response.text}")
        else:
            print("✅ Markdown message sent successfully!")

    except Exception as e:
        print(f"Markdown message failed: {e}")


if __name__ == "__main__":
    debug_telegram()
