import pytest
from app.graphs.general_agents.summary_agent import build_summary_agent
from langgraph.checkpoint.memory import MemorySaver


def test_summary_agent() -> None:
    """ensuring summary agent works and 
    makes sure final summary is of string type instead of document type"""

    string_docs="""
    Python is a versatile, general-purpose programming language designed with an 
    emphasis on code readability. Created by Guido van Rossum and first released 
    in 1991, it supports multiple paradigms—including object-oriented, procedural, 
    and functional programming. Its rich standard library and massive third-party 
    ecosystem make it a standard tool for machine learning, data engineering, 
    web frameworks, and rapid prototyping.

    """

    checkpointer = MemorySaver()
    graph  = build_summary_agent()
    compile_graph = graph.compile(checkpointer=checkpointer)
    config = {"configurable": {"thread_id": "1"}}
    inputs = {
        "string_documents": [string_docs],
        "clean_required": "yes",
    }
    result = compile_graph.invoke(inputs, config)
    assert len(result["final_summary"]) != 0
    assert isinstance(result["final_summary"],str)