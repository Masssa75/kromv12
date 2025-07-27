import requests
import json
import time

# Your premium bot token
BOT_TOKEN = "7558329908:AAGPBE3MSAVYownFJq1eOouQmsQPNqU1yt0"

print("Getting group ID using your bot token...")
print("\nIMPORTANT: This will only work if:")
print("1. The bot is already in the group")
print("2. Someone has sent a message in the group recently")
print("3. The bot has permission to read messages\n")

# First, delete the webhook to allow getUpdates
delete_webhook_url = f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook"
response = requests.post(delete_webhook_url)
print("Deleting webhook:", response.json())

time.sleep(1)

# Get updates
get_updates_url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
response = requests.get(get_updates_url)
data = response.json()

if data.get("ok"):
    updates = data.get("result", [])
    
    if not updates:
        print("\nNo recent messages found.")
        print("Please send a message in your group and run this script again.")
    else:
        print(f"\nFound {len(updates)} updates:\n")
        
        groups_found = set()
        
        for update in updates:
            if "message" in update:
                chat = update["message"].get("chat", {})
                chat_id = chat.get("id")
                chat_title = chat.get("title", "Private Chat")
                chat_type = chat.get("type", "unknown")
                
                if chat_type in ["group", "supergroup"]:
                    groups_found.add((chat_id, chat_title, chat_type))
        
        if groups_found:
            print("Groups found:")
            for chat_id, title, chat_type in groups_found:
                print(f"\nGroup: {title}")
                print(f"ID: {chat_id}")
                print(f"Type: {chat_type}")
                print("-" * 40)
        else:
            print("No group messages found. Only private messages detected.")
            
else:
    print("Error:", data.get("description", "Unknown error"))

print("\n\nREMEMBER: After getting the group ID, run the webhook setup script again!")
print("Run: node setup-telegram-webhook.js")