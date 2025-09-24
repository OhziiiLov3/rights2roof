# DuckDuckGo Search Tool  
### Documentation by Cecilia Kanne



***  
## Table of Contents  
- [DuckDuckGo Search Tool](#duckduckgo-search-tool)  
  - [Step 1 – Import Packages](#step-1--import-packages)  
  - [Step 2 – Initialize DuckDuckGo Search Client](#step-2--initialize-duckduckgo-search-client)  
  - [Step 3 – Define Broad DuckDuckGo Search Function](#step-3--define-broad-duckduckgo-search-function)  
  - [Step 4 – Wrap Function as StructuredTool](#step-4--wrap-function-as-structuredtool)  
  

***  



# DuckDuckGo Search Tool  



### Step 1 – Import Packages  
<details>  
<summary>📂 Code</summary>  



```python
from langchain_community.utilities import DuckDuckGoSearchAPIWrapper  # DuckDuckGo Instant Answer API wrapper
from app.models.schemas import ToolOutput                         # Custom structured output format
from langchain_core.tools import StructuredTool                   # Tool wrapper for LangChain workflow integration
```



</details>  



**Explanation:**  
Imports essential packages to handle DuckDuckGo queries, wrap output in a consistent schema, and package the function as a reusable tool for AI workflows.  



***  



### Step 2 – Initialize DuckDuckGo Search Client  
<details>  
<summary>📂 Code</summary>  



```python
# Initialize the DuckDuckGo search client using LangChain’s community wrapper.
# This client uses DuckDuckGo’s free Instant Answer API, requiring no API key.
duckduckgo = DuckDuckGoSearchAPIWrapper()
```



</details>  



**Explanation:**  
Sets up the search client to handle requests to DuckDuckGo’s Instant Answer API for fast, general search answers.  



***  



### Step 3 – Define Broad DuckDuckGo Search Function  
<details>  
<summary>📂 Code</summary>  



```python
def broad_duckduckgo_search(query: str) -> ToolOutput:
    """
    Perform a broad search query using DuckDuckGo Instant Answer API.

    Sends a user query and returns instant answers such as definitions, calculations,
    and concise informative snippets. Handles exceptions gracefully,
    returning error info if something goes wrong.

    Args:
        query (str): The user's search query.

    Returns:
        ToolOutput: Structured response containing:
          - tool: tool name 'broad_duckduckgo_search'
          - input: dict with query
          - output: returned answer text or error message
          - step: description of this execution step
    """
    try:
        # Query DuckDuckGo Instant Answer API
        result = duckduckgo.run(query)
    except Exception as e:
        # On error, return structured error info
        return ToolOutput(
            tool="broad_duckduckgo_search",
            input={"query": query},
            output=f"Error during DuckDuckGo search: {e}",
            step="Failed to perform DuckDuckGo search"
        )

    # Return structured search results on success
    return ToolOutput(
        tool="broad_duckduckgo_search",
        input={"query": query},
        output=result,
        step="Retrieve broad/general information using DuckDuckGo Instant Answer API"
    )
```



</details>  



**Explanation:**  
Queries DuckDuckGo for instant answers, handling exceptions gracefully. Outputs a consistent structured object for easy integration with other tools or agents.  



***  



### Step 4 – Wrap Function as StructuredTool  
<details>  
<summary>📂 Code</summary>  



```python
# Wrap the search function for use as a LangChain tool in agent workflows.
duckduckgo_search_tool = StructuredTool.from_function(
    func=broad_duckduckgo_search,
    name="broad_duckduckgo_search",
    description=(
        "Perform DuckDuckGo search using the free Instant Answer API "
        "for broad/general queries without requiring an API key."
    )
)
```



</details>  



**Explanation:**  
Enables the function to be invoked automatically within LangChain orchestration or AI agent workflows, improving modularity and reusability.  
