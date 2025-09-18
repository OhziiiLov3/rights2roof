from fastapi import FastAPI, Form, Request
from fastmcp import Client
import asyncio
from langsmith import traceable
import os
import logging
from slack_sdk import WebClient
from fastapi.responses import JSONResponse
from app.agents.planner_agent import planner_agent
from dotenv import load_dotenv
import json

# Import the GoogleNews tool
from app.tools.Gnews_tools import real_estate_news_tool

# Load environment variables from .env file
load_dotenv()

app = FastAPI(title="Rights-2-Roof Slash Command")

# Read Slack bot token from environment
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")

# Setup basic logging
logging.basicConfig(level=logging.INFO)

# Initialize Slack Client
client = WebClient(token=SLACK_BOT_TOKEN)

MCP_SERVER_URL = "http://127.0.0.1:5200/mcp"

# Slack Events Endpoint (for URL verification and events)


@app.post("/slack/events")
async def slack_events(request: Request):
    body = await request.json()
    if body.get("type") == "url_verification":
        # Respond with the challenge token to confirm URL
        return JSONResponse({"challenge": body["challenge"]})
    # Optionally handle other event types here
    return JSONResponse({"ok": True})

# Helper Function: Post Threaded response


@traceable
async def post_slack_thread(channel_id: str, user_id: str, query_text: str):
    """
    Runs the real estate news tool and sends the formatted news as a threaded response.
    """
    try:
        logging.info(
            f"[Rights2Roof Bot] fetching real estate news for {user_id}: {query_text}")

        # Call the real estate news tool synchronously (wrap in thread to not block async)
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: real_estate_news_tool.invoke(
                {"query": query_text} if query_text else {})
        )

        # result.output is a JSON string; parse it safely
        try:
            news_data = json.loads(result.output)
            formatted_news = news_data.get(
                "formatted", "No news articles found.")
        except Exception:
            formatted_news = result.output  # fallback to raw output

        # Post a placeholder message first to create a thread
        placeholder = await asyncio.to_thread(
            client.chat_postMessage,
            channel=channel_id,
            text=f"<@{user_id}> Fetching real estate news for your query..."
        )
        thread_ts = placeholder["ts"]

        # Post news results in the thread
        await asyncio.to_thread(
            client.chat_postMessage,
            channel=channel_id,
            thread_ts=thread_ts,
            text=formatted_news
        )

        logging.info(f"[Rights2Roof Bot] finished posting news for {user_id}")

    except Exception as e:
        logging.exception("[Rights2Roof Bot] Error fetching real estate news")

# Slack Slash Command Endpoint


@app.post("/slack/rights-2-roof")
async def slack_roof(
    text: str = Form(...),
    user_id: str = Form(...),
    channel_id: str = Form(...),
):
    """
    Handles /rights-2-roof <query> slash command from Slack.
    Responds immediately, then posts final answer asynchronously.
    """

    # Step 1: Slack respond immediately
    ephemeral_response = {
        "response_type": "ephemeral",
        "text": f"Got it! Running Rights2Roof search for: {text}"
    }

    # Step 2: Trigger background task for final answer
    asyncio.create_task(post_slack_thread(channel_id, user_id, text))

    return ephemeral_response


@app.get("/")
def root():
    return {"message": "Rights2Roof Slack webhook is running"}
