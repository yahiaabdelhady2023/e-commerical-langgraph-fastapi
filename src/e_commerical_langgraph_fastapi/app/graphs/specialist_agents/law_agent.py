import io
import operator
from typing import Any

from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langgraph.graph import END, START, StateGraph
from langgraph.types import Send
from PIL import Image
from pydantic import BaseModel, Field
from typing_extensions import Annotated, Literal, TypedDict

from e_commerical_langgraph_fastapi.app.graphs.general_agents.resources_agent import (
    build_resources_agent,
)
from e_commerical_langgraph_fastapi.app.graphs.general_agents.translation_agent import (
    build_translation_agent,
)
from e_commerical_langgraph_fastapi.app.graphs.custom_functions.utility_functions import (
    pythonic_text_clean,
)

load_dotenv()

LAW_LLM = init_chat_model(model="gemini-3.1-flash-lite", model_provider="google_genai")
TEXT_SPLITTER = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
    chunk_size=5000,
    chunk_overlap=100,
)

####################################################################
#              1. LAW STATES
####################################################################


class LawChildState(TypedDict):
    """State carried through a single legal compliance review."""

    script_index: int
    script_content: str
    legal_document_section: str
    feedback_list: Annotated[list[dict[str, Any]], operator.add]


class OverallLawState(TypedDict, total=False):
    """State carried through the legal review workflow."""

    messages: list[dict]
    string_documents_list: list[str]
    documents: list[Document]
    legal_document_sections: list[Document]
    feedback_list: Annotated[list[dict[str, Any]], operator.add]
    script_list: list[str]
    current_script: str
    final_script_list: list[str]
    work_status: Literal["inprogress", "done"]


####################################################################
#              2. VALIDATION MODELS
####################################################################


class LawSchemaFeedback(BaseModel):
    """Check whether a script conflicts with a legal section."""

    feedback: str = Field(
        description=(
            "Review the script against the legal section and describe only the concrete "
            "compliance violations or missing legal requirements."
        )
    )


class LawSchemaImproved(BaseModel):
    """Rewrite the script to satisfy the legal feedback."""

    improved_script: str = Field(
        description=(
            "Use the current script and feedback to produce a legally compliant version "
            "that keeps the original intent while fixing every issue."
        )
    )


####################################################################
#              3. PROCESSOR NODES
####################################################################


def compliance_review(state: LawChildState):
    """Check a script against one legal document section."""
    reviewer_llm = LAW_LLM.with_structured_output(LawSchemaFeedback)

    message = [
        {
            "role": "system",
            "content": (
                "You are a legal compliance reviewer. Judge the script against the provided "
                "legal section and mention only concrete violations or missing obligations."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Current script:\n{state['script_content']}\n\n"
                f"Legal document section:\n{state['legal_document_section']}"
            ),
        },
    ]
    result = reviewer_llm.invoke(message)
    return {
        "feedback_list": [
            {"script_index": state["script_index"], "feedback": result.feedback}
        ]
    }


def law_resource_node(state: OverallLawState):
    """Fetch the legal source documents from the current state or user request."""
    if state.get("string_documents_list"):
        return {"string_documents_list": state["string_documents_list"]}

    messages = state.get("messages", [])
    if not messages:
        raise ValueError(
            "Law resource node requires either a 'messages' input or pre-populated "
            "'string_documents_list' in the workflow state."
        )

    last_message = messages[-1]
    user_content = last_message.get("content") if isinstance(last_message, dict) else getattr(last_message, "content", "")

    resource_parentgraph = build_resources_agent()
    result = resource_parentgraph.compile().invoke({"messages": [{"role": "user", "content": user_content}]})

    data_list = result.get("data_list", [])
    string_documents = [
        str(item) if not hasattr(item, "content") else str(item.content)
        for item in data_list
    ]
    return {"string_documents_list": string_documents}


def law_clean_node(state: OverallLawState):
    """Normalize the raw legal text before translation and splitting."""
    cleaned_documents = [pythonic_text_clean(doc) for doc in state["string_documents_list"]]
    return {"documents": [Document(page_content=doc) for doc in cleaned_documents]}


def law_translation_node(state: OverallLawState):
    """Translate the cleaned legal text to English for review."""
    translation_parentgraph = build_translation_agent()
    result = translation_parentgraph.compile().invoke(
        {
            "string_documents": state["string_documents_list"],
            "target_language": "english",
        }
    )
    translated_document = result.get("final_translated_document", "")
    return {"string_documents_list": [translated_document]}


