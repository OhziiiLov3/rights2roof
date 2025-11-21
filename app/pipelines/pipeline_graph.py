from langgraph.graph import StateGraph, END
from app.models.pipeline_state import PipelineState
from app.agents.rag_node import rag_node
from app.agents.executor_node import executor_node
from app.agents.planner_node import planner_node


# build pipeline graph 
def build_pipeline_graph():
    graph = StateGraph(PipelineState)
    graph.add_node("planner", planner_node)
    graph.add_node("rag", rag_node)
    graph.add_node("executor", executor_node)

    graph.add_edge("planner","rag")
    graph.add_edge("rag","executor")
    graph.add_edge("executor",END)

    return graph