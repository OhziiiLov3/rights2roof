import time
import redis
import os
from dotenv import load_dotenv
load_dotenv()


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