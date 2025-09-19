# slack webhook
from fastapi import FastAPI, Form
from fastmcp import Client
import asyncio
from langsmith import traceable
import os
import logging
from slack_sdk import WebClient
from app.agents.planner_agent import planner_agent
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Rights-2-Roof Slash Command")


# intialize Slack Client 
SLACK_BOT_TOKEN=os.getenv("SLACK_BOT_TOKEN")
client = WebClient(token=SLACK_BOT_TOKEN)


MCP_SERVER_URL = "http://127.0.0.1:5200/mcp"


# Helper Function: Post Threaded response
@traceable
async def post_slack_thread(channel_id: str, user_id: str, query_text: str):
    """
    Runs the Planner agent and sends the final answer as a private DM to the user.
    """
    try:
        logging.info(f"[Right2Roof Bot] simulating pipeline for {user_id}:{query_text}")

        async with Client(MCP_SERVER_URL) as mcp_client:
            await mcp_client.ping()

            # call the planner tool(we will swap with agent pipline later)
            result = await mcp_client.call_tool(
                "planner_agent_tool",
                {"query": query_text}
            )
        
            # handles Pydantic output
            plan_steps = []
            for item in result.content:
                if hasattr(item, "data") and isinstance(item.data, list):
                    plan_steps.extend(item.data)
                elif hasattr(item, "text") and item.text:
                    plan_steps.append(item.text)
            
            # # Check if the tool call returned an error
            # if result.is_error:
            #     plan_steps = ["Error fetching plan"]
            # else:
            #     # result.content is a list of items returned by the tool
            #     for item in result.content:
            #         # MCP wraps the tool's return value in `data`
            #         if hasattr(item, "data") and isinstance(item.data, dict) and "result" in item.data:
            #             # item.data["result"] is a list of strings
            #             plan_steps.extend(item.data["result"])
            #         # fallback: some tools may return a text attribute
            #         elif hasattr(item, "text") and item.text:
            #             plan_steps.append(item.text)

            

            final_answer = "\n".join(f"{i+1}. {step}" for i, step in enumerate(plan_steps))




        # Post a placeholder message first(this creates the thread)
        placeholder = await asyncio.to_thread(
            client.chat_postMessage,
            channel=channel_id,
            text=f"<@{user_id}> Fetching information about your plan..."
        )

        # creates placeholder for message to respond in the thread 
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
        logging.exception(f"[Right2RoofBot] Error in planner agent")
        await asyncio.to_thread(
            client.chat_postMessage,
            channel=channel_id,
            text=f"<@{user_id}> Error fetching housing info: {str(e)}"
        )


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