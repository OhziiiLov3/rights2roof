from typing import List , TypedDict
from app.models.schemas import ExecutionPlan

class PipelineState(TypedDict, total=False):
    """
    shared state for mutli-agent pipeline.
    stores the user query, current plan, and conversation history
    """
    user_id: str
    query: str
    plan: ExecutionPlan | None 
    history: List[ExecutionPlan] = [] # multi-turn memory
    