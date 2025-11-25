#MCP Server goes here
from fastmcp import FastMCP            
from typing import Optional, Dict, Any  
import asyncio
from app.tools.wikipedia_tools import wikipedia_search
from app.tools.geo_tools import get_location_from_ip
from app.tools.tavily_tools import tavily_search
from app.tools.time_tools import time_tool_fn
from app.pipelines.pipeline_query import pipeline_query
from app.tools.bing_rss_tool import fetch_rss_news
from app.tools.legal_scan_tool import legiscan_search
from app.tools.chat_tool import chat_tool_fn
from app.tools.vector_store_tool import get_context
from langsmith import traceable
from app.services.serializers import serialize_tool_output


rights2roof_server = FastMCP("rights2roof_tools")


# == Tools for agents to use ==
@rights2roof_server.tool(description="geolocation tool to find the users location")
def fetch_location_from_ip(ip:Optional[str] = None) -> Dict[str, Any]:
    return{"result": get_location_from_ip(ip) }

@rights2roof_server.tool(description="Search Wikipedia for information")
def wikipedia_lookup(query: str) -> Dict[str, Any]:
    return {"result": wikipedia_search(query)}

@rights2roof_server.tool(description="Return the current date and time in ISO format.")
def time()-> Dict[str, Any]:
    return{"result": time_tool_fn()}

@rights2roof_server.tool(description="Search Tavily for recent/local housing info and return structured output.")
def tavily(query: str)-> Dict[str, Any]:
    return{"result": tavily_search(query)}

@rights2roof_server.tool(description="Fetch recent tenant rights & affordable housing updates (California and New York focus).")
def bing_rss(query: str) -> Dict[str, Any]:
    return {"result": fetch_rss_news(query)}

@rights2roof_server.tool(description="Search U.S. state legislation and bills (housing, tenant rights, eviction laws).")
def legiscan(query: str, state: str = "CA") -> Dict[str, Any]:
    return {"result": legiscan_search(query, state)}

@rights2roof_server.tool(description="Retreive legal housing context from PDFs stored in Redis")
def vector_lookup(query: str) -> Dict[str, Any]:
    result = get_context(query)  
    return {
        "tool": result.tool,
        "input": result.input,
        "output": [doc.page_content for doc in result.output],  # simplify to text
        "step": result.step
    }

@rights2roof_server.tool(description="Follow-up Q&A using conversation history")
async def chat_tool(query: str, user_id: str) -> Dict[str, Any]:
    # Run chat_tool_fn in a thread to avoid blocking
    result = await asyncio.to_thread(chat_tool_fn, user_id, query)
    return {"result": result.output}



# == Agent pipeline as tools ==
@rights2roof_server.tool(description="Run full Rights2Roof pipeline and return final answer")
def pipeline_tool(query: str, user_id: str, location: Optional[str] = None) -> dict:
    """
    Run full pipeline and return JSON-safe response for Slack and logging.
    """
    if location:
        query_with_location = f"{query} (State: {location})"
    else:
        query_with_location = query

    final_answer = pipeline_query(query_with_location, user_id)
    return {"result": final_answer}


def ping() -> str:
    return "pong"


if __name__ == "__main__":
    rights2roof_server.run(transport="http", host="0.0.0.0", port=5300, path="/mcp")