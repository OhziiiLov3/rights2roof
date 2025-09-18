from datetime import datetime, timezone
from langchain_core.tools import StructuredTool
from app.models.schemas import ToolOutput


def time_tool_fn() -> ToolOutput:
    """Return the current date and time in ISO format."""
    now_iso = datetime.now(timezone.utc).isoformat() 
    return ToolOutput(
        tool="time_tool",
        input={},
        output={"current_datetime": now_iso},
        step="Provide current date and time in ISO format for deadlines or cutoffs"
    )


time_tool = StructuredTool.from_function(
    func=time_tool_fn,
    name="time_tool",
    description="Returns the current UTC date and time in ISO format. Useful for deadlines, eviction timelines, or rental assistance cutoffs."
)


   