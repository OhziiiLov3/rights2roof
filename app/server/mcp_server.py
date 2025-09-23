#MCP Server goes here
from fastmcp import FastMCP            
from typing import Optional, Dict, Any  
import requests                         
import os    
from app.tools.wikipedia_tools import wikipedia_search
from app.tools.geo_tools import get_location_from_ip
from app.tools.tavily_tools import tavily_search
from app.tools.time_tools import time_tool_fn
from app.agents.planner_agent import planner_agent

rights2roof_server = FastMCP("rights2roof_tools")

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
    return{"result": tavily_search}



@rights2roof_server.tool(description="Run Planner agent to break query into steps")
def planner_agent_tool(query: str) -> Dict[str, Any]:
# simulate final answer
    plan_result = planner_agent(query)

        # Runs planner agent - just to demo for now - this will change 
    if hasattr(plan_result, "model_dump"):
        plan_steps = plan_result.model_dump().get("plan", [])
    else:
        plan_steps = plan_result.get("plan", [])
    return {"results":plan_steps}


def ping() -> str:
    return "pong"


if __name__ == "__main__":
    rights2roof_server.run(transport="http", host="0.0.0.0", port=5200)