from app.agents.planner_node import planner_node
from app.agents.rag_node import rag_node
from app.agents.executor_node import executor_node

user_id = "test_user"

# Simulate multiple turns
queries = [
    "Find recent tenant rights updates in Oakland",
    "What are the latest rent control changes?",
    "Provide links to official tenant resources"
]

# Initialize empty state
state = {"history": [], "user_id": user_id}

for i, query in enumerate(queries):
    print(f"\n--- Turn {i + 1} ---")
    
    # 1 Planner Node
    state["query"] = query
    state = planner_node(state)  # user_id is already in state
    
    # 2 RAG Node
    state = rag_node(state)
    
    # 3 Executor Node
    state = executor_node(state)
    
    # 4 Print result
    print("Query:", query)
    print("Executor Response:", state.get("executor_response"))
    print("Observations:", state.get("executor_observations"))
