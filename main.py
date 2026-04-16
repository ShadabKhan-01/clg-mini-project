from fastapi import FastAPI, Request
from agent import get_ai_response
from memory import get_chat_history, save_chat_history
import requests
import json
import redis
from config import TELEGRAM_TOKEN, REDIS_URL
import traceback

app = FastAPI()
redis_client = redis.from_url(REDIS_URL, decode_responses=True) # Upstash URL

def send_telegram_message(chat_id, text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    requests.post(url, json=payload)

@app.post("/webhook/telegram")
async def telegram_webhook(request: Request):
    data = await request.json()
    
    # Safely check that the message actually contains text
    if "message" in data and "text" in data["message"]:
        chat_id = data["message"]["chat"]["id"]
        user_message = data["message"]["text"]
        
        # --- The Redis Cooldown Lock ---
        lock_key = f"lock:{chat_id}"
        
        if redis_client.exists(lock_key):
            # We are removing the warning message so it stops confusing you!
            # Just silently ignore the phantom retries.
            return {"status": "rate_limited"}
            
        # Lock this user out for 3 seconds
        redis_client.setex(lock_key, 3, "locked")
        
        # --- The Safety Net ---
        try:
            # 1. Retrieve history
            chat_history = get_chat_history(chat_id)
            
            # 2. Get AI Response
            ai_reply, updated_history = get_ai_response(chat_history, user_message)
            
            # 3. Send response back
            if ai_reply:
                send_telegram_message(chat_id, ai_reply)
            
            # 4. Save history
            save_chat_history(chat_id, updated_history)
            
        except Exception as e:
            # This prints the TRUE error into your Vercel Logs!
            print("CRITICAL ERROR CAUSING CRASH:")
            traceback.print_exc()
            
            # Tell the user gracefully
            send_telegram_message(chat_id, "I encountered a slight technical glitch. Let's start over, what were we discussing?")
            
            # Wipe their memory so the corrupted state doesn't get stuck
            redis_client.delete(f"chat_history:{chat_id}")

    # ALWAYS return 200 OK so Telegram stops the endless retry loops
    return {"status": "ok"}
    data = await request.json()
    
    if "message" in data:
        chat_id = data["message"]["chat"]["id"]
        user_message = data["message"]["text"]
        
        # --- NEW: The Redis Cooldown Lock ---
        lock_key = f"lock:{chat_id}"
        
        # If the user messaged in the last 3 seconds, ignore them to save quota
        if redis_client.exists(lock_key):
            # Optional: Send a warning to the user
            send_telegram_message(chat_id, "You are messaging too fast! Please wait a moment.")
            return {"status": "rate_limited"}
            
        # Lock this user out for 3 seconds
        redis_client.setex(lock_key, 3, "locked")
        # -------------------------------------
        
        # 1. Retrieve history from Redis (from memory.py)
        chat_history = get_chat_history(chat_id)
        
        # 2. Get AI Response
        ai_reply, updated_history = get_ai_response(chat_history, user_message)
        
        # 3. Send response back to Telegram
        send_telegram_message(chat_id, ai_reply)
        
        # 4. Save updated history back to Redis
        save_chat_history(chat_id, updated_history)

    return {"status": "ok"}