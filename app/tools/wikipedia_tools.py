from langchain_community.tools import WikipediaQueryRun
from langchain_community.utilities import WikipediaAPIWrapper
from langchain_core.tools import StructuredTool
from app.models.schemas import ToolOutput

# Wikipedia client
wikipedia = WikipediaQueryRun(api_wrapper=WikipediaAPIWrapper())

def wikipedia_search(query: str):
    """Search Wikipedia for a given topic and return the result text."""
    result = wikipedia.run(query)
    return ToolOutput(
        tool="wikipedia_search",
        input={"query": query},
        output=result,
        step="Look up update to Rental Laws and Affordable Housing information"

    )

wikipedia_tool = StructuredTool.from_function(
    func=wikipedia_search,
    name="wikipedia_search",
    description="Search Wikipedia for information on a topic."
)

