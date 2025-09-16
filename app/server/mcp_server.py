#MCP Server goes here
from fastmcp import FastMCP
from langchain_community.tools import WikipediaQueryRun
from langchain_community.utilities import WikipediaAPIWrapper
from typing import Optional
import requests
from typing import Dict, Any
# from app.models.schemas import ToolOutput
import os

rights2roof_server = FastMCP("rights2roof_tools")
wikipedia = WikipediaQueryRun(api_wrapper=WikipediaAPIWrapper())

@rights2roof_server.tool()
def get_location_from_ip(ip:Optional[str] = None) -> Dict[str, Any]:
    """
    Uses ip-api.com to get location info from IP.
    If no IP provided, falls back to server IP.
    """

    if not ip:
        ip = os.getenv("IP_ADDRESS")
    url = f"http://ip-api.com/json/{ip}"
    response = requests.get(url)
    data = response.json()

    if data.get("status") != "success":
        raise ValueError(f"Could not get location for IP {ip}")
    return{
        "tool": "geo_location",
        "input": {"ip": ip},
        "output" : {"city": data.get("city"), "state": data.get("region"), "country": data.get("country")},
        "step":"Get User Location"
    }




@rights2roof_server.tool()
def wikipedia_search(query: str) -> Dict[str, Any]:
    """Search Wikipedia for a given topic and return the result text."""
    result = wikipedia.run(query)
    return {
        "tool":"wikipedia_search",
        "input":{"query": query},
        "output":result,
        "step":"Look up update to Rental Laws and Affordable Housing information"

    }





def ping() -> str:
    return "pong"


if __name__ == "__main__":
    rights2roof_server.run()