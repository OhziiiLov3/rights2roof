import requests
import os
from langchain_core.tools import StructuredTool
from app.models.schemas import ToolOutput
from typing import Optional


def get_location_from_ip(ip: Optional[str] = None) -> ToolOutput:
    """
    Uses ip-api.com to get location info from IP.
    Never throws for 0.0.0.0 or invalid IPs.
    """

    if not ip:
        ip = os.getenv("IP_ADDRESS")

    url = f"http://ip-api.com/json/{ip}"
    
    try:
        response = requests.get(url, timeout=3)
        data = response.json()
    except Exception:
        data = {"status": "fail"}

    if data.get("status") != "success":
        # fallback to empty location (Slack bot will ask for state later)
        return ToolOutput(
            tool="geo_location",
            input={"ip": ip},
            output={"city": None, "state": None, "country": None},
            step="Get User Location (fallback)"
        )
    
    return ToolOutput(
        tool="geo_location",
        input={"ip": ip},
        output={
            "city": data.get("city"),
            "state": data.get("region"),
            "country": data.get("country"),
        },
        step="Get User Location"
    )
