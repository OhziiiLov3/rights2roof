# execute_agent.py
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_openai import ChatOpenAI
from app.models.schemas import ExecutionPlan, ToolOutput, ExecutorOutput, RagAgentResponse
from app.tools import geo_tools, wikipedia_tools, tavily_tools, time_tools, google_news_tool, duckduckgo_tool, bing_rss_tool, legal_scan_tool, chat_tool
from langsmith import traceable
from typing import List

import os
from dotenv import load_dotenv

load_dotenv()


# Step 1: LLMs
executor_llm = ChatOpenAI(
    model="gpt-4o",
    temperature=0,
    openai_api_key=os.getenv("OPENAI_API_KEY")
)
synth_llm = ChatOpenAI(
    model="gpt-4o",
    temperature=0,
    openai_api_key=os.getenv("OPENAI_API_KEY")
)


# Step 2: Parsers
tool_parser = PydanticOutputParser(pydantic_object=ToolOutput)


# Step 3: Tool registry
TOOLS = {
    "geo_lookup": geo_tools.geo_tool,
    "wikipedia_search": wikipedia_tools.wikipedia_tool,
    "gnews_tool": google_news_tool.real_estate_news_tool,
    "tavily_tool": tavily_tools.tavily_tool,
    "time_tool": time_tools.time_tool,
    "broad_duckduckgo_search": duckduckgo_tool.duckduckgo,
    "bing_rss_tool": bing_rss_tool.bing_rss_tool,
    "legiscan_tool": legal_scan_tool.legiscan_tool,
    "chat_tool": chat_tool.chat_tool,
}


# Step 4: Executor Agent
@traceable
def execute_agent(rag_result: RagAgentResponse, plan_result: ExecutionPlan, query: str, verbose=False) -> ExecutorOutput:
    observations: List[ToolOutput] = []

    if isinstance(plan_result, dict):
        plan_result = ExecutionPlan(**plan_result)

    for idx, step in enumerate(plan_result.plan):
        # Ensure step id is JSON-safe
        step_id = getattr(step, "step", str(idx))
        # Step 1️: LLM chooses tool for this step
        decision_msg =  """
        You are an executor LLM that maps execution plan steps to the best tool.

        Available tools and purpose:
        - geo_lookup: get location info from IP or address
        - wikipedia_search: fetch factual background from Wikipedia
        - gnews_tool: get recent housing/real estate news and listings
        - tavily_tool: search structured/local housing info (listings, policies, assistance)
        - time_tool: get current date/time in ISO format
        - broad_duckduckgo_search: general purpose web search
        - bing_rss_tool: fetch recent tenant rights & affordable housing updates (California and New York focus)
        - legiscan_tool: search U.S. state legislation and bills (housing, tenant rights, eviction laws, rental policies)
        - chat_tool: follow-up Q&A agent using conversation history

        Instructions:
        - For each step, choose the tool that best matches the intent.
        - Return EXACTLY one JSON object like this:

        {{
        "tool": "<name_of_tool>",
        "input": {{"query": "<text_to_pass_to_tool>"}},
        "output": null
        }}

        - "tool" must be one of the tools above.
        - Do not include any extra text or explanations.
        - Make sure the JSON is valid.
        Examples:
        Step: "Find recent housing news in Brooklyn" -> tool: "gnews_tool", input.query: "recent housing news Brooklyn"
        Step: "Check local rent prices for apartments" -> tool: "tavily_tool", input.query: "rent prices apartments"
        Step: "Ask user if they want more details or Q&A" -> tool: "chat_tool", input.query: "Follow up with user for more questions"
        """

        decision_prompt = ChatPromptTemplate.from_messages([
            ("system",decision_msg),
            ("human", "Step: {step}")
        ])

        decision_chain = decision_prompt | executor_llm
        decision_content = getattr(decision_chain.invoke({"step": step}), "content", None)
        decision_content = decision_content or str(step)

        # Parse LLM decision
        decision: ToolOutput = tool_parser.parse(decision_content)
        tool_name = decision.tool
        tool_query = decision.input.get("query") or query

        # Step 3: Guard
        if tool_name not in TOOLS:
            if verbose:
                print(f"[Warning] Tool {tool_name} not found, skipping step.")
            continue

        # Step 4: Safe tool execution
        tool_instance = TOOLS[tool_name]
        tool_result = None
        
        if hasattr(tool_instance, "invoke"):
            tool_result = tool_instance.invoke({"query": tool_query}, verbose=verbose)
        elif hasattr(tool_instance, "run"):
            tool_result = tool_instance.run(tool_query)

        # Ensure output is JSON-safe
        if hasattr(tool_result, "model_dump"):
            tool_result = tool_result.model_dump()
        elif hasattr(tool_result, "dict"):
            tool_result = tool_result.dict()

        decision.output = tool_result
        decision.step = step_id
        observations.append(decision)

        if verbose:
            print(f"[Executor] Step: {step_id}")
            print(f"[Executor] Tool: {tool_name}")
            print(f"[Executor] Result: {tool_result}\n")

    synthesis_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful research assistant. Use the observations to answer clearly and concisely."),
    ("human",
    """
    User query: {query}

    Observations from tools:
    {observations}

    Instructions:
    - Provide a concise answer to the user.
    - Integrate relevant information from all tools.
    - Provide links to helpful and relevant resources
    - Do NOT include raw tool outputs, only the synthesized answer.
    """)
    ])
    synthesis_chain = synthesis_prompt | synth_llm

    final_answer_msg = synthesis_chain.invoke({
        "query": query,
        "observations": [obs.model_dump() for obs in observations]
    })

    final_answer_text = getattr(final_answer_msg, "content", str(final_answer_msg))

    # Return serialized observations 
    return ExecutorOutput(
        final_answer=final_answer_text,
        observations=observations  
)
