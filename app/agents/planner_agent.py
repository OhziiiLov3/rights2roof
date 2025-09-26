from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_openai import ChatOpenAI
from app.models.schemas import ExecutionPlan, ToolOutput
from app.tools import geo_tools, wikipedia_tools, tavily_tools, time_tools
from langsmith import traceable

import os
from dotenv import load_dotenv




load_dotenv()
OPENAI_API_KEY=os.getenv("OPENAI_API_KEY")



#Step 1: Define Model for planner agent
planner_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, openai_api_key=OPENAI_API_KEY, verbose=True)

#Step 2: Load Output Parser - This parses the llm's text into structure JSON and validatas the data
plan_parser = PydanticOutputParser(pydantic_object=ExecutionPlan)


# Step 6: add tools, availablie tools listed in the prompt for reference (will add wikipedia or whatever tool to make this step better)
AVAILABLE_TOOLS = [geo_tools.geo_tool, wikipedia_tools.wikipedia_tool, tavily_tools.tavily_tool, time_tools.time_tool ]
tool_descriptions = [f"- {t.name}: {t.description}" for t in AVAILABLE_TOOLS]

# Map tool names to functions for execution
TOOL_MAP = {
    "geo_location": geo_tools.geo_tool,
    "wikipedia_search": wikipedia_tools.wikipedia_tool,
    "tavily_tool": tavily_tools.tavily_tool,
    "time_tool": time_tools.time_tool
}

# Step 3: Create system message(later will specific the tools)
system_message = f"""
You are a research planner. Break the user's query into a list of ordered steps.

You have access to the following tools:

{chr(10).join(tool_descriptions)}

Guidelines for tool usage:
- Only use `geo_location` if the query requires knowing the user's location (e.g., local events, nearby resources).
- Use `time_tool` if the query depends on current or future time (e.g., deadlines, dates, schedules).
- Use `wikipedia_search` for general background or definitions related to the query.
- Use `tavily_tool` (search) for recent, specific, or up-to-date information related to the query.

Important instructions:
- Choose tools that best help answer the user's query (do not always default to geo_location).
- For each step, include a "tool" field (geo_location, wikipedia_search, tavily_tool, time_tool).
- Provide concise inputs that make sense for the tool (e.g., query text, not "user's location").
- Always return steps as JSON following these format instructions:
{{format_instructions}}
- Do not include any text outside of the JSON.

 """

# Step 4: create system and human prompt
planner_prompt= ChatPromptTemplate.from_messages([
   ("system", system_message),
   ("human", "{query}")
])

# Step 5: Set up Planner Chain
planner_chain = planner_prompt.partial(format_instructions=plan_parser.get_format_instructions()) | planner_llm | plan_parser


# Helper: Execute a single tool and attach output
def execute_tool(step: ToolOutput) -> ToolOutput:
    tool_func = TOOL_MAP.get(step.tool)
    if not tool_func:
        step.output = f"Tool {step.tool} not found"
        return step
    try:
        # Execute tool (can adapt for async if needed)
        step.output = tool_func.invoke(step.input)
    except Exception as e:
        step.output = f"Error executing tool: {str(e)}"
    return step


# Step 6: Create Planner Agent with Error Loggins 
@traceable
def planner_agent(query: str):
    try:
        # 1 Generate plan with tool references
        plan_result: ExecutionPlan = planner_chain.invoke({"query": query})
        
        # 2️ Execute each tool to enrich steps
        enriched_plan = []
        for step in plan_result.plan:
            enriched_step = execute_tool(step)
            enriched_plan.append(enriched_step)
        return ExecutionPlan(plan=enriched_plan)
    except Exception as e:
        return ExecutionPlan(plan=[ToolOutput(tool="error", input=query, output=str(e))])



