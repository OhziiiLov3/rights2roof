# Planner Tools – Tavily & Time  
### Documentation by Keith Baskerville  

---
## Table of Contents  
- [Tavily Tool](#tavily-tool)  
  - [Step 1 – Import Packages](#step-1--import-packages)  
  - [Step 2 – Create Tavily Client](#step-2--create-tavily-client)  
  - [Step 3 – Define Tavily Search Function](#step-3--define-tavily-search-function)  
  - [Step 4 – Wrap Function as StructuredTool](#step-4--wrap-function-as-structuredtool)  
  - [Step 5 – Example Usage](#step-5--example-usage)  
- [Time Tool](#time-tool)  
  - [Step 1 – Import Packages](#step-1--import-packages-1)  
  - [Step 2 – Define Time Function](#step-2--define-time-function)  
  - [Step 3 – Wrap Function as StructuredTool](#step-3--wrap-function-as-structuredtool-1)  
  - [Step 4 – Example Usage](#step-4--example-usage-1)  

---

# Tavily Tool  

### Step 1 – Import Packages  
<details>
<summary>📂 Code</summary>

```python
import os
from langchain_tavily import TavilySearch
from langchain_core.tools import StructuredTool
from app.models.schemas import ToolOutput
from dotenv import load_dotenv

load_dotenv()
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
```

</details>

**Explanation:**  
Imports packages for Tavily search, structured tool creation, and environment variables.  

---

### Step 2 – Create Tavily Client  
<details>
<summary>📂 Code</summary>

```python
tavily = TavilySearch(
    max_results=5,
    topic="general",
    search_depth="basic",
    api_key=TAVILY_API_KEY
)
```

</details>

**Explanation:**  
Initializes a Tavily client for fetching recent/local housing information.  

---

### Step 3 – Define Tavily Search Function  
<details>
<summary>📂 Code</summary>

```python
def tavily_search(query: str) -> ToolOutput:
    """Search Tavily for recent/local housing info and return structured output."""
    result = tavily.invoke(query)
    return ToolOutput(
        tool="tavily_tool",
        input={"query": query},
        output=result,
        step="Search for recent/local housing info"
    )
```

</details>

**Explanation:**  
Wraps the Tavily query in a function that returns a structured `ToolOutput`, including a descriptive `step`.  

---

### Step 4 – Wrap Function as StructuredTool  
<details>
<summary>📂 Code</summary>

```python
tavily_tool = StructuredTool.from_function(
    func=tavily_search,
    name="tavily_tool",
    description="Use this to fetch recent/local housing info (tenant rights, rental assistance programs, deadlines, city/state policies)."
)
```

</details>

**Explanation:**  
Allows the Planner or Executor to call `tavily_search` as an automated LangChain tool.  

---

### Step 5 – Example Usage  
<details>
<summary>📂 Code</summary>

```python
query = "Affordable housing programs in NYC 2025"
result = tavily_tool.invoke({"query": query})
print(result.output)
```

</details>

**Explanation:**  
Demonstrates how to call the `tavily_tool` and retrieve recent/local housing information.  

---

# Time Tool  

### Step 1 – Import Packages  
<details>
<summary>📂 Code</summary>

```python
from datetime import datetime, timezone
from langchain_core.tools import StructuredTool
from app.models.schemas import ToolOutput
```

</details>

**Explanation:**  
Imports packages for getting the current date/time and creating structured tools.  

---

### Step 2 – Define Time Function  
<details>
<summary>📂 Code</summary>

```python
def time_tool_fn() -> ToolOutput:
    """Return the current date and time in ISO format."""
    now_iso = datetime.now(timezone.utc).isoformat()
    return ToolOutput(
        tool="time_tool",
        input={},
        output={"current_datetime": now_iso},
        step="Provide current date and time in ISO format for deadlines or cutoffs"
    )
```

</details>

**Explanation:**  
Returns the current UTC date and time in ISO format for planning tasks.  

---

### Step 3 – Wrap Function as StructuredTool  
<details>
<summary>📂 Code</summary>

```python
time_tool = StructuredTool.from_function(
    func=time_tool_fn,
    name="time_tool",
    description="Returns the current UTC date and time in ISO format. Useful for deadlines, eviction timelines, or rental assistance cutoffs."
)
```

</details>

**Explanation:**  
Enables the Planner or Executor to call `time_tool_fn` automatically as a LangChain tool.  

---

### Step 4 – Example Usage  
<details>
<summary>📂 Code</summary>

```python
result = time_tool.invoke({})
print(result.output)
```

</details>

**Explanation:**  
Demonstrates calling the `time_tool` to retrieve the current UTC date and time.  
