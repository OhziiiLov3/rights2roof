import logging
import json
from langsmith import traceable
from app.services.redis_helpers import get_cached_result, cache_result, get_user_location
from app.agents.planner_node import planner_node
from app.agents.rag_node import rag_node
from app.agents.executor_node import executor_node
from app.services.serializers import (
    serialize_tool_output,
    serialize_execution_plan,
    ensure_execution_plan
)
from app.models.schemas import ExecutionPlan
from app.models.pipeline_state import PipelineState

@traceable(run_type="chain", name="Pipeline Execution")
def pipeline_query(user_query: str, user_id: str) -> str:
    """
    Run the Rights2Roof pipeline with multi-turn support.
    Maintains history between queries for the same user.
    """
    logging.info(f"[Pipeline] Running query: {user_query}")

    # Cache key for multi-turn history
    cache_key = f"user:{user_id}:history"
    cached = get_cached_result(cache_key)
    history = []
    if cached:
        history = json.loads(cached).get("history", [])
        logging.info(f"[Pipeline] Loaded {len(history)} previous steps from history")

    # Planner node -> returns dict
    plan_result = planner_node({"query": user_query, "user_id": user_id, "history": history})
    plan_obj: ExecutionPlan = ensure_execution_plan(plan_result)

    # RAG node -> receives JSON-safe plan
    rag_result = rag_node({
        "query": user_query,
        "plan": serialize_execution_plan(plan_obj)["plan"],
        "history": history,
        "user_id": user_id
    })
    location = get_user_location(user_id)
    # Executor node -> receives proper ExecutionPlan object
    executor_result = executor_node({
        "query": user_query,
        "plan": plan_obj,
        "rag_response": rag_result.get("rag_response"),
        "history": history,
        "user_id": user_id,
        "location": location
    })

    executor_response = executor_result.get("executor_response", "No response from executor")

    # Update history with the new turn
    history.append({
        "query": user_query,
        "plan": serialize_execution_plan(plan_obj),
        "rag_response": rag_result.get("rag_response"),
        "executor_response": executor_response,
        "executor_observations": serialize_tool_output(executor_result.get("executor_observations"))
    })

    # Cache updated history
    cache_result(cache_key, json.dumps({"history": history}))

    return executor_response

