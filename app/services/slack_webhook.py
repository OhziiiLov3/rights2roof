# slack webhook
from fastapi import FastAPI, Form
import asyncio
import os
import logging

app = FastAPI(title="Rights-2-Roof Slash Command")

logging.basicConfig(level=logging.INFO)

# Helper Function: Post Threaded response
async def post_slack_thread(channel_id: str, user_id: str, query_text: str):
    """
    For now, just simulates MCP response for testing.
    """
    try:
        logging.info(f"[Right2Roof Bot] simulating pipeline for {user_id}:{query_text}")

    # ==== @Peter- the MCP Client that connects the server will go below here(remove the simulation ) ==== 

        # simulate final answer
        final_answer = f"Simulated housing info for query: '{query_text}' "
        # simulate async posting delay
        await asyncio.sleep(1)

        logging.info(f"[Right2Roof Bot] Finished simulated response for {user_id}")
        print(f"[Thread] Channel: {channel_id} | User: {user_id} | Answer: {final_answer}")
        
    except Exception as e:
        logging.exception(f"[HousingBot] Error in simulated pipeline")


# Slack Slash Command  Endpoint
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