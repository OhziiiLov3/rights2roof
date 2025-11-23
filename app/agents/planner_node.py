import logging
from langsmith import traceable
from app.agents.planner_agent import planner_chain, execute_tool
from app.models.schemas import ExecutionPlan, ToolOutput
from app.services.redis_helpers import get_messages
from app.services.serializers import serialize_tool_output

@traceable(run_type="tool")
def planner_node(state: dict) -> dict:
    """Generate an execution plan and return JSON-safe data."""
    query = state.get("query")
    user_id = state.get("user_id")
    history = state.get("history", [])

    prior_messages = get_messages(user_id, limit=10) if user_id else []
    context_query = (
        query + "\nPrevious conversation:\n" + "\n".join(prior_messages)
        if prior_messages else query
    )

    try:
        # 1. Produce raw plan
        plan_result = planner_chain.invoke({"query": context_query})

        # 2. Unwrap plan list
        if isinstance(plan_result, dict):
            raw_steps = plan_result.get("plan", [])
        else:
            raw_steps = getattr(plan_result, "plan", [])


        # 3. Execute steps
        enriched_steps = [execute_tool(step) for step in raw_steps]

        # 4. Wrap in ExecutionPlan (expects a list of ToolOutput objects)
        enriched_plan = ExecutionPlan(
            plan=[step if isinstance(step, ToolOutput) else ToolOutput(**step) for step in enriched_steps]
        )

        # 5. Store JSON-safe version for state/history
        plan_json_safe = [serialize_tool_output(step) for step in enriched_plan.plan]

        new_state = state.copy()
        new_state["plan"] = plan_json_safe
        new_state["history"] = state.get("history", []) + [plan_json_safe]
        return new_state

    except Exception as e:
        logging.error(f"[PlannerNode] Error: {str(e)}")

        # Create proper ToolOutput object for error
        error_step = ToolOutput(tool="error", input=query, output=str(e))
        error_plan = ExecutionPlan(plan=[error_step])

        plan_json_safe = [serialize_tool_output(step) for step in error_plan.plan]

        new_state = state.copy()
        new_state["plan"] = plan_json_safe
        new_state["history"] = history + [plan_json_safe]
        return new_state
