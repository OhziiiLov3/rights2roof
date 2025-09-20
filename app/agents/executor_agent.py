from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_openai import ChatOpenAI
from app.models.schemas import ExecutionPlan, ToolOutput, ExecutorOutput
from app.tools import wikipedia_tools, tavily_tools, google_news_tool
from langsmith import traceable
from typing import List

import os
from dotenv import load_dotenv

load_dotenv()
OPENAI_API_KEY=os.getenv("OPENAI_API_KEY")

#Step 1: Define Model LLM for executor agent and combined result
executor_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, openai_api_key=OPENAI_API_KEY, verbose=True)
combined_llm = ChatOpenAI(model="gpt-4o", temperature=0, openai_api_key=OPENAI_API_KEY, verbose=True)

#Step 2:
tool_parser=PydanticOutputParser(pydantic_object=ToolOutput)

#Step 3: Create Dictionary of tools
TOOLS= {
    "wikipedia_search":wikipedia_tools.wikipedia_tool,
    "tavily_tool":tavily_tools.tavily_tool,
    "real_estate_news_update":google_news_tool.real_estate_news_tool,
}

#Step 4: Create function to run our agent - we will need to come back and update with RAG Agent into argument to replace "query"
def execute_agent(plan:ExecutionPlan,query:str,verbose=False)->ExecutorOutput:
    """
    runs each step in the plan:
    1) Uses LLM to select the best tool
    2) Invokes the tool
    3) Combines a final answer from the tool outputs
    """

    observations:List[ToolOutput]=[]
    return ExecutorOutput(final_answer="",observations=[])
