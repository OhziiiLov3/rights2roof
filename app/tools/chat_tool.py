# app/tools/chat_tool.py
from app.services.redis_helpers import add_message, get_cached_result
from app.tools.vector_store_tool import get_context
from app.models.schemas import ToolOutput
from langchain_openai import ChatOpenAI
import os
import json
from dotenv import load_dotenv
from langchain_core.tools import StructuredTool

import asyncio
from langsmith import traceable

# Load .env variables
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Initialize llm client
followup_llm = ChatOpenAI(
    api_key=OPENAI_API_KEY, 
    model="gpt-4.1",
    temperature=0
)

@traceable()
async def chat_tool_fn(user_id: str, query: str) -> ToolOutput:
    """Follow-up Q&A agent using conversation history asynchronously."""
    from app.pipelines.pipeline_query import pipeline_query
    def sync_call():
        # === Load pipeline history ===
        cache_key = f"user:{user_id}:history"
        cached = get_cached_result(cache_key)
        history = json.loads(cached).get("history", []) if cached else []
        
        last_turn = history[-1] if history else {}
        prev_answer = last_turn.get("executor_response", "")
        prev_plan = last_turn.get("plan", {})
        prev_rag = last_turn.get("rag_response", "")

        # === Optional: add vector store lookup for deeper follow-up ===
        vector_results = get_context(query)
        vector_text = "\n".join([d.page_content for d in vector_results.output]) if vector_results.output else ""

        prompt = f"""
        You are Rights2Roof, a tenant rights legal assistant.

        **User's new follow-up question:**
        {query}

        **Previous assistant answer:**
        {prev_answer}

        **Previous plan:**
        {prev_plan}

        **Previous legal citations + RAG info:**
        {prev_rag}

        **Additional relevant legal context from vector search:**
        {vector_text}

        Provide a clear, legally accurate follow-up answer that stays consistent
        with the prior reasoning and California/US tenant law when applicable.
        """

        answer = followup_llm.invoke(prompt).content

        # track follow-ups in redis history if needed
        add_message(user_id, f"FOLLOWUP_QUERY: {query}")
        add_message(user_id, f"FOLLOWUP_ANSWER: {answer}")

        return answer
    
    output = await asyncio.to_thread(sync_call)
    
    return ToolOutput(
        tool="chat_tool",
        input={"query": query},
        output=output,
        step="Follow-up Q&A agent"
    )


chat_tool = StructuredTool.from_function(
    func=chat_tool_fn,
    name="chat_tool",
    description="Follow-up conversational agent for tenant/housing Q&A using conversation history via Gemini."
)