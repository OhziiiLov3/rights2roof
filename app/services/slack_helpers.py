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



MCP_SERVER_URL = "http://127.0.0.1:5200/mcp"

# In-memory rate limit store
user_request_log = {}

# Rate limit config
MAX_REQUESTS_PER_HOUR = 10
RATE_LIMIT_WINDOW = 3600  # seconds in 1 hour



# Allowed Topics for user query santitation
# first pass to test topics
# ALLOWED_TOPICS = ["rent", "housing","moving","eviction","tenant","lease","landlord","assistance", "housing repairs"]

ALLOWED_PATTERNS = [
    r"\brent(ing|al)?\b",            # rent, rental, renting
    r"\bhousing\b",                  # housing
    r"\beviction(s)?\b",             # eviction, evictions
    r"\btenant(s)?\b",               # tenant, tenants
    r"\blease(s)?\b",                # lease, leases
    r"\blandlord(s)?\b",             # landlord, landlords
    r"\bassistance\b",               # assistance
    r"\bshelter(s)?\b",              # shelter, shelters
    r"\bapartment(s)?\b",            # apartment, apartments
    r"\bflat(s)?\b",                 # flat, flats (UK term)
]

# Helper Function: Clean up and validate user input before sending it to agents.
def sanitize_query(query:str)-> str:
    """
    Clean up and validate user input before sending it to agents.
    """
    # strip slack mentions like <@U12345>
    cleaned = re.sub(r"<@[\w\d]+>", "", query)
    # Remove Slack markdown chars(*,_,``) and removes whitespace
    cleaned = re.sub(r"[*_`]","",cleaned).strip()

    # check for topic relavance
    if not any(re.search(pattern, cleaned.lower()) for pattern in ALLOWED_PATTERNS):
        raise ValueError("Query not related to housing/tenant issues.")
    
    return cleaned

# Helper Function to check user rate limits(10 requests per hour)
def check_rate_limit(user_id:str)->bool:
    """
    Returns True if user is under rate limit, False if exceeded.
    """
    now = time.time()
    if user_id not in user_request_log:
        user_request_log[user_id] = []

    # remove expired timestamps
    user_request_log[user_id] =[
        timestamp for timestamp in user_request_log[user_id] if now - timestamp < RATE_LIMIT_WINDOW
    ]
    
    if len(user_request_log[user_id]) >= MAX_REQUESTS_PER_HOUR:
        return False
    # log current request
    user_request_log[user_id].append(now)
    print("Request",user_request_log)
    return True


# Helper Function: Post Threaded response
@traceable
async def post_slack_thread(client: WebClient,channel_id: str, user_id: str, query_text: str):
    """
    Runs the Planner agent and sends the final answer as a private DM to the user.
    """
    try:
        logging.info(f"[Right2Roof Bot] simulating pipeline for {user_id}:{query_text}")
        # async with Client(MCP_SERVER_URL) as mcp_client:
        #     await mcp_client.ping()
        #     # call the pipline_query_tool(when ready)
        #     result = await mcp_client.call_tool(
        #         "pipeline_query_tool",
        #         {"query": query_text}
        #     )


        # TEMPORARY :runs pipeline query locally for now 
        result = pipeline_query(query_text)
        logging.info(f"Pipeline result: {result.get('plan')}")

        # plan is key coming from pydantic model 
        plan_steps = result.get("plan", [])
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

      
        print(f"[Thread] Channel: {channel_id} | User: {user_id} | Answer: {final_answer}")
        
    except Exception as e:
        logging.exception(f"[Right2RoofBot] Error in planner agent")
        await asyncio.to_thread(
            client.chat_postMessage,
            channel=channel_id,
            text=f"<@{user_id}> Error fetching housing info: {str(e)}"
        )