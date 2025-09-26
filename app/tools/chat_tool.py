# app/tools/chat_tool.py
from app.services.redis_helpers import get_messages, add_message
from app.models.schemas import ToolOutput
from langchain_openai import ChatOpenAI
import os
from dotenv import load_dotenv
from langchain_core.tools import StructuredTool
import asyncio

# Load .env variables
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Initialize Gemini client
openAI_llm = ChatOpenAI(api_key=OPENAI_API_KEY, model="gpt-4.1", temperature=0)

async def chat_tool_fn(user_id: str, query: str) -> ToolOutput:
    """Follow-up Q&A agent using conversation history asynchronously."""
    
    def sync_call():
        history = get_messages(user_id, limit=10)
        context = "\n".join(history)
        answer = openAI_llm.invoke(f"Conversation so far:\n{context}\nUser: {query}\nAssistant:")
        add_message(user_id, f"CHAT_QUERY: {query}")
        add_message(user_id, f"CHAT_ANSWER: {answer.content}")
        return answer.content
    
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