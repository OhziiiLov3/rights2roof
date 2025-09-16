import requests
import os
from langchain_core.tools import StructuredTool
from app.models.schemas import ToolOutput
from typing import Optional


def get_location_from_ip(ip:Optional[str] = None) -> ToolOutput:
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
    return ToolOutput(
        tool="geo_location",
        input={"ip": ip},
        output={"city": data.get("city"), "state": data.get("region"), "country": data.get("country")},
        step="Get User Location"
    )

# --- Wrap the Tools (StructuredTool) --
# It lets your agent or executor actually call the tool with inputs.
# Without this, LangChain doesn’t know how to execute get_location_from_ip

geo_tool = StructuredTool.from_function(
    func=get_location_from_ip,
    name="geo_location",
    description="Get city, state, and country from an IP address.",
)