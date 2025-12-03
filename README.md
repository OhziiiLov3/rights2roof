#  <img src="https://i.imgur.com/MhEU6fv.png" alt="Logo" width="40" style="vertical-align: middle;"> Rights2Roof — AI Housing Rights Slack Bot  



## Table of Contents  
- [Overview](#overview)  
- [Architecture](#architecture) 
- [Core Components](#core-components) 
- [Production Setup (Slack Config)](#production-setup-slack-config)  
  - [Step 1 - Configure Slash Commands](#step-1---configure-slash-commands)
  - [Step 2 - Configure Event Subscriptions](#step-2---configure-event-subscriptions)
  - [Step 3 - Deployment Strategy](#step-3---deployment-strategy)
- [Local Development (Docker)](#local-development-docker)  
  - [Step 1 - Clone Repo](#step-1---clone-repo)  
  - [Step 2 – Create .env File](#step-2---create-env-file)  
  - [Step 3 – Docker Compose Services](#step-3---docker-compose-services)  
  - [Step 4 – Slack + ngrok Setup](#step-4---slack--ngrok-setup)  
  - [Step 5 – Configure Event Subscriptions (Local Dev)](#step-5---configure-event-subscriptions-local-dev)  
- [Contributors](#contributors)
- [Tech Stack](#tech-stack)  
- [Project Structure](#project-structure)  

***

# Overview  

Rights2Roof is a multi-service AI stack providing **tenant-rights assistance** via a Slack bot.  
It uses:

- FastAPI  
- Slack Events API  
- Model Context Protocol (MCP) FastMCP
- RedisStack (JSON, Search, Vectors)  
- Vector search + legal document scanning  
- Multi-turn contextual memory  
- Docker for local orchestration  
- Railway for production hosting  

---
# Architecture

**Workflow:**  
Slack → FastAPI (Slack Webhook) → MCP Server → Planner Agent/Tools → RAG Agents → Executor Agent / Tool → Response in Slack thread

![Rights2Roof Architecture](https://i.imgur.com/EH2IATJ.png)

# Core Components
### Feature Overview
<details>
<summary>Components</summary>

- **Slack Webhook (FastAPI):**  
  Receives `/rights-2-roof` and `/rights-2-roof-history` slash commands and Slack events.  
  Validates user input, manages location prompts, rate-limits users, and forwards sanitized requests to the MCP server.


- **MCP Server:**  
```python
from fastmcp import FastMCP        
rights2roof_server = FastMCP("rights2roof_tools")
# == Agent pipeline as tools ==
@rights2roof_server.tool(description="Run full Rights2Roof pipeline and return final answer")
def pipeline_tool(query: str, user_id: str, location: str = None) -> dict:
    """
    Run full pipeline and return JSON-safe response for Slack and logging.
    """
    if location:
        query = f"{query} (State: {location})"
    final_answer = pipeline_query(query, user_id)
    return {"result": final_answer}

def ping() -> str:
    return "pong"
if __name__ == "__main__":
    rights2roof_server.run(transport="http", host="0.0.0.0", port=5300, path="/mcp")
```
  Central orchestrator for the Rights2Roof agent system.  
  Manages:
  - Planner → RAG → Executor pipeline  
  - Tool routing  
  - Integration with Redis (cache, user context, history)  
  - Integration with the vector store  
  Returns a fully composed answer back to FastAPI for delivery into Slack.

- **LangGraph Orchestrated Agents:**  
  The multi-agent reasoning flow is built in **LangGraph**, which provides step-level control, memory boundaries, and deterministic agent transitions.  
  LangGraph manages:
  - Planner node  
  - RAG node  
  - Executor node  
  - Tool execution nodes  
  - State passing and multi-turn context  
  This ensures the system is fully deterministic, debuggable, and supports multi-turn Slack conversations.

 ```python
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
from app.models.pipeline_state import PipelineState
from app.agents.rag_node import rag_node
from app.agents.executor_node import executor_node
from app.agents.planner_node import planner_node

def build_pipeline_graph():

    checkpointer = InMemorySaver()

    graph = StateGraph(PipelineState, memory_saver=checkpointer)

    # Add nodes
    graph.add_node("planner", planner_node)
    graph.add_node("rag", rag_node)
    graph.add_node("executor", executor_node)

    # Define edges
    graph.add_edge(START, "planner") 
    graph.add_edge("planner", "rag")
    graph.add_edge("rag", "executor")
    graph.add_edge("executor", END)

    compiled_graph = graph.compile(checkpointer=checkpointer)

    return compiled_graph, checkpointer
 ```

- **Planner Agent:**  
  Interprets user intent and breaks questions into actionable steps.  
  Decides when to call tools such as:
  - Geo location  
  - Legislative search  
  - Vector retrieval  
  - Time tools  
  - Redis memory/context lookup  
  Produces a structured plan consumed by RAG + Executor.

- **RAG Agent / Tools:**  
  Retrieves all relevant information from internal and external knowledge sources:
  - **Redis Vector Store** (tenant guides, eviction PDFs, local/state housing laws)  
  - **Redis Cache** (recent responses, previous queries, user-specific context)  
  - **External live tools** (legislative databases, news search, Wikipedia, etc.)  
  Falls back to external search if the vector DB is missing domain coverage.

- **Executor Agent:**  
  Takes Planner output + RAG context and produces the final Slack-ready answer.  
  Responsibilities:
  - Synthesize findings into plain-language housing rights guidance  
  - Add citations, links, and explanations  
  - Ensure correct Slack formatting  
  - Adjust tone for clarity and safety

- **Redis Stack (Caching, Memory, Vector DB):**  
  Redis is a core part of the system and is used for **five different responsibilities**:

  1. **Rate Limiting (ZSET-based):**  
     Uses sorted sets to enforce *10 requests per user per hour*.  
     Clears expired timestamps and blocks excessive usage.

  2. **Chat History for Multi-Turn Conversations:**  
     Stores the last N user messages in sorted sets.  
     Enables context-aware follow-up responses.

  3. **Thread Tracking:**  
     Stores `last_thread_ts` per user to ensure all replies go into the correct Slack thread.

  4. **User Location Memory:**  
     Stores a user’s resolved city/state after prompting.  
     Allows jurisdiction-specific answers without re-asking every turn.

  5. **General Caching (set/get):**  
     Speeds up repeated queries by caching expensive computation for 1 hour.  
     Used by agents to avoid redundant RAG or external searches.

  6. **Redis Vector Store (Embeddings):**  
     Stores PDF embeddings (tenant law, statutes, eviction guides).  
     Provides similarity search for legal context through LangChain’s `RedisVectorStore`.  
     Used by the RAG agent to retrieve relevant excerpts with `k=5`.

- **Vector Store Tool:**  
  A LangChain StructuredTool that retrieves legal context from Redis vector DB.  
  Used when the user’s query requires legal knowledge, statute summaries, or document excerpts.

- **Response to Slack:**  
  FastAPI receives the agent output, attaches thread metadata, and posts the final formatted answer back into the user’s Slack thread.
  
This architecture enables **fast**, **stateful**, and **jurisdiction-aware** multi-turn conversations tailored to the user’s housing issue.

</details>


# Production Setup (Slack Config)
### Step 1 - Configure Slash Commands
<details>
<summary>Slash Commads + API step up</summary>

### [Rights 2 Roof Slack API](https://slack-api-production-c357.up.railway.app) deployed via railway 
1. Go to your Slack workspace → Settings & administration → Manage apps → Custom Integrations → Slash Commands.
2. **Create a new command**:
- Command: `/rights-2-roof`
- Request URL: `https://slack-api-production-c357.up.railway.app/slack/rights-2-roof`
- Method: POST
- Short description: Ask about tenant rights and housing issues.
- Usage hint: `/rights-2-roof` <your question here>
3. **Create a second command**:
- Command: `/rights-2-roof-history`
- Request URL: `https://slack-api-production-c357.up.railway.app/slack/rights-2-roof-history`
- Method: POST
- Short description: Retrieve recent tenant-rights queries and answer
4. Add environment variables in your Railway service:  
</details>

### Step 2 - Configure Event Subscriptions
<details>
<summary>Slack Events + API setup</summary>

### [Rights 2 Roof Slack API](https://slack-api-production-c357.up.railway.app) deployed via railway 
1. Enable Event Subscriptions in your Slack App.
2. Enter your Request URL: `https://slack-api-production-c357.up.railway.app/slack/events`
3. Subscribe to the following bot events:
- message.channels
- message.im
- message.groups
4. Save changes and install/update your app in the workspace.
</details>

### Step 3 - Deployment Strategy
<details>
<summary>How Rights2Roof is deployed on Railway</summary>

The production stack is deployed entirely on **Railway**, with each major component running as an isolated, scalable service. This separation keeps the system modular, fault-tolerant, and easy to maintain.

#### **Deployment Architecture (Railway)**

![Rights2Roof Deployment](https://i.imgur.com/zFayStu.png)

- **Slack FastAPI Service**  
  Hosts the Slack webhook endpoints (`/slack/rights-2-roof`, `/slack/rights-2-roof-history`, `/slack/events`).  
  Handles slash commands, event subscriptions, and routes user queries to the MCP server.  
  Runs independently so Slack can always reach your API.

- **MCP Server (FastMCP)**  
  Deployed as its own Railway service.  
  Runs the Planner → RAG → Executor pipeline, manages tools, calls Redis, queries the vector DB, and synthesizes answers.  
  This isolation ensures your reasoning engine scales without interfering with Slack traffic.

- **Redis Stack (Railway Redis)**  
  Used for:  
  - Multi-turn conversation history  
  - Caching RAG results  
  - Storing location context  
  - Temporary session state for Slack interactions  
  Redis dramatically reduces repeated calls to external APIs and speeds up follow-up questions.

- **Vector Store Service**  
  Runs separately to store:  
  - Tenant rights guides  
  - Legal documents  
  - Statutes  
  - Summaries and embeddings  
  Accessible by the MCP RAG tools for fast similarity search and cross-jurisdiction retrieval.

#### **Benefits of This Approach**
- Fully decoupled services → easier debugging & redeploys  
- MCP pipeline is free to scale independently from webhooks  
- Redis ensures fast multi-turn conversations with low latency  
- Vector DB enables high-quality legal RAG without overloading Redis  
- Railway handles logs, metrics, and service orchestration automatically  

This setup ensures that Rights2Roof stays reliable, low-latency, and production-ready — even during heavy Slack usage.
</details>

---
# Local Development (Docker)
### Step 1 - Clone Repo
<details>
<summary>Clone Repo + Create feature branch</summary>

```bash
# Step 1(a)- Clone repo 
git clone https://github.com/OhziiiLov3/rights2roof.git
cd rights2roof
# Step 1(b) - Swithc to Dev
git checkout dev
# Step 1(c) — Create feature branch
git checkout -b feature/add-something
# Step 1(d) — Work & Push
git push origin feature/add-something
```
</details> 

### Step 2 - Create .env File
<details>
<summary>env.example</summary>

```bash
# === OpenAI & APIs ===
OPENAI_API_KEY=your_openai_api_key_here
TAVILY_API_KEY=your_tavily_key_here
NEWSAPI_KEY=your_newsapi_key_here
LEGISCAN_API_KEY=your_legiscan_key_here
IP_ADDRESS=0.0.0.0

# === Slack Integration ===
SLACK_BOT_TOKEN=your_slack_bot_token_here
SLACK_SIGNING_SECRET=your_slack_signing_secret_here

# === Ngrok (optional) ===
NGROK_AUTHTOKEN=your_ngrok_authtoken_here
NGROK_DOMAIN=your-ngrok-subdomain.ngrok-free.app

# === MCP Service URL ===
MCP_SERVER_URL=http://mcp:5300/mcp

# === LangSmith Config ===
LANGSMITH_TRACING=true
LANGSMITH_ENDPOINT=https://api.smith.langchain.com
LANGSMITH_API_KEY=your_langsmith_api_key_here
LANGSMITH_PROJECT=rights2roof-pipeline

# === Redis Configuration ===
# For local dev, uncomment:
# REDIS_HOST=localhost
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0

# === Vector Store URL ===
VECTOR_STORE_URL=http://vector_store:5400

```
</details>

### Step 3 - Docker Compose Services
<details>
<summary>Using Docker Compose</summary>

```bash
services:
  redis:
    image: redis/redis-stack:latest
    ports:
      - "6379:6379"
      - "8001:8001"
    volumes:
      - redis_data:/data
    restart: unless-stopped

  vector_store:
    build: .
    env_file:
      - .env
    depends_on:
      - redis
    environment:
      - REDIS_HOST=redis
      - REDIS_PORT=6379
    command: ["uv", "run", "-m", "app.tools.vector_store_tool"]
    restart: "no"
    

  mcp:
    build: .
    env_file:
      - .env
    depends_on:
      - redis
      - vector_store
    environment:
      - REDIS_HOST=redis
      - REDIS_PORT=6379
      - VECTOR_STORE_URL=http://vector_store:5400 
    command: ["uv", "run", "-m", "app.server.mcp_server"]
    ports:
      - "5300:5300"
    restart: unless-stopped

  slack_api:
    build: .
    env_file:
      - .env
    depends_on:
      - redis
      - mcp
    environment:
      - REDIS_HOST=redis
      - REDIS_PORT=6379
      - MCP_SERVER_URL=http://mcp:5300/mcp
    command: uv run uvicorn app.services.slack_webhook:app --host 0.0.0.0 --port 8000 --reload
    ports:
      - "8000:8000"
    restart: unless-stopped

  ngrok:
    image: ngrok/ngrok:latest
    command: http slack_api:8000 --domain=${NGROK_DOMAIN}
    environment:
      - NGROK_AUTHTOKEN=${NGROK_AUTHTOKEN}
    depends_on:
      - slack_api
    ports:
      - "4040:4040"
    restart: unless-stopped

volumes:
  redis_data:

```
```bash
# Build and Run Docker Services
docker compose build
docker compose up
```
</details> 

### Step 4 - Slack + ngrok Setup
<details>
<summary>Slash Commands + Local API setup</summary>


### [Rights 2 Roof Slack API (Local via ngrok)](https://ngrok.com)  

1. Start your local FastAPI server and ngrok on port `8000`:

```bash
uvicorn app.services.slack_webhook:app --reload --host 0.0.0.0 --port 8000
ngrok http 8000
```
2. Copy the HTTPS URL **generated by ngrok** (e.g., https://<your-ngrok-id>.ngrok-free.app).
3. Go to your Slack workspace → Settings & administration → Manage apps → Custom Integrations → Slash Commands.
4. **Create a new command**:
- Command: `/rights-2-roof`
- Request URL: `https://<your-ngrok-id>.ngrok-free.app/slack/rights-2-roof`
- Method: POST
- Short description: Ask about tenant rights and housing issues.
- Usage hint: `/rights-2-roof` <your question here>
5. **Create a second command**:
- Command: `/rights-2-roof-history`
- Request URL: `https://<your-ngrok-id>.ngrok-free.app/slack/rights-2-roof-history`
- Method: POST
- Short description: Retrieve recent tenant-rights queries and answers.
6. Add environment variables in your .env file:
```bash
SLACK_SIGNING_SECRET=<your-slack-signing-secret>
SLACK_BOT_TOKEN=<your-slack-bot-token>
OPENAI_API_KEY=<your-openai-key>
NGROK_URL=https://<your-ngrok-id>.ngrok-free.app
```
</details> 

### Step 5 - Configure Event Subscriptions (Local Dev)
<details> <summary>Slack Events + Local API setup</summary>

### [Rights 2 Roof Slack API](https://ngrok.com/)
1. Enable Event Subscriptions in your Slack App.
2. Enter your Request URL:
`https://<your-ngrok-id>.ngrok-free.app/slack/events`
3. Subscribe to the following bot events:
- message.channels
- message.im
- message.groups
4. Save changes and install/update your app in the workspace.
</details> 

--- 
## Contributors 
Thank you to everyone who has contributed to **Rights2Roof**.  
Your work helps make housing rights more accessible for everyone.

### Core Contributors
| Name | Role | GitHub |
|------|------|--------|
| Keith Baskerville |  Communication Systems Lead | [@ohziiilov3](https://github.com/ohziiilov3) |
| Peter Iyayi | Deployment & Reliability Lead  |  [@PeterIyayi](https://github.com/PeterIyayi) |
| Celilia Kanne | Tooling & Intergration Lead| [@ceciliacloud](https://github.com/ceciliacloud) |
| Don Namgyal | Data & Evaluation Lead | [@dnamgyal](https://github.com/dnamgyal) |
| Chijioge Nwogu | Architecture & Planning Lead | [@chinwogu45-source](https://github.com/chinwogu45-source) |

### Want to Contribute?
We welcome contributions of all kinds, including:
- 🐛 Bug fixes  
- 📚 Documentation improvements  
- 🧩 New tools or agents  
- ⚙️ Improvements to the MCP pipeline  
- 🧪 Tests and workflow enhancements  
- 🚀 Feature proposals  

### How to Get Started
1. **Fork** the repo  
2. **Create a new branch** (`feature/my-update`)  
3. **Commit** your changes  
4. **Open a Pull Request** into `dev`  
5. The team will review and merge following the contribution guidelines

### Contributor Guidelines
- PRs must target the `dev` branch  
- Please follow the project coding style (Python + FastAPI + LangGraph conventions)  
- Add clear descriptions and context in your PR  
- Keep commits small and focused  

---
