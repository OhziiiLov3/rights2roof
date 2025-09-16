from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_openai import ChatOpenAI

from app.models.schemas import ExecutionPlan

import os
from dotenv import load_dotenv

load_dotenv()
OPENAI_API_KEY=os.getenv("OPENAI_API_KEY")


#Step 1: Define Model for planner agent
planner_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, openai_api_key=OPENAI_API_KEY)

#Step 2: Load Output Parser - This parses the llm's text into structure JSON and validatas the data
plan_parser = PydanticOutputParser(pydantic_object=ExecutionPlan)


# Step 3: Create system message(later will specific the tools)
system_message = f"""
You are a research planner. Break the user's query into a list of ordered steps.
Important guidelines:
- Keep concise
- Always return steps as JSON following these format instructions:
{{format_instructions}}
- Do not include any text outside of the JSON.

 """

# Step 4: create system and human prompt
planner_propmt= ChatPromptTemplate.from_messages([
   ("system", system_message),
   ("human", "{query}")
])

# Step 5: Set up Planner Chain
planner_chain = planner_propmt.partial(format_instructions=plan_parser.get_format_instructions()) | planner_llm | plan_parser

# Step 6: Create Planner Agent 
def planner_agent(query: str):
    result = planner_chain.invoke({"query": query})
    return result

print(planner_agent("Help me create a plan to move into a new apartment"))