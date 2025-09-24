from langchain_community.utilities import DuckDuckGoSearchAPIWrapper
from app.models.schemas import ToolOutput
from langchain_core.tools import StructuredTool

# Initialize the DuckDuckGo search client using the LangChain community wrapper.
# This client communicates with DuckDuckGo's Instant Answer API, which is free and requires no API key.
duckduckgo = DuckDuckGoSearchAPIWrapper()

def broad_duckduckgo_search(query: str) -> ToolOutput:
    """
    Perform a broad search on DuckDuckGo for general queries.

    This function sends the query to DuckDuckGo's Instant Answer API and retrieves
    quick facts such as definitions, calculations, and concise informational snippets.
    It handles errors gracefully, returning an informative message on failure.

    Args:
        query (str): The search query string.

    Returns:
        ToolOutput: A structured output containing:
          - tool: Identifier name of the tool used
          - input: Dictionary with original query
          - output: The resulting text from DuckDuckGo or an error message
          - step: Description of this processing step
    """
    try:
        # Run the DuckDuckGo Instant Answer API query via the wrapper
        result = duckduckgo.run(query)
    except Exception as e:
        # If an error occurs, encapsulate details in ToolOutput for debugging or user notification
        return ToolOutput(
            tool="broad_duckduckgo_search",
            input={"query": query},
            output=f"Error during DuckDuckGo search: {e}",
            step="Failed to perform DuckDuckGo search"
        )
    
    # If successful, return the retrieved information wrapped in ToolOutput for consistent interface
    return ToolOutput(
        tool="broad_duckduckgo_search",
        input={"query": query},
        output=result,
        step="Retrieve broad/general information using DuckDuckGo Instant Answer API"
    )

# Create a StructuredTool instance from the search function allowing seamless integration
# into LangChain workflows or other orchestration frameworks.
duckduckgo_search_tool = StructuredTool.from_function(
    func=broad_duckduckgo_search,
    name="broad_duckduckgo_search",
    description=(
        "Perform a DuckDuckGo search using the free Instant Answer API "
        "for broad/general queries without requiring an API key."
    )
)

#Test Block
if __name__ == "__main__":
    test_query = "tenant rights laws 2025"
    output = broad_duckduckgo_search(test_query)
    print("Search Tool Output:")
    print(output.output)
