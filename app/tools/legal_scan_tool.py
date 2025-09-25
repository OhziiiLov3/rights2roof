import os
import requests
from app.models.schemas import ToolOutput
from dotenv import load_dotenv
from langchain_core.tools import StructuredTool


load_dotenv()
LEGISCAN_API_KEY = os.getenv("LEGISCAN_API_KEY")

def legiscan_search(query: str, state: str = "CA") -> ToolOutput:
    """
    Search legislation using LegiScan API.
    E.g. keyword search, filter by state (like California).
    """
    url = "https://api.legiscan.com/?key={}&op=search".format(LEGISCAN_API_KEY)
    params = {
        "state": state,
        "q": query
    }
    resp = requests.get(url, params=params)
    data = resp.json() if resp.status_code == 200 else {"error": resp.text}

    return ToolOutput(
        tool="legiscan_tool",
        input={"query": query, "state": state},
        output=data,
        step="Search legislative bills matching query"
    )

legiscan_tool = StructuredTool.from_function(
    func=legiscan_search,
    name="legiscan_tool",
    description="Use this tool to fetch legislative bills (state or federal) matching a query, e.g. tenant rights, rent control, eviction laws."
)