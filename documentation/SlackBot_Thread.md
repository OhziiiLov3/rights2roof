# Slack Webhook for Rights2Roof  
### Documentation by Keith Baskerville  

---
## Table of Contents  
- [Step 1 – Import Packages](#step-1--import-packages)  
- [Step 2 – Initialize Slack Client](#step-2--initialize-slack-client)  
- [Step 3 – Helper Function: Post Threaded Response](#step-3--helper-function-post-threaded-response)  
  - [Optional: Post Thread in Original Channel](#optional-post-thread-in-original-channel)  
- [Step 4 – Slash Command Endpoint](#step-4--slash-command-endpoint)  
- [Step 5 – Root Endpoint](#step-5--root-endpoint)  

---

### Step 1 – Import Packages  
<details>
<summary>📂 Code</summary>

```python
from fastapi import FastAPI, Form
import asyncio
import os
import logging
from slack_sdk import WebClient
from app.agents.planner_agent import planner_agent
from dotenv import load_dotenv

load_dotenv()
```

</details>

**Explanation:**  
Imports packages for FastAPI, Slack SDK, asynchronous tasks, environment variables, and logging.  

---

### Step 2 – Initialize Slack Client  
<details>
<summary>📂 Code</summary>

```python
app = FastAPI(title="Rights-2-Roof Slash Command")
logging.basicConfig(level=logging.INFO)

SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
client = WebClient(token=SLACK_BOT_TOKEN)
```

</details>

**Explanation:**  
Sets up FastAPI app, configures logging, and initializes the Slack WebClient using the bot token.  

---

### Step 3 – Helper Function: Post Threaded Response  
<details>
<summary>📂 Code</summary>

```python
async def post_slack_thread(channel_id: str, user_id: str, query_text: str):
    """
    Runs the Planner agent and sends the final answer as a private DM to the user.
    """
    try:
        logging.info(f"[Right2Roof Bot] simulating pipeline for {user_id}:{query_text}")

        # Call Planner Agent
        plan_result = planner_agent(query_text)

        if hasattr(plan_result, "model_dump"):
            plan_steps = plan_result.model_dump().get("plan", [])
        else:
            plan_steps = plan_result.get("plan", [])

        final_answer = "\n".join(f"{i+1}. {step}" for i, step in enumerate(plan_steps))

        # Post final answer as DM to user
        await asyncio.to_thread(
            client.chat_postMessage,
            channel=user_id,
            text=final_answer
        )

        logging.info(f"[Right2Roof Bot] Finished simulated response for {user_id}")
        print(f"[Thread] Channel: {channel_id} | User: {user_id} | Answer: {final_answer}")
        
    except Exception as e:
        logging.exception(f"[HousingBot] Error in simulated pipeline")
```

</details>

**Explanation:**  
This function runs the Planner agent for the user query and posts the results to the user as a direct message.  
It handles errors gracefully using logging and prints final output for debugging.  

---

#### Optional: Post Thread in Original Channel  

<details>
<summary>📂 Code</summary>

```python
# Placeholder message to create a thread in the original channel
# placeholder = await asyncio.to_thread(
#     client.chat_postMessage,
#     channel=channel_id,
#     text=f"<@{user_id}> Fetching information about your plan..."
# )
# thread_ts = placeholder["ts"]
# Post final answer in the thread instead of DM
# await asyncio.to_thread(
#     client.chat_postMessage,
#     channel=channel_id,
#     thread_ts=thread_ts,
#     text=final_answer
# )
```

</details>

**Explanation:**  
Optionally, the final answer can be posted as a threaded message in the original channel instead of a DM. This preserves conversation context.  

---

### Step 4 – Slash Command Endpoint  
<details>
<summary>📂 Code</summary>

```python
@app.post("/slack/rights-2-roof")
async def slack_roof(text: str = Form(...), user_id: str = Form(...), channel_id: str = Form(...)):
    """
    Handles /rights-2-roof <query> slash command from Slack.
    Responds immediately, then posts final answer asynchronously.
    """
    ephemeral_response = {
        "response_type": "ephemeral",
        "text": f"Got it! Running Rights2Roof search for: {text}"
    }

    # Trigger background task for final answer
    asyncio.create_task(post_slack_thread(channel_id, user_id, text))

    return ephemeral_response
```

</details>

**Explanation:**  
Handles the `/rights-2-roof` Slack command.  
Returns an immediate ephemeral confirmation and triggers the background task to post the final answer.  

---

### Step 5 – Root Endpoint  
<details>
<summary>📂 Code</summary>

```python
@app.get("/")
def root():
    return {"message": "Rights2Roof Slack webhook is running"}
```

</details>

**Explanation:**  
A simple root endpoint to verify the Slack webhook server is running.  
