# Wikipedia Tool  
### Documentation by Keith Baskerville  

---
## Table of Contents  
- [Step 1 – Import Packages](#step-1--import-packages)  
- [Step 2 – Create Wikipedia Client](#step-2--create-wikipedia-client)  
- [Step 3 – Define Wikipedia Search Function](#step-3--define-wikipedia-search-function)  
- [Step 4 – Wrap Function as StructuredTool](#step-4--wrap-function-as-structuredtool)  
- [Step 5 – Example Usage](#step-5--example-usage)  

---

### Step 1 – Import Packages  
<details>
<summary>📂 Code</summary>

```python
from langchain_community.tools import WikipediaQueryRun
from langchain_community.utilities import WikipediaAPIWrapper
from langchain_core.tools import StructuredTool
from app.models.schemas import ToolOutput
```

</details>

**Explanation:**  
Imports packages for interacting with Wikipedia, creating LangChain tools, and defining output schemas.  

---

### Step 2 – Create Wikipedia Client  
<details>
<summary>📂 Code</summary>

```python
wikipedia = WikipediaQueryRun(api_wrapper=WikipediaAPIWrapper())
```

</details>

**Explanation:**  
Initializes a Wikipedia client using the LangChain API wrapper, which handles queries to the Wikipedia API.  

---

### Step 3 – Define Wikipedia Search Function  
<details>
<summary>📂 Code</summary>

```python
def wikipedia_search(query: str):
    """Search Wikipedia for a given topic and return the result text."""
    result = wikipedia.run(query)
    return ToolOutput(
        tool="wikipedia_search",
        input={"query": query},
        output=result,
        step="Look up updates to Rental Laws and Affordable Housing information"
    )
```

</details>

**Explanation:**  
Defines a function that takes a user query, searches Wikipedia, and returns a structured `ToolOutput`.  
The `step` field explains the purpose of the tool for the Planner/Executor.  

---

### Step 4 – Wrap Function as StructuredTool  
<details>
<summary>📂 Code</summary>

```python
wikipedia_tool = StructuredTool.from_function(
    func=wikipedia_search,
    name="wikipedia_search",
    description="Search Wikipedia for information on a topic."
)
```

</details>

**Explanation:**  
Wraps the `wikipedia_search` function as a `StructuredTool`, allowing the Planner or Executor agent to call it automatically with inputs.  

---

### Step 5 – Example Usage  
<details>
<summary>📂 Code</summary>

```python
# Example usage
query = "Tenant rights in New York 2025"
result = wikipedia_tool.invoke({"query": query})
print(result.output)
```

</details>

**Explanation:**  
Demonstrates how to call the `wikipedia_tool` and access the retrieved Wikipedia text.  

---
