import pytest
from app.graphs.general_agents.translation_agent import build_translation_agent
from langgraph.checkpoint.memory import MemorySaver


def test_summary_agent() -> None:
    """ensuring summary agent works and 
    makes sure final summary is of string type instead of document type"""

    string_docs="""
   Chaque matin, la ville s'éveille lentement sous une lumière dorée. 
   Les passants se pressent vers les stations de métro, 
   tandis que l'arôme du café frais s'échappe des terrasses encore calmes.
   Une légère brise d'automne fait tourbillonner quelques feuilles sèches sur le trottoir, rappelant que les saisons changent, 
   mais que le rythme du quotidien, lui, reste immuable.

    """
    checkpointer = MemorySaver()
    graph  = build_translation_agent()
    compile_graph = graph.compile(checkpointer=checkpointer)
    config = {"configurable": {"thread_id": "1"}}
    inputs = {
        "string_documents": [string_docs],
        "target_language": "english",
    }
    result = compile_graph.invoke(inputs, config)
    assert len(result["final_translated_document"]) != 0
    assert isinstance(result["final_translated_document"],str)