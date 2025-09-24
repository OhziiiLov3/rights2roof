# Pydantic Schemas go here
from pydantic import BaseModel, Field
from typing import List, Any, Optional


# Define Schema for ToolOutput (execution agent will use this when ready)
class ToolOutput(BaseModel):
    tool: str
    input: Any
    output: Any
    step: Optional[str] = None 




# Defines schema for the Plan
class ExecutionPlan(BaseModel):
    plan: List[ToolOutput] = Field(
        description="A list of steps to execute in order to answer a propmpt"
    )

class RagAgentResponse(BaseModel):
    query: str = Field(description="User's original query to the RAG agent")
    response: str = Field(description="The information the RAG agent was able to gather based on the context provided and the user's query")