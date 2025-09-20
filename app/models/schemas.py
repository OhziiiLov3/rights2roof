# Pydantic Schemas go here
from pydantic import BaseModel, Field
from typing import List, Any, Optional


# Defines schema for the Plan
class ExecutionPlan(BaseModel):
    plan: List[str] = Field(
        description="A list of steps to execute in order to answer a propmpt"
    )

# Define Schema for ToolOutput (execution agent will use this when ready)
class ToolOutput(BaseModel):
    tool: str
    input: Any
    output: Any
    step: Optional[str] = None 

# Define Schema for Execution Output
class ExecutorOutput(BaseModel):
    final_answer: str
    observations: List[ToolOutput]=[] 



