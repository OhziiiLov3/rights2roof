import logging
from langsmith import traceable
from app.tools.vector_store_tool import get_context
from app.agents.rag_agent import rag_chain
from app.services.redis_helpers import get_messages
from app.models.schemas import RagAgentResponse

@traceable(run_type="retriever")
def rag_node(state: dict) -> dict:
    """RAG node that retrieves context and returns JSON-safe dicts."""
    query = state.get("query")
    plan = state.get("plan")
    user_id = state.get("user_id")

    try:
        # 1. Previous messages
        previous_messages = get_messages(user_id, limit=10) if user_id else []
        previous_context = "\n".join(previous_messages)

        # 2. Vector store retrieval
        vector_context = get_context(query).output

        # 3. Merge context
        context = f"{previous_context}\n\n{vector_context}" if previous_context else vector_context

        # 4. Safe plan extraction
        plan_list = plan.get("plan", []) if isinstance(plan, dict) else plan

        # 5. Run RAG chain
        rag_result = rag_chain.invoke({
            "plan": plan_list,
            "query": query,
            "context": context
        })

        if isinstance(rag_result, RagAgentResponse):
            rag_result = rag_result.model_dump()

        new_state = state.copy()
        new_state["rag_response"] = rag_result
        return new_state

    except Exception as e:
        logging.error(f"[RAG Node] Error: {str(e)}")
        new_state = state.copy()
        new_state["rag_response"] = {"error": str(e)}
        return new_state
