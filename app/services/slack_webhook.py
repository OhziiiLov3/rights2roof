# slack webhook
from fastapi import FastAPI, Form
import asyncio
import os
from dotenv import load_dotenv
from slack_sdk import WebClient
from app.services.slack_helpers import sanitize_query, post_slack_thread 
from app.services.redis_helpers import check_rate_limit , add_message, get_messages
load_dotenv()




app = FastAPI(title="Rights-2-Roof Slash Command")

# intialize Slack Client 
SLACK_BOT_TOKEN=os.getenv("SLACK_BOT_TOKEN")
client = WebClient(token=SLACK_BOT_TOKEN)




# Slack Slash Command Endpoint
@app.post("/slack/rights-2-roof")
async def slack_roof(text: str = Form(...),user_id: str = Form(...),channel_id: str = Form(...),):
    """
    Handles /rights-2-roof <query> slash command from Slack.
    Responds immediately, then posts final answer asynchronously.
    """
    # rate limiting 
    if not check_rate_limit(user_id):
        return {
            "response_type": "ephemeral",
            "text": f"Rate limit exceeded. You can only make 10 requests per hour."
        }
    try:
        # Step 1: Sanitize
        safe_text = sanitize_query(text)

        add_message(user_id, f"USER_QUERY: {safe_text}")

        # step 2: Slack to respond immediately 
        ephemeral_response = {
            "response_type": "ephemeral",
            "text": f"Got it! Running Rights2Roof search for: {safe_text}"
        }

        # step 3: Trigger background task for final answer
        asyncio.create_task(post_slack_thread(client,channel_id,user_id, safe_text))
        return ephemeral_response
    
    except ValueError as error:
        return{
            "response_type": "ephemeral",
            "text": f"Sorry, your query isn't related to housing/tenant issues:{str(error)}"
        }

# /rights-2-roof-history
@app.post("/slack/rights-2-roof-history")
async def slack_history(user_id: str = Form(...), channel_id: str = Form(...), limit = 10):
    """Handles /rights-2-roof-history to fetch recent conversation history."""

    history =  get_messages(user_id, limit=limit)
    if not history:
        return {
            "response_type": "ephemeral",
            "text": "No recent history found"
        }
    
    formatted = "\n".join(history)

    await asyncio.to_thread(
        client.chat_postMessage,
        channel=channel_id,
        text=f"Your recent Rights2Roof history:\n ```{formatted}```"
    )

    return  {
            "response_type": "ephemeral",
            "text": "History sent to Channel!"
        }


@app.get("/")
def root():
    return {"message": "Rights2Roof Slack webhook is running"}