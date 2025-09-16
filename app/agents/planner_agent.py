from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_openai import ChatOpenAI
from app.models.schemas import ExecutionPlan
from app.tools import geo_tools
import os
from dotenv import load_dotenv
import logging



load_dotenv()
OPENAI_API_KEY=os.getenv("OPENAI_API_KEY")

# Setup basic logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)


#Step 1: Define Model for planner agent
planner_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, openai_api_key=OPENAI_API_KEY)

#Step 2: Load Output Parser - This parses the llm's text into structure JSON and validatas the data
plan_parser = PydanticOutputParser(pydantic_object=ExecutionPlan)


# Step 6: add tools, availablie tools listed in the prompt for reference (will add wikipedia or whatever tool to make this step better)
AVAILABLE_TOOLS = [geo_tools.geo_tool]

tool_descriptions = [f"- {t.name}: {t.description}" for t in AVAILABLE_TOOLS]


# Step 3: Create system message(later will specific the tools)
system_message = f"""
You are a research planner. Break the user's query into a list of ordered steps.

You have access to the following tools:

{chr(10).join(tool_descriptions)}

Important guidelines:
- Use `geo_lookup` when you need location-specific information.

Important guidelines:
- Keep concise
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

# Step 6: Create Planner Agent with Error Loggins 
def planner_agent(query: str):
    try:
        logging.info(f"Planner Agent invoked with query: {query}")
        result = planner_chain.invoke({"query": query})
        logging.info("Planner Agent successfully generated plan.")
        return result
    except Exception as e:
        logging.error(f"Error in planner_agent: {e}", exc_info=True)
    return result



# Test
# Test/debugging
import logging
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_openai import ChatOpenAI
from app.models.schemas import ExecutionPlan
from app.tools import geo_tools
import os
from dotenv import load_dotenv

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Setup basic logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)

# Step 1: Define Model for planner agent
planner_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, openai_api_key=OPENAI_API_KEY)

# Step 2: Load Output Parser
plan_parser = PydanticOutputParser(pydantic_object=ExecutionPlan)

# Step 3: Add tools
AVAILABLE_TOOLS = [geo_tools.geo_tool]
tool_descriptions = [f"- {t.name}: {t.description}" for t in AVAILABLE_TOOLS]

# Step 4: System message
system_message = f"""
You are a research planner. Break the user's query into a list of ordered steps.

You have access to the following tools:

{chr(10).join(tool_descriptions)}

Important guidelines:
- Use `geo_lookup` when you need location-specific information.
- Keep concise
- Always return steps as JSON following these format instructions:
{{format_instructions}}
- Do not include any text outside of the JSON.
"""

# Step 5: Create prompt
planner_prompt = ChatPromptTemplate.from_messages([
   ("system", system_message),
   ("human", "{query}")
])

# Step 6: Set up Planner Chain
planner_chain = planner_prompt.partial(format_instructions=plan_parser.get_format_instructions()) | planner_llm | plan_parser

# Step 7: Planner Agent with error logging
def planner_agent(query: str):
    try:
        logging.info(f"Planner Agent invoked with query: {query}")
        result = planner_chain.invoke({"query": query})
        logging.info("Planner Agent successfully generated plan.")
        return result
    except Exception as e:
        logging.error(f"Error in planner_agent: {e}", exc_info=True)
        return {"error": str(e)}

# Test
if __name__ == "__main__":
    test_query = "Help me create a plan to look for housing in my area"
    
    plan_result = planner_agent(test_query)
    print("Planner Agent Output:")
    print(plan_result)

    # Optional: Test geo tool with logging
    try:
        logging.info("Testing geo tool...")
        geo_output = geo_tools.geo_tool.invoke({"ip": None}, verbose=True)
        print(geo_output)
    except Exception as e:
        logging.error(f"Geo tool error: {e}", exc_info=True)





# print(planner_agent("Help me create a plan to move into a new apartment"))
# raw_output = (planner_prompt.partial(format_instructions=plan_parser.get_format_instructions()) | planner_llm).invoke(
#     {"query": "What are the key differences between photosynthesis and cellular respiration?"}
# )

# Prints json object a list of a "plan"
# print(raw_output.content)
