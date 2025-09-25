# test_executor_agent.py

# Assuming the necessary imports and environment variables are set
import json
import logging
from app.models.schemas import ExecutionPlan, ToolOutput, ExecutorOutput, RagAgentResponse
from app.agents.executor_agent import execute_agent  # Import the function from your agent file

# Mock inputs for testing
user_query = "What are the tenant rights in Oakland, CA regarding rent increases?"
user_id = "user123"

# Create mock plan result (typically this comes from the planner)
plan_result = ExecutionPlan(
    plan=[ToolOutput(tool="wikipedia_search", input="tenant rights in Oakland CA", output="")]
)

# Create mock rag result (this would typically be returned from the RAG agent)
rag_result = RagAgentResponse(
    query=user_query,
    response="In Oakland, CA, tenant rights regarding rent increases are governed by several laws and regulations. Key points include: ..."
)

# Call the execute_agent function (this is the function that simulates the decision-making process and final output)
try:
    executor_result = execute_agent(rag_result, plan_result, user_query)

    # Print the final answer from the executor agent
    print(f"Final answer from executor agent: {executor_result.final_answer}")

except Exception as e:
    print(f"Error during testing: {str(e)}")
