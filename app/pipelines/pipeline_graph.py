from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
from app.models.pipeline_state import PipelineState
from app.agents.rag_node import rag_node
from app.agents.executor_node import executor_node
from app.agents.planner_node import planner_node

def build_pipeline_graph():

    checkpointer = InMemorySaver()

    graph = StateGraph(PipelineState, memory_saver=checkpointer)

    # Add nodes
    graph.add_node("planner", planner_node)
    graph.add_node("rag", rag_node)
    graph.add_node("executor", executor_node)

    # Define edges
    graph.add_edge(START, "planner") 
    graph.add_edge("planner", "rag")
    graph.add_edge("rag", "executor")
    graph.add_edge("executor", END)

    compiled_graph = graph.compile(checkpointer=checkpointer)

    return compiled_graph, checkpointer