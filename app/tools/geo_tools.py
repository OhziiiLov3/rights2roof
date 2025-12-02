import requests
import os
from langchain_core.tools import StructuredTool
from app.models.schemas import ToolOutput
from typing import Optional


def get_location_from_ip(ip: Optional[str] = None) -> ToolOutput:
    """
    Graceful geo lookup:
    - Slack never sends real IPs — prevents failures on 0.0.0.0 / internal IPs.
    - If IP lookup fails, returns a soft failure instead of raising.
    """

    # If no IP or a known internal IP → return soft failure
    if not ip or ip in ["0.0.0.0", "127.0.0.1"] or ip.startswith("100."):
        return ToolOutput(
            tool="geo_location",
            input={"ip": ip},
            output={"error": "NO_IP_AVAILABLE"},
            step="Get User Location"
        )

    try:
        url = f"http://ip-api.com/json/{ip}"
        response = requests.get(url, timeout=3)
        data = response.json()

        if data.get("status") != "success":
            return ToolOutput(
                tool="geo_location",
                input={"ip": ip},
                output={"error": "LOOKUP_FAILED"},
                step="Get User Location"
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

    except Exception:
        return ToolOutput(
            tool="geo_location",
            input={"ip": ip},
            output={"error": "LOOKUP_EXCEPTION"},
            step="Get User Location"
        )

# --- Wrap the Tools (StructuredTool) --
geo_tool = StructuredTool.from_function(
    func=get_location_from_ip,
    name="geo_location",
    description="Get User's Location",
)