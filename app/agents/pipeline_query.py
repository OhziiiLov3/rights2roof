# file to run pipeline -> export pipeline_query fn to the mcp_server to run as a tool 
import logging
from typing import Dict, Any
from langsmith import traceable

from app.agents.planner_agent import planner_agent


@traceable
def pipeline_query(user_query:str)-> Dict[str,Any]:
    """
    Full pipeline to process a user query:
    1. Planner generates steps
    2. RAG retrieves supporting info (stubbed)
    3. Executor synthesizes final answer (stubbed)
    """
    logging.info(f"[Pipeline] Running Planner for query: {user_query}")

    # Step 1 : Planner Agent
    plan_result = planner_agent(user_query)
  
    if hasattr(plan_result, "model_dump"):
        plan_steps = plan_result.model_dump().get("plan", [])
    elif isinstance(plan_result, str):
        plan_steps = {"plan": [plan_result]}
    elif isinstance(plan_result, list):
        plan_steps = {"plan": plan_result}


    # Step 2: Rag Agent goes here 


    # Step 3: Executor goes here


    # right now just return plan_result 
    return {"plan": plan_steps}

def ping() -> str:
    return "Pipeline MCP is alive"
