from types import SimpleNamespace

from langchain_core.documents import Document

from app.graphs.specialist_agents import law_agent as law_agent_module
from app.graphs.specialist_agents.law_agent import (
    adjust_script,
    build_law_agent,
    law_documents_splitter_router,
)


def test_law_agent_builds_graph():
    """The law agent should expose a standard builder and valid graph nodes."""
    graph = build_law_agent()

    assert graph is not None
    node_names = set(graph.nodes)
    assert {"law_resource_node", "law_clean_node", "law_translation_node", "law_split_documents_node", "law_subgraph", "adjust_script"}.issubset(node_names)


def test_adjust_script_keeps_feedback_separate_per_script(monkeypatch):
    """Each script is revised with its own feedback and returned in list order."""

    class FakeAdjustLLM:
        def with_structured_output(self, _schema):
            return self

        def invoke(self, messages):
            return SimpleNamespace(improved_script=f"revised: {messages[1]['content']}")

    monkeypatch.setattr(law_agent_module, "LAW_LLM", FakeAdjustLLM())

    result = adjust_script(
        {
            "script_list": ["first", "second"],
            "feedback_list": [
                {"script_index": 0, "feedback": "first issue"},
                {"script_index": 1, "feedback": "second issue"},
            ],
        }
    )

    assert len(result["final_script_list"]) == 2
    assert "first issue" in result["final_script_list"][0]
    assert "second issue" not in result["final_script_list"][0]
    assert "second issue" in result["final_script_list"][1]
    assert "first issue" not in result["final_script_list"][1]


def test_router_checks_each_script_against_each_legal_section():
    sends = law_documents_splitter_router(
        {
            "script_list": ["first", "second"],
            "legal_document_sections": [
                Document(page_content="section one"),
                Document(page_content="section two"),
            ],
        }
    )

    assert len(sends) == 4
    assert [(send.arg["script_index"], send.arg["legal_document_section"]) for send in sends] == [
        (0, "section one"),
        (0, "section two"),
        (1, "section one"),
        (1, "section two"),
    ]


def test_law_agent_invokes_parallel_reviews_without_state_collision(monkeypatch):
    class FakeLLM:
        def with_structured_output(self, schema):
            class FakeStructuredLLM:
                def invoke(self, messages):
                    if schema is law_agent_module.LawSchemaFeedback:
                        return SimpleNamespace(feedback="Make product claims verifiable.")
                    current_script = messages[1]["content"].split("Current script:\n", 1)[1].split(
                        "\n\nFeedback:", 1
                    )[0]
                    return SimpleNamespace(improved_script=f"Reviewed: {current_script}")

            return FakeStructuredLLM()

    monkeypatch.setattr(law_agent_module, "LAW_LLM", FakeLLM())
    monkeypatch.setattr(
        law_agent_module,
        "law_translation_node",
        lambda state: {"string_documents_list": state["string_documents_list"]},
    )

    result = build_law_agent().compile().invoke(
        {
            "string_documents_list": ["Legal requirements for product advertising."],
            "script_list": ["KumoBrew kettle ad", "HoshiGlow lamp ad"],
        }
    )

    assert result["final_script_list"] == [
        "Reviewed: KumoBrew kettle ad",
        "Reviewed: HoshiGlow lamp ad",
    ]
