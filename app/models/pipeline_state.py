from typing import List, TypedDict
from app.models.schemas import ExecutionPlan

class PipelineState(TypedDict, total=False):
    user_id: str
    query: str
    plan: ExecutionPlan | None
    history: List[ExecutionPlan]  # multi-turn memory
