# Slack Helpers for Rights2Roof  
### Documentation by Keith Baskerville  

---
## Table of Contents  
- [Step 1 – Import Packages](#step-1--import-packages)  
- [Step 2 – Configuration](#step-2--configuration)  
- [Step 3 – Sanitize User Query](#step-3--sanitize-user-query)  
- [Step 4 – Rate Limiting](#step-4--rate-limiting)  
- [Step 5 – Post Slack Threaded Response](#step-5--post-slack-threaded-response)  

---

### Step 1 – Import Packages  
<details>
<summary>📂 Code</summary>

```python
import re
import asyncio
import logging
import time
from fastmcp import Client
from slack_sdk import WebClient
from app.agents.pipeline_query import pipeline_query
from langsmith import traceable
from dotenv import load_dotenv
import os

load_dotenv()
```

</details>

**Explanation:**  
Imports necessary libraries for regular expressions, asynchronous tasks, logging, Slack SDK, environment variables, and the Planner pipeline.  

---

### Step 2 – Configuration  
<details>
<summary>📂 Code</summary>

```python
MCP_SERVER_URL = "http://127.0.0.1:5200/mcp"

# In-memory rate limit store
user_request_log = {}

# Rate limit config
MAX_REQUESTS_PER_HOUR = 10
RATE_LIMIT_WINDOW = 3600  # seconds in 1 hour

# Allowed patterns for user queries
ALLOWED_PATTERNS = [
    r"\brent(ing|al)?\b",
    r"\bhousing\b",
    r"\beviction(s)?\b",
    r"\btenant(s)?\b",
    r"\blease(s)?\b",
    r"\blandlord(s)?\b",
    r"\bassistance\b",
    r"\bshelter(s)?\b",
    r"\bapartment(s)?\b",
    r"\bflat(s)?\b",
]
```

</details>

**Explanation:**  
Defines MCP server URL, rate limit configuration, in-memory tracking for user requests, and allowed query patterns for housing/tenant topics.  

---

### Step 3 – Sanitize User Query  
<details>
<summary>📂 Code</summary>

```python
def sanitize_query(query: str) -> str:
    """
    Cleans up and validates user input before sending it to agents.
    Removes Slack mentions, markdown characters, and checks topic relevance.
    """
    cleaned = re.sub(r"<@[\w\d]+>", "", query)
    cleaned = re.sub(r"[*_`]", "", cleaned).strip()

    if not any(re.search(pattern, cleaned.lower()) for pattern in ALLOWED_PATTERNS):
        raise ValueError("Query not related to housing/tenant issues.")
    
    return cleaned
```

</details>

**Explanation:**  
Removes Slack mentions, markdown formatting, and whitespace from user input. Validates that the query relates to housing/tenant issues using predefined regex patterns. Raises an error for invalid queries.  

---

### Step 4 – Rate Limiting  
<details>
<summary>📂 Code</summary>

```python
def check_rate_limit(user_id: str) -> bool:
    """
    Returns True if user is under rate limit, False if exceeded.
    Logs requests and ensures no more than 10 per hour.
    """
    now = time.time()
    if user_id not in user_request_log:
        user_request_log[user_id] = []

    user_request_log[user_id] = [
        timestamp for timestamp in user_request_log[user_id]
        if now - timestamp < RATE_LIMIT_WINDOW
    ]
    
    if len(user_request_log[user_id]) >= MAX_REQUESTS_PER_HOUR:
        return False

    user_request_log[user_id].append(now)
    return True
```

</details>

**Explanation:**  
Tracks each user’s request timestamps. Enforces a limit of 10 requests per hour, removing expired timestamps. Returns `False` if limit exceeded; otherwise, logs the new request and returns `True`.  

---

### Step 5 – Post Slack Threaded Response  
<details>
<summary>📂 Code</summary>

```python
@traceable
async def post_slack_thread(client: WebClient, channel_id: str, user_id: str, query_text: str):
    """
    Runs the Planner agent and sends the final answer in a Slack thread.
    Handles errors gracefully and posts error messages if needed.
    """
    try:
        logging.info(f"[Right2Roof Bot] simulating pipeline for {user_id}:{query_text}")

        # Call Planner Pipeline locally (temporary)
        result = pipeline_query(query_text)
        logging.info(f"Pipeline result: {result.get('plan')}")

        plan_steps = result.get("plan", [])
        final_answer = "\n".join(f"{i+1}. {step}" for i, step in enumerate(plan_steps))

        # Post placeholder message to create thread
        placeholder = await asyncio.to_thread(
            client.chat_postMessage,
            channel=channel_id,
            text=f"<@{user_id}> Fetching information about your plan..."
        )
        thread_ts = placeholder["ts"]

        # Post final answer in thread
        await asyncio.to_thread(
            client.chat_postMessage,
            channel=channel_id,
            thread_ts=thread_ts,
            text=final_answer
        )

        print(f"[Thread] Channel: {channel_id} | User: {user_id} | Answer: {final_answer}")
        
    except Exception as e:
        logging.exception(f"[Right2RoofBot] Error in planner agent")
        await asyncio.to_thread(
            client.chat_postMessage,
            channel=channel_id,
            text=f"<@{user_id}> Error fetching housing info: {str(e)}"
        )
```

</details>

**Explanation:**  
- Runs the Planner agent to generate an execution plan.  
- Posts a placeholder message to initiate a Slack thread.  
- Posts the final answer in the thread.  
- Handles exceptions by logging and sending an error message to the user.  
- Decorated with `@traceable` for LangSmith tracing.  

---

This documentation covers **all core helpers** used in your Slack webhook: sanitizing queries, rate limiting, and posting threaded responses.  

