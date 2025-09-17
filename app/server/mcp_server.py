#MCP Server goes here
from fastmcp import FastMCP            
from typing import Optional, Dict, Any  
import requests                         
import os    
from app.tools.wikipedia_tools import wikipedia_search
from app.tools.geo_tools import get_location_from_ip
from app.tools.tavily_tools import tavily_search
from app.tools.time_tools import time_tool_fn

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




def ping() -> str:
    return "pong"


if __name__ == "__main__":
    rights2roof_server.run()