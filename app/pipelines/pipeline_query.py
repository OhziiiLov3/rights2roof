# file to run pipeline -> export pipeline_query fn to the mcp_server to run as a tool 
import logging
import json
from langsmith import traceable
from langgraph.graph import StateGraph, END
from app.pipelines.pipeline_state import PipelineState
from app.services.redis_helpers import get_cached_result, cache_result
from app.agents.planner_agent import planner_agent
from app.agents.rag_agent import rag_agent
from app.agents.executor_agent import execute_agent
from app.models.schemas import ExecutorOutput






@traceable
def pipeline_query(user_query: str, user_id: str) -> str:
    """
    Run the full pipeline and return only the executor final answer for Slack.
    Full pipeline info is cached for history.
    """
    logging.info(f"[Pipeline] Running Planner for query: {user_query}")

    # Step 1: Check cache
    cache_key = f"user:{user_id}:query:{user_query}"
    cached = get_cached_result(cache_key)
    if cached:
        cached_data = json.loads(cached)
        return cached_data.get("executor_response", "No cached answer")

    # Step 2: Planner
    plan_result = planner_agent(user_query)

    # Step 3: RAG
    rag_result = rag_agent(plan_result, user_query)
    rag_response = rag_result.get("response", "No response available")

    # Step 4: Executor
    try:
        executor_result = execute_agent(rag_result, plan_result, user_query)
        executor_response = getattr(executor_result, "final_answer", str(executor_result))
    except Exception as e:
        executor_response = f"Executor agent failed: {str(e)}"

    # cache the plan, rag and excutor results 
    cached_obj = {
        "plan": plan_result.model_dump() if hasattr(plan_result, "model_dump") else plan_result,
        "rag_response": rag_response,
        "executor_response": executor_response
    }

    # Cache the full pipeline
    cache_result(cache_key, json.dumps(cached_obj))

    # Return just the executor response
    return executor_response



