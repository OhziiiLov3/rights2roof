# Smoke Test For Planner Agent 
from app.agents.planner_agent import planner_agent
from app.tools import geo_tools, wikipedia_tools, tavily_tools
import logging


# Test with wikipedia and geolocation and Tavily tool
if __name__ == "__main__":
    test_query = "Help me create a plan to look for housing in my area"

    # Test Planner Agent
    try:
        plan_result = planner_agent(test_query)
        print("Planner Agent Output:")
        print(plan_result)
    except Exception as e:
        logging.error(f"Planner agent error: {e}", exc_info=True)

    # Test Geo Tool
    try:
        logging.info("Testing geo tool...")
        geo_output = geo_tools.geo_tool.invoke({"ip": None}, verbose=True)
        print("Geo Tool Output:")
        print(geo_output)
    except Exception as e:
        logging.error(f"Geo tool error: {e}", exc_info=True)

    # Test Wikipedia Tool
    try:
        logging.info("Testing Wikipedia tool...")
        wiki_output = wikipedia_tools.wikipedia_tool.invoke({"query": "Help me find rental assistance programs"}, verbose=True)
        print("Wikipedia Tool Output:")
        print(wiki_output)
    except Exception as e:
        logging.error(f"Wikipedia tool error: {e}", exc_info=True)
    
     # Test Tavily Tool
    try:
        logging.info("Testing Tavily search tool...")
        tavily_output = tavily_tools.tavily_tool.invoke(
            {"query": "NYC rental assistance September 2025"},
            verbose=True
        )
        print("Tavily Tool Output:")
        print(tavily_output.model_dump_json(indent=2))  # Pydantic v2 safe print
    except Exception as e:
        logging.error(f"Tavily tool error: {e}", exc_info=True)



# simple test

# print(planner_agent("Help me create a plan to move into a new apartment"))
# raw_output = (planner_prompt.partial(format_instructions=plan_parser.get_format_instructions()) | planner_llm).invoke(
#     {"query": "What are the key differences between photosynthesis and cellular respiration?"}
# )

# Prints json object a list of a "plan"
# print(raw_output.content)