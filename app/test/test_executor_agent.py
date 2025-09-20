from app.models.schemas import ExecutionPlan
from app.agents.executor_agent import execute_agent

if __name__=="__main__":
    test_plan=ExecutionPlan(plan=[
        "determine user city from IP address",
        "Get recent opportunities nearby",
    ])
    query="can my landord increase rent by 20%?"
    result=execute_agent(test_plan,query)

    print("final answer")
    print(result)
