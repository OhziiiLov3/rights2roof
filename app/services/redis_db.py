import os
import redis
from app.models.schemas import UserData

r = redis.Redis(host=os.getenv("REDIS_HOST"), port=os.getenv("REDIS_PORT"), decode_responses=True)

def get_user_session(user_id) -> UserData:
    try:
        user_data = r.get(user_id)
        return user_data
    except redis.RedisError as e:
        return None

def create_user_session(user_id, user_data: UserData) -> UserData:
    try:
        r.set(user_id, user_data)
    except redis.RedisError as e:
        print(f"Error creating session for user {user_id}: {e}")
        return None

def update_user_session(user_id, user_data: UserData) -> UserData:
    try:
        r.set(user_id, user_data)
    except redis.RedisError as e:
        print(f"Error updating session for user {user_id}: {e}")
        return None