def law_split_documents_node(state: OverallLawState):
    """Split the translated legal text into reviewable document sections."""
    if not state.get("documents"):
        return {"legal_document_sections": [Document(page_content=text) for text in state["string_documents_list"]]}

    split_sections = TEXT_SPLITTER.split_documents(state["documents"])
    return {"legal_document_sections": split_sections}


def law_documents_splitter_router(state: OverallLawState):
    """Create a compliance review subtask for each script and legal section."""
    script_list = state.get("script_list") or [state["current_script"]]
    return [
        Send(
            "law_subgraph",
            {
                "script_index": script_index,
                "script_content": current_script,
                "legal_document_section": legal_document_section.page_content,
            },
        )
        for script_index, current_script in enumerate(script_list)
        for legal_document_section in state["legal_document_sections"]
    ]


def adjust_script(state: OverallLawState):
    """Rewrite each script using only its own collected legal feedback."""
    script_list = state.get("script_list") or [state.get("current_script", "")]
    feedback_list = state.get("feedback_list", [])

    final_script_list = []
    for script_index, current_script in enumerate(script_list):
        script_feedback = [
            item["feedback"]
            for item in feedback_list
            if item["script_index"] == script_index
        ]
        if not script_feedback:
            final_script_list.append(current_script)
            continue

        adjust_llm = LAW_LLM.with_structured_output(LawSchemaImproved)
        message = [
            {
                "role": "system",
                "content": "Improve the script to satisfy the legal feedback while preserving the original intent.",
            },
            {
                "role": "user",
                "content": (
                    f"Current script:\n{current_script}\n\n"
                    f"Feedback:\n{chr(10).join(script_feedback)}"
                ),
            },
        ]
        result = adjust_llm.invoke(message)
        final_script_list.append(result.improved_script)

    return {"final_script_list": final_script_list, "work_status": "done"}


####################################################################
#              4. LAW SUBGRAPH CONSTRUCTION
####################################################################


law_subgraph = StateGraph(LawChildState)
law_subgraph.add_node("compliance_review", compliance_review)
law_subgraph.add_edge(START, "compliance_review")
law_subgraph.add_edge("compliance_review", END)
law_subgraph_compiled = law_subgraph.compile()


####################################################################
#              5. LAW GRAPH CONSTRUCTION
####################################################################


law_agent = StateGraph(OverallLawState)
law_agent.add_node("law_resource_node", law_resource_node)
law_agent.add_node("law_clean_node", law_clean_node)
law_agent.add_node("law_translation_node", law_translation_node)
law_agent.add_node("law_split_documents_node", law_split_documents_node)
law_agent.add_node("law_subgraph", law_subgraph_compiled)
law_agent.add_node("adjust_script", adjust_script)
law_agent.add_edge(START, "law_resource_node")
law_agent.add_edge("law_resource_node", "law_clean_node")
law_agent.add_edge("law_clean_node", "law_translation_node")
law_agent.add_edge("law_translation_node", "law_split_documents_node")
law_agent.add_conditional_edges(
    "law_split_documents_node",
    law_documents_splitter_router,
    ["law_subgraph"],
)
law_agent.add_edge("law_subgraph", "adjust_script")
law_agent.add_edge("adjust_script", END)
law_agent_compiled = law_agent.compile()


####################################################################
#              6. IMPORT BUILD
####################################################################


def build_law_agent():
    """Build the uncompiled law compliance graph."""
    law_agent = StateGraph(OverallLawState)
    law_agent.add_node("law_resource_node", law_resource_node)
    law_agent.add_node("law_clean_node", law_clean_node)
    law_agent.add_node("law_translation_node", law_translation_node)
    law_agent.add_node("law_split_documents_node", law_split_documents_node)
    law_agent.add_node("law_subgraph", law_subgraph_compiled)
    law_agent.add_node("adjust_script", adjust_script)
    law_agent.add_edge(START, "law_resource_node")
    law_agent.add_edge("law_resource_node", "law_clean_node")
    law_agent.add_edge("law_clean_node", "law_translation_node")
    law_agent.add_edge("law_translation_node", "law_split_documents_node")
    law_agent.add_conditional_edges(
        "law_split_documents_node",
        law_documents_splitter_router,
        ["law_subgraph"],
    )
    law_agent.add_edge("law_subgraph", "adjust_script")
    law_agent.add_edge("adjust_script", END)
    return law_agent


####################################################################
#              7. SAVING GRAPH IMAGES
####################################################################


def save_law_agent_graph_png():
    """Save a PNG diagram for the law graph."""
    graph_bytes = io.BytesIO(law_agent_compiled.get_graph().draw_mermaid_png())
    with Image.open(graph_bytes) as image:
        image.save("law_agent_graph.png")
