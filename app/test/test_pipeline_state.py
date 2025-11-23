# test_pipeline_graph.py
from app.pipelines.pipeline_graph import build_pipeline_graph
from langchain_core.runnables import RunnableConfig
import pprint

def main():
    graph, checkpointer = build_pipeline_graph()

    # Initial state
    state = {
        "user_id": "test_user",
        "query": "Find affordable housing in SF",
        "plan": None,
        "history": []
    }

    # Thread ID for LangGraph persistence
    thread_id = "pipeline_thread:test_user"
    config: RunnableConfig = {"configurable": {"thread_id": thread_id}}

    # Invoke graph
    result = graph.invoke(state, config=config)
    print("Graph invoke returned:", result)

    # Get latest state snapshot
    state_snapshot = graph.get_state(config=config)
    print("\nCurrent checkpoint: ")
    pprint.pprint(state_snapshot.values)

    # Get full state history
    history = graph.get_state_history(config=config)
    print("\nState history: ")
    for idx, snap in enumerate(history):
        print(f"Checkpoint {idx}: values={snap.values}, metadata={snap.metadata}")

if __name__ == "__main__":
    main()
