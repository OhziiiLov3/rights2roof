from app.models.schemas import ExecutionPlan
from app.agents.executor_agent import execute_agent, execute_tool_call

if __name__=="__main__":
    test_plan=ExecutionPlan(plan=[
        "determine user city from IP address",
        "Get recent opportunities nearby",
    ])
    query="can my landord increase rent by 20%?"
    result=execute_agent(test_plan,query)

    print("final answer")
    print(result)

# Test executor agent - geo tool
geo_call = {"tool": "geo_location", "input": "8.8.8.8"}  # IP address for testing
geo_result = execute_tool_call(geo_call)
print("Geo Tool Output:", geo_result)

# Example 2: Test wikipedia_search
wiki_call = {"tool": "wikipedia_search", "input": "Venezuela history"}
wiki_result = execute_tool_call(wiki_call)
print("Wikipedia Tool Output:", wiki_result)
