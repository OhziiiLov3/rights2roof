import re 
import asyncio
import logging
import json
from fastmcp import Client
# from slack_sdk import WebClient
from slack_sdk.web.async_client import AsyncWebClient
from app.services.redis_helpers import add_message, set_last_thread, get_cached_result
from langsmith import traceable
from app.tools.chat_tool import chat_tool_fn
import os 
from dotenv import load_dotenv


load_dotenv()
# MCP_SERVER_URL = "http://127.0.0.1:5200/mcp" # local dev 
MCP_SERVER_URL="http://mcp:5300/mcp"
SLACK_BOT_TOKEN=os.getenv("SLACK_BOT_TOKEN")
client = AsyncWebClient(token=SLACK_BOT_TOKEN)



# Allowed patterns for user query santitation
ALLOWED_PATTERNS = [
    r"\brent(ing|al)?\b",            # rent, rental, renting
    r"\bhousing\b",                  # housing
    r"\beviction(s)?\b",             # eviction, evictions
    r"\btenant(s)?\b",               # tenant, tenants
    r"\blease(s)?\b",                # lease, leases
    r"\brepair(s)?\b",                # repair, repairs
    r"\blandlord(s)?\b",             # landlord, landlords
    r"\bassistance\b",               # assistance
    r"\binsurance\b",               # assistance
    r"\baffordable\b",               # affordable
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



# Helper Function: Post Threaded response
@traceable
async def post_slack_thread(client: AsyncWebClient,channel_id: str, user_id: str, query_text: str):
    """
    Runs the Planner agent and sends the final answer as a private DM to the user.
    """
    try:
        logging.info(f"[Right2Roof Bot] simulating pipeline for {user_id}:{query_text}")
        mcp_client = None
        for attempt in range(5):  # try 10 times
            try:
                mcp_client = await Client(MCP_SERVER_URL).__aenter__()
                await mcp_client.ping()
                break
            except Exception as e:
                wait_time = 2 ** attempt  
                logging.warning(f"[Right2Roof Bot] MCP connection failed (attempt {attempt+1}). Retrying in {wait_time}s...")
                await asyncio.sleep(wait_time)
        else:
            raise RuntimeError("Unable to connect to MCP server after multiple attempts")

        # call the pipeline tool
        result = await mcp_client.call_tool(
            "pipeline_tool",
            {
                "query": query_text,
                "user_id": user_id
            }
        )

        # exit MCP client context
        await mcp_client.__aexit__(None, None, None)

        logging.info(f"MCP result: {result}")

        # Extract executor response from MCP result
        try:
            raw_text = result.content[0].text  # MCP returns JSON string
            pipeline_response = json.loads(raw_text).get("result", "No result available")
        except Exception as e:
            logging.error(f"Failed to parse MCP result: {e}")
            pipeline_response = str(result)


        # fallback if pipeline is empty or weak 
        if not pipeline_response or len(pipeline_response) < 40:  
            logging.info("Pipeline weak. Falling back to vector store...")
            async with Client(MCP_SERVER_URL) as mcp_client:
                vector_result = await mcp_client.call_tool(
                    "vector_lookup", {"query": query_text}
                )
            raw_vector = vector_result.content[0].text
            fallback_context = json.loads(raw_vector).get("output", [])
            pipeline_response = "📚 From our tenant rights guide:\n" + "\n".join(fallback_context[:3])

        dm_response = await client.conversations_open(users=user_id)
        dm_channel_id = dm_response["channel"]["id"]


        placeholder = await client.chat_postMessage(
            channel=dm_channel_id,
            text=f"<@{user_id}> Fetching information about: {query_text}..."
        )

        # creates placeholder for message to respond in the thread 
        thread_ts = placeholder["ts"]
        set_last_thread(user_id, thread_ts)

        # Post final answer in the thread
        await client.chat_postMessage(
            channel=dm_channel_id,
            thread_ts=thread_ts,
            text=f"🏠 Rights2Roof:\n{pipeline_response}"
        )

        # Call chat_tool for follow-up Q&A
        # Prepare follow-up context in background but do NOT post it
        follow_up_query = f"Based on the answer:\n{pipeline_response}\nThe user asks a follow-up: {query_text}"
        asyncio.create_task(chat_tool_fn(user_id, follow_up_query))
       
        # post follow up - question
        await client.chat_postMessage(
        channel=dm_channel_id,
        user=user_id,
        thread_ts=thread_ts,
        text="💬 Want to dive deeper? Ask me a follow-up question here in this thread."
    )

        # save result in redis 
        cache_key = f"user:{user_id}:query:{query_text}"
        full_pipeline_result = get_cached_result(cache_key) or ""
        add_message(user_id, f"FULL_PIPELINE: {full_pipeline_result}")
 
        print(f"[Thread] Channel: {channel_id} | User: {user_id} | Answer: {pipeline_response}")
        
    except Exception as e:
        logging.exception(f"[Right2RoofBot] Error in planner agent")
        await client.chat_postMessage(
            channel=channel_id,
            user=user_id,
            text=f"<@{user_id}> Error fetching housing info: {str(e)}"
        )
    # logs errors
        add_message(user_id, f"BOT_ERROR: {str(e)}")

