# Rights2Roof 🏠

## 🚀 Overview
**Rights2Roof** is an open-source multi-agent Slack bot that helps tenants and landlords understand their housing rights.  
From eviction notice rules to rental assistance programs, the bot provides **plain-language, jurisdiction-specific guidance** with links to trusted resources.

Housing issues affect millions of people, yet laws and resources are fragmented and confusing. Rights2Roof bridges this gap by combining retrieval-augmented generation (RAG), planning, and execution agents to deliver clear answers where they’re needed most — in chat.

---


## ✨ Features
- **Slack Integration** — Trigger queries with `/R2Rbot`, receive threaded answers.
- **Planner Agent** — Detects user intent & jurisdiction, generates step-by-step action plans.
- **RAG Knowledge Base** — Retrieves laws, tenant guides, and housing program docs.
- **Dynamic Search Tools** — Fetch up-to-date legislation, programs, and news.
- **Executor Agent** — Synthesizes results into human-friendly, plain-language responses.
- **Geolocation** — Tailors responses to the user’s city/state.
- **Data Validation & Logging** — Pydantic schemas ensure structured, reliable outputs.
-**LangSmith Integration**  — With MCP + LangSmith monitoring, every call is structured and logged.
- **MCP Orchestration** — Agents communicate via Model Context Protocol (MCP) 
- **Vector DB & Caching** — Fast retrieval with document embeddings and Redis memory.

---

## 🧑‍💻 Example Scenarios
**Tenant in California**
```text
User: /R2Rbot Can my landlord raise rent by 20%?
Bot: “In California, rent increases are capped at 10% per year for most units under rent control. See the CA Department of Consumer Affairs guide."
```

**Case manager in New York**
```text
User: /R2Rbot eviction notice New York
Bot: “In New York, landlords usually must give 3 days’ notice before filing an eviction. More details here.”
```

***Tenant in NYC***
```text
User: /R2Rbot rental assistance NYC
Bot: “Here are rental assistance programs in NYC:
1. CityFHEPS – rent subsidies for low-income tenants.
2. ERAP – statewide emergency rent arrears program.
3. One-Shot Deal – one-time emergency rent grant.”
```
---

## 🧩 Architecture

**Workflow:**  
Slack → Planner Agent → RAG Agent → Executor Agent → Response in Slack thread  

- **Planner Agent:** Takes user intent (e.g., “I need help with rent in NYC”), breaks it into ordered steps, calls tools to get contextual info (Geo, Search, Time, etc.) .  
- **RAG Agent:** Pulls relevant info from vector DB (tenant guides, laws), falls back to search if DB doesn’t cover query.
- **Executor Agent:** Synthesizes final output, combines Planner + RAG outputs, returns a plain-language answer with links.


---
