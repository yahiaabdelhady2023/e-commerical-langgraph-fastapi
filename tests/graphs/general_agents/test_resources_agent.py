import pytest
from app.graphs.general_agents.resources_agent import build_resources_subgraph_agent
from langgraph.checkpoint.memory import MemorySaver


def test_classify_resource_node() -> None:
    checkpointer = MemorySaver()
    graph  = build_resources_subgraph_agent()
    compile_graph = graph.compile(checkpointer=checkpointer)

    print("graph nodes are",graph.nodes)
    #only invoking classify_resource node
    result = compile_graph.nodes["classify_resource"].invoke(
        {"current_resource":"product_list.txt"}
    )        

    assert result["type_resource"] == "txt"