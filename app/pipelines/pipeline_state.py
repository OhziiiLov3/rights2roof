from typing import List 
from app.models.schemas import ExecutionPlan

class PipelineState:
    """
    shared state for mutli-agent pipeline.
    stores the user query, current plan, and conversation history
    """
    user_id: str
    query: str
    plan: ExecutionPlan | None = None
    history: List[ExecutionPlan] = [] # multi-turn memory
    