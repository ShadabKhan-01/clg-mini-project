import json
import redis
from config import REDIS_URL

redis_client = redis.from_url(REDIS_URL, decode_responses=True)

def get_chat_history(chat_id: int) -> list:
    """Retrieves previous chat messages for a specific Telegram user."""
    history_key = f"chat_history:{chat_id}"
    raw_history = redis_client.get(history_key)
    
    if raw_history:
        return json.loads(raw_history)
    return []

def save_chat_history(chat_id: int, updated_history: list):
    """Saves the updated conversation back to Redis for 24 hours."""
    history_key = f"chat_history:{chat_id}"
    redis_client.setex(history_key, 86400, json.dumps(updated_history))