import logging
import json
from langsmith import traceable
from app.services.redis_helpers import get_cached_result, cache_result
from app.agents.planner_node import planner_node
from app.agents.rag_node import rag_node
from app.agents.executor_node import executor_node
from app.services.serializers import (
    serialize_tool_output,
    serialize_execution_plan,
    ensure_execution_plan
)
from app.models.schemas import ExecutionPlan

@traceable(run_type="chain", name="Pipeline Execution")
def pipeline_query(user_query: str, user_id: str) -> str:
    """
    Run the full Rights2Roof pipeline and return the executor final answer.
    Handles dicts vs Pydantic objects, integrates serializer for JSON safety.
    """
    logging.info(f"[Pipeline] Running Planner for query: {user_query}")

    # 1. Check cache
    cache_key = f"user:{user_id}:query:{user_query}"
    cached = get_cached_result(cache_key)
    if cached:
        cached_data = json.loads(cached)
        logging.info("[Pipeline] Returning cached result")
        return cached_data.get("executor_response", "No cached answer")

    # 2. Run nodes

    # Planner node -> returns dict
    plan_result = planner_node({"query": user_query, "user_id": user_id, "history": []})
    plan_obj: ExecutionPlan = ensure_execution_plan(plan_result)

    # RAG node -> receives JSON-safe plan
    rag_result = rag_node({
        "query": user_query,
        "plan": serialize_execution_plan(plan_obj)["plan"],
        "history": [],
        "user_id": user_id
    })

    # Executor node -> receives proper ExecutionPlan object
    executor_result = executor_node({
        "query": user_query,
        "plan": plan_obj,
        "rag_response": rag_result.get("rag_response"),
        "user_id": user_id
    })

    executor_response = executor_result.get("executor_response", "No response from executor")

    # 3. Serialize and cache full pipeline result
    cache_obj = {
        "plan": serialize_execution_plan(plan_obj),
        "rag_response": rag_result.get("rag_response"),
        "executor_response": executor_response,
        "executor_observations": serialize_tool_output(executor_result.get("executor_observations"))
    }
    cache_result(cache_key, json.dumps(cache_obj))

    return executor_response
