from langgraph.graph import StateGraph, END
from app.pipelines.pipeline_state import PipelineState
from app.agents.planner_agent import planner_agent
from app.agents.rag_agent import rag_agent
from app.agents.executor_agent import execute_agent
from app.agents.planner_node import planner_node

# build pipeline graph 
def build_pipeline_graph():
    graph = StateGraph(PipelineState)
    graph.add_node("planner", planner_node)
    graph.add_node("rag", rag_agent)
    graph.add_node("executor", execute_agent)

    graph.add_edge("planner","rag")
    graph.add_edge("rag","executor")
    graph.add_edge("executor",END)

    return graph