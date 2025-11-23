# serializers.py
from app.models.schemas import ToolOutput, ExecutionPlan
import logging

def serialize_tool_output(obj):
    """
    Recursively convert ToolOutput (and nested ToolOutputs) to dicts,
    converting 'step' to string to satisfy JSON serialization.
    """
    if isinstance(obj, ToolOutput):
        return {
            "tool": obj.tool,
            "input": serialize_tool_output(obj.input) if isinstance(obj.input, (ToolOutput, dict, list)) else obj.input,
            "output": serialize_tool_output(obj.output) if isinstance(obj.output, (ToolOutput, dict, list)) else obj.output,
            "step": str(obj.step) if obj.step is not None else None
        }
    elif isinstance(obj, list):
        return [serialize_tool_output(i) for i in obj]
    elif isinstance(obj, dict):
        return {k: serialize_tool_output(v) for k, v in obj.items()}
    else:
        return obj


def serialize_execution_plan(plan: ExecutionPlan):
    """
    Convert ExecutionPlan to a JSON-safe dict.
    """
    if not isinstance(plan, ExecutionPlan):
        return plan  # fallback

    return {
        "plan": [serialize_tool_output(step) for step in plan.plan]
    }


def ensure_execution_plan(plan_data) -> ExecutionPlan:
    """
    Convert input (dict, list, or ExecutionPlan) into a valid ExecutionPlan object
    with proper ToolOutput items.
    """
    if isinstance(plan_data, ExecutionPlan):
        return plan_data

    if isinstance(plan_data, dict):
        steps = plan_data.get("plan", [])
    elif isinstance(plan_data, list):
        steps = plan_data
    else:
        steps = []

    wrapped_steps = []
    for step in steps:
        if isinstance(step, ToolOutput):
            wrapped_steps.append(step)
        elif isinstance(step, dict):
            wrapped_steps.append(ToolOutput(**step))
        else:
            logging.warning(f"[ensure_execution_plan] Skipping invalid step: {step}")

    return ExecutionPlan(plan=wrapped_steps)
