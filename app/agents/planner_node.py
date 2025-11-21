from langsmith import traceable
from app.agents.planner_agent import planner_chain, execute_tool
from app.models.schemas import ExecutionPlan, ToolOutput
import logging


# langgrapg node for planner agent, accepts and returns pipelineState Dict
@traceable
def planner_node(state: dict) -> dict:

    query = state.get("query")
    history = state.get("history",[])

    # 1. Build context: inject history into the LLM prompt
    if history:
        prior = []
        for plan in history:
            for step in plan["plan"]:
                prior.append(f"{step['tool']}: {step['output']}")
        context_query = query + "\nPrevious steps:\n" + "\n".join(prior)
    else:
        context_query = query

    try:
        # 2. Generate a plan 
        plan_result = planner_chain.invoke({"query": context_query})

        # 3. Execute tools
        enriched_steps = []
        for step in plan_result.plan:
            enriched = execute_tool(step)
            enriched_steps.append(enriched)
            
        enriched_plan = ExecutionPlan(plan=enriched_steps)

        # 4. Update State
        new_state = state.copy()
        new_state["plan"] = enriched_plan
        new_state["history"] = history + [enriched_plan]

        logging.info("[PlannerNode] Plan generated")
        return new_state

    except Exception as e:
        logging.error(f"[PlannerNode] Error: {str(e)}")

        error_plan = ExecutionPlan(plan=[
            ToolOutput(tool="error", input=query, output=str(e))
        ])

        new_state = state.copy()
        new_state["plan"] = error_plan
        new_state["history"] = history + [error_plan]
        return new_state
        
    # test 
if __name__ == "__main__":
  
    test_query = "Find news about housing policy in Oakland"
    print("\nRunning planner_node test...\n")

        # Whatever function your node exposes
    result = planner_node({"query": test_query})

    print("\n--- Planner Node Output ---\n")
    print(result)