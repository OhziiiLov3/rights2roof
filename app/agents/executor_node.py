import logging
from langsmith import traceable
from app.agents.executor_agent import execute_agent
from app.services.redis_helpers import add_message
from app.services.serializers import serialize_tool_output, ensure_execution_plan

@traceable(run_type="chain")
def executor_node(state: dict) -> dict:
    """Runs the executor and returns JSON-safe data."""
    try:
        plan_data = state.get("plan")
        rag_response = state.get("rag_response")
        query = state.get("query")
        user_id = state.get("user_id")

        if not plan_data:
            logging.warning("[ExecutorNode] No plan in state.")
            return state

        # Ensure valid ExecutionPlan object
        plan_obj = ensure_execution_plan(plan_data)

        # Execute agent
        executor_result = execute_agent(
            rag_result=rag_response,
            plan_result=plan_obj,
            query=query,
            verbose=True
        )

        # JSON-safe serialization
        serialized_observations = serialize_tool_output(executor_result.observations)
        serialized_plan = serialize_tool_output(plan_obj.plan)

        if user_id:
            add_message(user_id, f"user: {query}")
            add_message(user_id, f"agent: {executor_result.final_answer}")

        new_state = state.copy()
        new_state["executor_response"] = executor_result.final_answer
        new_state["executor_observations"] = serialized_observations
        new_state["plan"] = serialized_plan
        return new_state

    except Exception as e:
        logging.error(f"[ExecutorNode] Error: {str(e)}")
        new_state = state.copy()
        new_state["executor_response"] = f"Executor failed: {e}"
        new_state["executor_observations"] = []
        return new_state
