import logging 
from langsmith import traceable
from app.models.schemas import RagAgentResponse
from app.tools.vector_store_tool import get_context
from app.agents.rag_agent import rag_chain


# langgraph node for rag agent, accepts pipeline state dict and returns updated state with RAG response

@traceable
def rag_node(state:  dict) -> dict:
    query = state.get("query")
    plan = state.get("plan")
    history = state.get("history", [])


    try:
        # 1. Get context from vector store
        context = get_context(query).output

        # 2. Prepare chain input 
        plan_input = plan
        if hasattr(plan, "plan"): 
            # convert toolouput objects to dicts
            plan_input = [step.model_dump() if hasattr(step,"model_dump") else step for step in plan.plan]

        #  3. Run RAG chain 
        rag_result = rag_chain.invoke({"plan": plan_input, "query":query ,"context": context})
        
        # 4. Convert to dict if Pydantic object 
        if isinstance(rag_result, RagAgentResponse):
            rag_result = rag_result.model_dump()
        # 5. Update pipeline state

        new_state = state.copy()
        new_state["rag_response"] = rag_result
        return new_state
    
    except Exception as e:
        logging.error(f"[RAG Node] Error:{str(e)}")
        new_state = state.copy()
        new_state["rag_response"] = {"error": str(e)}
        return new_state
    
# Simple test 
if __name__ == "__main__":
    test_query = "What are the tenant rights in Oakland, CA?"
    test_plan = [{"tool": "wikipedia_search", "input": "tenant rights", "output": None, "step": "1"}]

    result = rag_node({"query": test_query, "plan": test_plan, "history": []})
    print("\n--- RAG Node Output ---\n")
    print(result)