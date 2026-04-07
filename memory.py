import json
import redis
from config import REDIS_URL

# Connect to Upstash Redis
redis_client = redis.from_url(REDIS_URL, decode_responses=True)

def get_chat_history(chat_id: int) -> list:
    """Retrieves previous chat messages for a specific Telegram user."""
    history_key = f"chat_history:{chat_id}"
    raw_history = redis_client.get(history_key)
    
    # Type check for Pylance/JSON parsing safety
    if isinstance(raw_history, str):
        return json.loads(raw_history)
    return []

def save_chat_history(chat_id: int, updated_history: list):
    """Saves the updated conversation back to Redis for 24 hours."""
    history_key = f"chat_history:{chat_id}"
    
    formatted_history = []
    for m in updated_history:
        parts = []
        for p in m.parts:
            try:
                # Try to extract text. If it is a function call, the SDK throws a ValueError
                if p.text:
                    parts.append({"text": p.text})
            except ValueError:
                # Silently skip saving internal function calls to Redis
                pass 
                
        # Only save the message if it contains actual text parts
        if parts: 
            formatted_history.append({"role": m.role, "parts": parts})
    
    # Save with an expiration time of 86400 seconds (24 hours)
    redis_client.setex(history_key, 86400, json.dumps(formatted_history))