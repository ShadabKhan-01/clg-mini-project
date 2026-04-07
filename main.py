from fastapi import FastAPI, Request
from agent import get_ai_response
import requests
import json
import redis
from config import TELEGRAM_TOKEN, REDIS_URL

app = FastAPI()
redis_client = redis.from_url(REDIS_URL, decode_responses=True) # Upstash URL

def send_telegram_message(chat_id, text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    requests.post(url, json=payload)

@app.post("/webhook/telegram")
async def telegram_webhook(request: Request):
    data = await request.json()
    
    if "message" in data:
        chat_id = data["message"]["chat"]["id"]
        user_message = data["message"]["text"]
        
        # 1. Retrieve history from Redis (Upstash)
        history_key = f"chat_history:{chat_id}"
        raw_history = redis_client.get(history_key)
        
        # Pylance Fix: Explicitly check if it is a string to satisfy the type checker
        if isinstance(raw_history, str):
            chat_history = json.loads(raw_history)
        else:
            chat_history = []
        
        # 2. Get Gemini Response (Will automatically call Cal.com if needed)
        ai_reply, updated_history = get_ai_response(chat_history, user_message)
        
        # 3. Send response back to Telegram
        send_telegram_message(chat_id, ai_reply)
        
        # 4. Save updated history back to Redis (expire after 24 hours)
        # Format history to be JSON serializable for Gemini
        formatted_history = [{"role": m.role, "parts": [{"text": p.text} for p in m.parts]} for m in updated_history]
        redis_client.setex(history_key, 86400, json.dumps(formatted_history))

    return {"status": "ok"}