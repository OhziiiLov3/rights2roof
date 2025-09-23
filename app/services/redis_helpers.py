import time
import redis
import os
from dotenv import load_dotenv
load_dotenv()
from typing import List , Any, Optional


# connect to Redis
r = redis.Redis(
    host=os.getenv("REDIS_HOST","localhost"),
    port=int(os.getenv("REDIS_PORT", 6379)),
    db=0,
    decode_responses=True
)

# Rate limit config
MAX_REQUESTS_PER_HOUR = 10
RATE_LIMIT_WINDOW = 3600  # seconds in 1 hour

# === Rate Limits ===
# Helper Function to check user rate limits(10 requests per hour)
def check_rate_limit(user_id:str)->bool:
    """
    Returns True if user is under rate limit, False if exceeded.
    Uses Redis sorted sets to track request timestamps.
    """
    now = time.time()
    key = f"user:{user_id}:requests"
    # remove expired requests from the sorted set
    r.zremrangebyscore(key, 0, now - RATE_LIMIT_WINDOW)

    # Count how many requests remain in the last hour:
    current_count = r.zcard(key)
    if current_count >= MAX_REQUESTS_PER_HOUR:
        return False
    
    # Add the new request timestamp
    r.zadd(key, {str(now): now})
    #  ensures key expires eventually(if user goes inactive)
    r.expire(key, RATE_LIMIT_WINDOW)
    return True

# === Chat History APIs (add & get messages)===
def add_message(user_id:str, message: str, expire_days: int = 1) -> None:
    """Add a message to Redis sorted set with timestamps"""
    now = time.time()
    key = f"user:{user_id}:messages"
    r.zadd(key,{message:now})
    r.expire(key, expire_days * 24 * 3600)

def get_messages(user_id: str, limit: int = 20) -> List[str]:
    """Get last N messages for a user"""
    key = f"user:{user_id}:messages"
    return r.zrevrange(key, 0, limit - 1)

# Add a helpers to save and fetch the last thread_ts per user:
def set_last_thread(user_id:str, thread_ts: str, expire_days: int = 1)-> None:
    """Stores the last slack thread_timestamp for a user"""
    key = f"user:{user_id}:last_thread"
    r.setex(key, expire_days * 24 * 3600, thread_ts)

def get_last_thread(user_id:str)-> str | None:
    """Retrieve the last slack thread_ts for a user"""
    key = f"user:{user_id}:last_thread"
    return r.get(key)

# Caching APIs
def cache_result(key: str, value: Any, expire_seconds: int = 3600) -> None:
    """Cache any result in redis"""
    r.set(key, value, ex=expire_seconds)

def get_cached_result(key:str) -> Optional[str]:
    """Return cached value if exists, else None"""
    return r.get(key)

