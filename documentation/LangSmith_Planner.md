
---

# LangSmith – Planner Agent Traceable

### Documentation by Keith Baskerville

---

## Table of Contents

* [LangSmith Traceable](#langsmith-traceable)

  * [Step 1 – Import Packages](#step-1--import-packages)
  * [Step 2 – Apply `@traceable` Decorator](#step-2--apply-traceable-decorator)
  * [Step 3 – Example Usage](#step-3--example-usage)

---

# LangSmith Traceable

### Step 1 – Import Packages

<details>
<summary>📂 Code</summary>

```python
from langsmith import traceable
```

</details>

**Explanation:**
Imports the `traceable` decorator from LangSmith. This will automatically capture LLM calls, chain steps, and any outputs for observability in the LangSmith dashboard.

---

### Step 2 – Apply `@traceable` Decorator

<details>
<summary>📂 Code</summary>

```python
@traceable
def planner_agent(query: str):
    try:
        result = planner_chain.invoke({"query": query})
        return result
    except Exception as e:
        return {"error": str(e)}
```

</details>

**Explanation:**
The `@traceable` decorator wraps the `planner_agent` function. All invocations of the planner agent—including LLM calls, tool usage, and outputs—will be logged to LangSmith automatically.

*Note:* No `callback_manager` is needed for `ChatOpenAI`; the decorator handles all monitoring.

---

### Step 3 – Example Usage

<details>
<summary>📂 Code</summary>

```python
query = "I need help finding affordable housing in NYC"
result = planner_agent(query)
print(result)
```

</details>

**Explanation:**
Demonstrates calling the planner agent. The execution is tracked in LangSmith, where you can view step-by-step breakdowns, tools used, and final output.

---

