import os
from langchain_tavily import TavilySearch
from langchain_core.tools import StructuredTool
from app.models.schemas import ToolOutput
from dotenv import load_dotenv

load_dotenv()
TAVILY_API_KEY=os.getenv("TAVILY_API_KEY")

# client
tavily = TavilySearch(
    max_results = 3,
    topic="general",
    search_depth = "basic",
    api_key=TAVILY_API_KEY
)

def tavily_search(query:str) -> ToolOutput:
    """Search Tavily for recent/local housing info and return structured output."""
    result = tavily.invoke(query)

    return ToolOutput(
        tool="tavily_tool",
        input={"query": query},
        output=result,
        step="Search for recent/local housing info"
    )


tavily_tool = StructuredTool.from_function(
    func=tavily_search,
    name="tavily_tool",
    description="Use this to fetch recent/local housing info (tenant rights, rental assistance programs, deadlines, city/state policies)."
)


