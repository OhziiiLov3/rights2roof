# slack webhook
from fastapi import FastAPI, Form, Request
import asyncio
import os
import json
from dotenv import load_dotenv
from slack_sdk import WebClient
from slack_sdk.web.async_client import AsyncWebClient
from app.services.slack_helpers import sanitize_query, post_slack_thread 
from app.services.redis_helpers import check_rate_limit , add_message, get_messages , get_last_thread, set_last_thread, get_user_location, set_user_location
from app.tools.chat_tool import chat_tool_fn
load_dotenv()

app = FastAPI(title="Rights-2-Roof Slash Command")

# intialize Slack Client 
SLACK_BOT_TOKEN=os.getenv("SLACK_BOT_TOKEN")
# client = WebClient(token=SLACK_BOT_TOKEN)
client = AsyncWebClient(token=SLACK_BOT_TOKEN)

# POST/slack/rights-2-roof -> Users query and responds to slack channel with answer
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

        location = get_user_location(user_id)
        if not location:
            return {
                "response_type": "ephemeral",
                "text": "🏠 To give you accurate tenant-rights info, what *state* are you in? (e.g., CA, NY, TX)"
                }

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
    


# Slack Event Subscription: Follow-ups in threads
@app.post("/slack/events")
async def slack_events(req: Request):
    payload = await req.json()

    # Slack URL verification
    if "challenge" in payload:
        return {"challenge": payload["challenge"]}

    event = payload.get("event", {})
    text = event.get("text")
    user_id = event.get("user")
    channel_id = event.get("channel")
    thread_ts = event.get("thread_ts") or event.get("ts")

    if not text or not user_id:
        return {"ok": True}


    # Ignore bot messages
    if event.get("bot_id"):
        return {"ok": True}
    
    user_location = get_user_location(user_id)

    if not user_location:
        cleaned = text.strip().upper()

     
        if len(cleaned) in (2, 3):
            set_user_location(user_id, cleaned)

            await client.chat_postMessage(
                channel=channel_id,
                thread_ts=thread_ts,
                text=f"👍 Got it! I'll use **{cleaned}** for all tenant-rights answers."
            )
            return {"ok": True}

        # Failed validation → ask again
        await client.chat_postMessage(
            channel=channel_id,
            thread_ts=thread_ts,
            text="⚠️ Please enter a valid 2-letter state code (ex: CA, NY, TX)."
        )
        return {"ok": True}


    if not check_rate_limit(user_id):
        await client.chat_postMessage(
            channel=channel_id,
            thread_ts=thread_ts,
            text="Rate limit exceeded. Try again later."
        )
        return {"ok": True}

    # Trigger follow-up chat tool
    asyncio.create_task(run_followup(user_id, channel_id, thread_ts, text))
    return {"ok": True}

async def run_followup(user_id: str, channel_id: str, thread_ts: str, text: str):
    """Helper to run chat tool for follow-ups in thread."""
    try:
        follow_up = await chat_tool_fn(user_id, text)
        await client.chat_postMessage(
            channel=channel_id,
            thread_ts=thread_ts,
            text=f"💬 Follow-up response:\n{follow_up.output}"
        )
    except Exception as e:
        await client.chat_postMessage(
            channel=channel_id,
            thread_ts=thread_ts,
            text=f"⚠️ Error fetching follow-up response: {str(e)}"
        )


# POST/rights-2-roof-history -> post request and responds with message history to slack
@app.post("/slack/rights-2-roof-history")
async def slack_history(user_id: str = Form(...), channel_id: str = Form(...), limit: int = 10):
    """Fetches recent conversation history with only User Query + R2R Answer."""

    history = get_messages(user_id, limit=limit)
    if not history:
        return {
            "response_type": "ephemeral",
            "text": "No recent history found"
        }

    formatted_messages = []
    for i, msg in enumerate(history, start=1):
        if msg.startswith("FULL_PIPELINE: "):
            try:
                payload = msg[len("FULL_PIPELINE: "):]
                pipeline_data = json.loads(payload)
                user_query = pipeline_data.get("query", "N/A")
                executor_resp = pipeline_data.get("executor_response", "N/A")

                formatted_messages.append(
                    f"{i}. *User:* {user_query}\n  *R2R Answer:* {executor_resp}"
                )
            except Exception:
                formatted_messages.append(f"{i}. {msg}")
        else:
            formatted_messages.append(f"{i}. {msg}")

    formatted = "\n\n".join(formatted_messages)

    dm_response = await client.conversations_open(users=user_id)
    dm_channel_id = dm_response["channel"]["id"]


    # Get the last thread_ts for this user
    thread_ts = get_last_thread(user_id)
    if thread_ts:
        await client.chat_postMessage(
            channel=dm_channel_id,
            thread_ts=thread_ts,
            text=f"📖 Your recent Rights2Roof history:\n{formatted}"
        )
    else:
        response = await client.chat_postMessage(
            channel=dm_channel_id,
            text=f"📖 Your recent Rights2Roof history:\n{formatted}"
        )
        set_last_thread(user_id, response["ts"])

    return {
        "response_type": "ephemeral",
        "text": "📖 History sent to Thread!"
    }



@app.get("/")
def root():
    return {"message": "Rights2Roof Slack webhook is running"}