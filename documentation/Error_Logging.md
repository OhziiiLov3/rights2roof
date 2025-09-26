# Planner Agent – Logging & Error Handling  
### Documentation by Keith Baskerville  

---
## Table of Contents  
- [Step 1 – Import Packages](#step-1--import-packages)  
- [Step 2 – Setup Logging](#step-2--setup-logging)  
- [Step 3 – Define Model for Planner Agent](#step-3--define-model-for-planner-agent)  
- [Step 4 – Load Output Parser](#step-4--load-output-parser)  
- [Step 5 – Add Tools](#step-5--add-tools)  
- [Step 6 – Create System Message](#step-6--create-system-message)  
- [Step 7 – Create Prompt Template](#step-7--create-prompt-template)  
- [Step 8 – Set Up Planner Chain](#step-8--set-up-planner-chain)  
- [Step 9 – Planner Agent with Logging & Error Handling](#step-9--planner-agent-with-logging--error-handling)  
- [Step 10 – Test Planner Agent](#step-10--test-planner-agent)  

---

### Step 1 – Import Packages  
<details>
<summary>📂 Code</summary>

```python
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_openai import ChatOpenAI
from app.models.schemas import ExecutionPlan
from app.tools import geo_tools
import os
from dotenv import load_dotenv
import logging

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
```

</details>

**Explanation:**  
Imports required packages for LangChain, OpenAI, environment variables, tools, and logging.  

---

### Step 2 – Setup Logging  
<details>
<summary>📂 Code</summary>

```python
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)
```

</details>

**Explanation:**  
Sets up basic logging so the Planner can record info and error messages during execution.  

---

### Step 3 – Define Model for Planner Agent  
<details>
<summary>📂 Code</summary>

```python
planner_llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0,
    openai_api_key=OPENAI_API_KEY
)
```

</details>

**Explanation:**  
Initializes the language model that powers the Planner.  

---

### Step 4 – Load Output Parser  
<details>
<summary>📂 Code</summary>

```python
plan_parser = PydanticOutputParser(pydantic_object=ExecutionPlan)
```

</details>

**Explanation:**  
Parses and validates the LLM’s output to match the `ExecutionPlan` schema.  

---

### Step 5 – Add Tools  
<details>
<summary>📂 Code</summary>

```python
AVAILABLE_TOOLS = [geo_tools.geo_tool]
tool_descriptions = [f"- {t.name}: {t.description}" for t in AVAILABLE_TOOLS]
```

</details>

**Explanation:**  
Lists available tools the Planner can call (e.g., Geo Tool).  

---

### Step 6 – Create System Message  
<details>
<summary>📂 Code</summary>

```python
system_message = f"""
You are a research planner. Break the user's query into a list of ordered steps.

You have access to the following tools:

{chr(10).join(tool_descriptions)}

Important guidelines:
- Use `geo_lookup` when you need location-specific information.
- Keep concise
- Always return steps as JSON following these format instructions:
{{format_instructions}}
- Do not include any text outside of the JSON.
"""
```

</details>

**Explanation:**  
Defines the Planner’s role and instructions for formatting output.  

---

### Step 7 – Create Prompt Template  
<details>
<summary>📂 Code</summary>

```python
planner_prompt = ChatPromptTemplate.from_messages([
   ("system", system_message),
   ("human", "{query}")
])
```

</details>

**Explanation:**  
Combines system instructions with user queries to provide structured input for the LLM.  

---

### Step 8 – Set Up Planner Chain  
<details>
<summary>📂 Code</summary>

```python
planner_chain = (
    planner_prompt.partial(format_instructions=plan_parser.get_format_instructions())
    | planner_llm
    | plan_parser
)
```

</details>

**Explanation:**  
Links the prompt → LLM → parser chain to produce a structured execution plan.  

---

### Step 9 – Planner Agent with Logging & Error Handling  
<details>
<summary>📂 Code</summary>

```python
def planner_agent(query: str):
    try:
        logging.info(f"Planner Agent invoked with query: {query}")
        result = planner_chain.invoke({"query": query})
        logging.info("Planner Agent successfully generated plan.")
        return result
    except Exception as e:
        logging.error(f"Error in planner_agent: {e}", exc_info=True)
        return {"error": str(e)}
```

</details>

**Explanation:**  
Wraps the Planner execution in `try/except` to log info and errors. Returns a structured error message if something fails.  

---

### Step 10 – Test Planner Agent  
<details>
<summary>📂 Code</summary>

```python
if __name__ == "__main__":
    test_query = "Help me create a plan to look for housing in my area"
    
    plan_result = planner_agent(test_query)
    print("Planner Agent Output:")
    print(plan_result)

    # Optional: Test Geo Tool with logging
    try:
        logging.info("Testing geo tool...")
        geo_output = geo_tools.geo_tool.invoke({"ip": None}, verbose=True)
        print(geo_output)
    except Exception as e:
        logging.error(f"Geo tool error: {e}", exc_info=True)
```

</details>

**Explanation:**  
Runs a sample query through the Planner Agent and logs the results. Also tests the Geo Tool with error handling.  

---

