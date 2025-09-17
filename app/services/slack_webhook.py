# slack webhook
from fastapi import FastAPI, Form
import asyncio
import os
import logging
from slack_sdk import WebClient
from app.agents.planner_agent import planner_agent
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Rights-2-Roof Slash Command")
logging.basicConfig(level=logging.INFO)

# intialize Slack Client 
SLACK_BOT_TOKEN=os.getenv("SLACK_BOT_TOKEN")
client = WebClient(token=SLACK_BOT_TOKEN)



# Helper Function: Post Threaded response
async def post_slack_thread(channel_id: str, user_id: str, query_text: str):
    """
    For now, just simulates MCP response for testing.
    """
    try:
        logging.info(f"[Right2Roof Bot] simulating pipeline for {user_id}:{query_text}")

    # ==== @Peter- the MCP Client that connects the server will go below here(remove the simulation ) ==== 

        # Call Planner Agent instead of simulating 
        plan_result = planner_agent(query_text)

         # Runs planner agent - just to demo for now - this will change 
        if hasattr(plan_result, "model_dump"):
            plan_steps = plan_result.model_dump().get("plan", [])
        else:
            plan_steps = plan_result.get("plan", [])

        final_answer = "\n".join(f"{i+1}. {step}" for i, step in enumerate(plan_steps))


        # Post a placeholder message first(this creates the thread)
        placeholder = await asyncio.to_thread(
            client.chat_postMessage,
            channel=channel_id,
            text=f"<@{user_id}> Fetching information about your plan..."
        )

        thread_ts = placeholder["ts"]

        # Post final answer in the thread
        await asyncio.to_thread(
            client.chat_postMessage,
            channel=channel_id,
            thread_ts=thread_ts,
            text=final_answer
        )

        logging.info(f"[Right2Roof Bot] Finished simulated response for {user_id}")
        print(f"[Thread] Channel: {channel_id} | User: {user_id} | Answer: {final_answer}")
        
    except Exception as e:
        logging.exception(f"[HousingBot] Error in simulated pipeline")


# Slack Slash Command Endpoint
@app.post("/slack/rights-2-roof")
async def slack_roof(text: str = Form(...),user_id: str = Form(...),channel_id: str = Form(...),):
    """
    Handles /rights-2-roof <query> slash command from Slack.
    Responds immediately, then posts final answer asynchronously.
    """

    # step 1: Slack to respond immediately 
    ephemeral_response = {
        "response_type": "ephemeral",
        "text": f"Got it! Running Rights2Roof search for: {text}"
    }

    # step 2: Trigger background task for final answer
    asyncio.create_task(post_slack_thread(channel_id,user_id, text))

    return ephemeral_response


@app.get("/")
def root():
    return {"message": "Rights2Roof Slack webhook is running"}