import time
from app.services.redis_helpers import check_rate_limit


if __name__ == "__main__":
    user_id = "test_user2"

    for i in range(12):
        allowed = check_rate_limit(user_id)
        print(f"Request {i+1}: {'✅ Allowed' if allowed else '❌ Blocked'}")
        time.sleep(0.5)  
