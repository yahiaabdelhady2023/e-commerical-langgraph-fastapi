from langgraph.checkpoint.memory import MemorySaver

from app.graphs.specialist_agents.article_synthesizer import build_article_synthesizer


def test_article_synthesizer():
    """Ensure the article synthesizer produces a non-empty final summary."""
    checkpointer = MemorySaver()
    graph = build_article_synthesizer()
    compile_graph = graph.compile(checkpointer=checkpointer)
    inputs = {
        "messages": [
            {
                "role": "user",
                "content": "Use this documents/china_test_small.txt to get information about china",
            }
        ]
    }
    config = {"configurable": {"thread_id": "1"}}

    result = compile_graph.invoke(inputs, config)

    assert len(result["final_summary"]) != 0
    assert isinstance(result["final_summary"], str)

