# file to run pipeline -> export pipeline_query fn to the mcp_server to run as a tool 
import logging
import json
from typing import Dict, Any
from langsmith import traceable
from app.services.redis_helpers import get_cached_result, cache_result
from app.agents.planner_agent import planner_agent


@traceable
def pipeline_query(user_query:str, user_id: str)-> Dict[str,Any]:
    """
    Full pipeline to process a user query:
    1. Planner generates steps
    2. RAG retrieves supporting info (stubbed)
    3. Executor synthesizes final answer (stubbed)
    """
    logging.info(f"[Pipeline] Running Planner for query: {user_query}")

    # Step 1: chech if query is cached
    cache_key = f"user{user_id}:query:{user_query}"
    cached = get_cached_result(cache_key)
    if cached:
        logging.info(f"[Pipeline] Cache hit for {user_query}")
        final_answer = json.loads(cached)
        return {"final_answer": final_answer, "cached": True}
    
    # Step 2 : Planner Agent
    plan_result = planner_agent(user_query)
    logging.info(f"[Pipeline] Planner output: {plan_result}")

    # Step 3: Rag Agent goes here 

    # Step 4: Executor goes here

    # Cache the final answer (will replace with exuection)
    final_answer = {"plan": plan_result.model_dump()}
    cache_result(cache_key, json.dumps(final_answer))

    # right now just return plan_result 
    return {"plan": plan_result, "cached": False}



