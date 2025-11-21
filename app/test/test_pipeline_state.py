import pytest
from app.models.pipeline_state import PipelineState
from app.models.schemas import ExecutionPlan, ToolOutput
import logging

logging.basicConfig(level=logging.INFO)

def test_pipeline_state_init():
    logging.info("Initializing PipelineState...")

    state = PipelineState()
    state.user_id = "user123"
    state.query = "Find affordable housing in SF"

    # Sample step and plan
    sample_step = ToolOutput(tool="wikipedia_search", input="housing rights", output="Sample output")
    sample_plan = ExecutionPlan(plan=[sample_step])

    # Print / log the sample plan
    print("Sample plan (raw object):", sample_plan)
    logging.info("Sample plan as dict: %s", sample_plan.model_dump())
    logging.info("Sample plan as JSON:\n%s", sample_plan.model_dump_json(indent=2))

    state.plan = sample_plan    
    state.history.append(sample_plan)

    logging.info(f"Updated state.plan: {state.plan.model_dump()}")
    logging.info(f"Updated state.history length: {len(state.history)}")

    assert state.plan == sample_plan
    assert len(state.history) == 1
    assert state.history[0].plan[0].tool == "wikipedia_search"
