import pytest
from app.graphs.specialist_agents.culture_agent import build_culture_agent
from langgraph.checkpoint.memory import MemorySaver
from pydantic import BaseModel, Field



def test_culture_agent():
    """tests the whole agent system also checks if final summary is not empty and is of type str"""
    checkpointer = MemorySaver()
    graph  = build_culture_agent()
    compile_graph = graph.compile(checkpointer=checkpointer)
    inputs = {
    "messages": [
        {
            "role": "user", 
            "content": "Use this documents/china_test_small.txt to get information about china"
        }
        ]
    }
    config = {"configurable": {"thread_id": "1"}}

    result = compile_graph.invoke(inputs,config)

    assert len(result["final_summary"]) !=0

    assert isinstance(result["final_summary"],str)

