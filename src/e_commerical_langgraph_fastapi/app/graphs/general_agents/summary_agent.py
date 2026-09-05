import operator
from typing import Any, Literal
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.types import Send
from pydantic import BaseModel, Field
from typing_extensions import Annotated, TypedDict
import io
from PIL import Image
from app.graphs.custom_functions.utility_functions import pythonic_text_clean

CHUNK_SIZE = 5000
CHUNK_OVERLAP_SIZE = 100
FAIL = "failed"
SUCCESS = "success"

load_dotenv()
text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
    chunk_size=CHUNK_SIZE,
    chunk_overlap=CHUNK_OVERLAP_SIZE,
)
general_llm = init_chat_model(model="gemini-3.1-flash-lite", model_provider="google_genai")

####################################################################
#              1. SUMMARY STATES
####################################################################

class SummaryState(TypedDict):
    string_documents: list[str]
    documents: list[Document]
    splitted_documents: list[Document]
    error_messages: Annotated[list, add_messages]
    mini_summaries: Annotated[list[Document], operator.add]
    final_summary: str
    clean_required: Literal["yes", "no"]

class SummaryWorkerState(TypedDict):
    current_clean_document: Document
    mini_summaries: Annotated[list[Document], operator.add]
    final_summary: str

class SummaryProcessingSchema(BaseModel):
    """Changes throughout summary worker nodes."""

    current_mini_summary: Document = Field(
        description="Write a short summary of the current document and return only a Document."
    )

class SummaryOutputSchema(BaseModel):
    """Combines the worker summaries into one final summary."""

    final_summary: Document = Field(
        description="Write a cohesive final summary using all mini-summaries."
    )

class SummaryPurgeSchema(BaseModel):
    """Removes irrelevant material without summarising the document."""

    cleaned_document: str = Field(
        description=(
            "Remove headers, footers, page numbers, legal disclaimers, copyright notices, "
            "terms of service, privacy policies, broken markdown, and duplicated text. "
            "Keep all other original text and do not summarise it."
        )
    )

####################################################################
#              3. CLASSIFIER NODES
####################################################################

def is_cleaning_required_classifer(state: SummaryState):
    """Check whether documents require cleaning before processing."""
    return {"clean_required": state["clean_required"]}

def summary_task_splitter_router(state: SummaryState):
    """Create a summary subgraph task for each split document."""
    return [
        Send("summary_subgraph", {"current_clean_document": current_clean_document})
        for current_clean_document in state["splitted_documents"]
    ]

def clean_required_router(state: SummaryState):
    return state["clean_required"]

####################################################################
#              4. PROCESSOR NODES
####################################################################

def string_to_documents(state: dict[str, Any]):
    """Convert string documents to LangChain Document objects."""
    documents = [Document(page_content=string_doc) for string_doc in state["string_documents"]]
    return {"documents": documents}

def clean_string_documents(state: dict[str, Any]):
    """Clean binary data, images, whitespace, markup, and disclaimers."""
    cleaned_documents = [
        pythonic_text_clean(string_doc)
        for string_doc in state["string_documents"]
    ]
    return {"string_documents": cleaned_documents}

def purge_irrelevant_information(state: dict[str, Any]):
    """Remove irrelevant document material using the structured LLM output."""
    summary_llm = general_llm.with_structured_output(SummaryPurgeSchema)
    cleaned_documents = []
    for string_doc in state["string_documents"]:
        msg = [
            {"role": "system", "content": "Clean the document without summarising it."},
            {"role": "user", "content": string_doc},
        ]
        result = summary_llm.invoke(msg)
        cleaned_documents.append(result.cleaned_document)
    return {"string_documents": cleaned_documents}

def split_documents(state: dict[str, Any]):
    """Split documents into chunks that can be processed by worker nodes."""
    return {"splitted_documents": text_splitter.split_documents(state["documents"])}

def summarise_document(state: SummaryWorkerState):
    """Summarise one document as a mini-summary."""
    summary_llm = general_llm.with_structured_output(SummaryProcessingSchema)
    msg = [
        {"role": "system", "content": "Given a document, summarise it."},
        {"role": "user", "content": state["current_clean_document"].page_content},
    ]
    result = summary_llm.invoke(msg)
    return {"mini_summaries": [result.current_mini_summary]}

def aggregrate_summaries(state: SummaryState):
    """Combine all mini-summaries into one cohesive final summary."""
    summary_llm = general_llm.with_structured_output(SummaryOutputSchema)
    msg = [
        {"role": "system", "content": "Combine these summaries into one cohesive summary."},
        {"role": "user", "content": [summary.page_content for summary in state["mini_summaries"]]},
    ]
    result = summary_llm.invoke(msg)
    return {"final_summary": result.final_summary}

####################################################################
#              5. SUMMARY SUBGRAPH CONSTRUCTION
####################################################################

summary_subgraph = StateGraph(SummaryWorkerState)
summary_subgraph.add_node("summarise_document", summarise_document)
summary_subgraph.add_edge(START, "summarise_document")
summary_subgraph.add_edge("summarise_document", END)
compiled_summary_subgraph = summary_subgraph.compile()

####################################################################
#              6. PARENT SUMMARY GRAPH CONSTRUCTION
####################################################################

summary_parentgraph = StateGraph(SummaryState)
summary_parentgraph.add_node("is_cleaning_required_classifer", is_cleaning_required_classifer)
summary_parentgraph.add_node("clean_string_documents", clean_string_documents)
# summary_parentgraph.add_node("purge_irrelevant_information", purge_irrelevant_information)
summary_parentgraph.add_node("string_to_documents", string_to_documents)
summary_parentgraph.add_node("split_documents", split_documents)
summary_parentgraph.add_node("summary_subgraph", compiled_summary_subgraph)
summary_parentgraph.add_node("aggregrate_summaries", aggregrate_summaries)
summary_parentgraph.add_edge(START, "is_cleaning_required_classifer")
summary_parentgraph.add_conditional_edges(
    "is_cleaning_required_classifer",
    clean_required_router,
    {"yes": "clean_string_documents", "no": "string_to_documents"},
)
summary_parentgraph.add_edge("clean_string_documents", "string_to_documents")
summary_parentgraph.add_edge("string_to_documents", "split_documents")
summary_parentgraph.add_conditional_edges(
    "split_documents",
    summary_task_splitter_router,
    ["summary_subgraph"],
)
summary_parentgraph.add_edge("summary_subgraph", "aggregrate_summaries")
summary_parentgraph.add_edge("aggregrate_summaries", END)
compiled_summary_parentgraph = summary_parentgraph.compile()

####################################################################
#              7. IMPORT BUILD
####################################################################

def build_summary_agent():
    """Build the uncompiled parent summary graph."""
    summary_parentgraph = StateGraph(SummaryState)
    summary_parentgraph.add_node("is_cleaning_required_classifer", is_cleaning_required_classifer)
    summary_parentgraph.add_node("clean_string_documents", clean_string_documents)
    summary_parentgraph.add_node("purge_irrelevant_information", purge_irrelevant_information)
    summary_parentgraph.add_node("string_to_documents", string_to_documents)
    summary_parentgraph.add_node("split_documents", split_documents)
    summary_parentgraph.add_node("summary_subgraph", compiled_summary_subgraph)
    summary_parentgraph.add_node("aggregrate_summaries", aggregrate_summaries)
    summary_parentgraph.add_edge(START, "is_cleaning_required_classifer")
    summary_parentgraph.add_conditional_edges(
        "is_cleaning_required_classifer",
        clean_required_router,
        {"yes": "clean_string_documents", "no": "string_to_documents"},
    )
    summary_parentgraph.add_edge("clean_string_documents", "purge_irrelevant_information")
    summary_parentgraph.add_edge("purge_irrelevant_information", "string_to_documents")
    summary_parentgraph.add_edge("string_to_documents", "split_documents")
    summary_parentgraph.add_conditional_edges(
        "split_documents",
        summary_task_splitter_router,
        ["summary_subgraph"],
    )
    summary_parentgraph.add_edge("summary_subgraph", "aggregrate_summaries")
    summary_parentgraph.add_edge("aggregrate_summaries", END)
    return summary_parentgraph

def build_summary_subgraph_agent():
    """Build the uncompiled summary worker graph."""
    summary_subgraph = StateGraph(SummaryWorkerState)
    summary_subgraph.add_node("summarise_document", summarise_document)
    summary_subgraph.add_edge(START, "summarise_document")
    summary_subgraph.add_edge("summarise_document", END)
    return summary_subgraph



####################################################################
#              8. Saving Graph Images
####################################################################

graph_bytes = io.BytesIO(compiled_summary_parentgraph.get_graph().draw_mermaid_png())

with Image.open(graph_bytes) as img:
    img.save("parent_summary_graph.png")


graph_bytes = io.BytesIO(compiled_summary_subgraph.get_graph().draw_mermaid_png())

with Image.open(graph_bytes) as img:
    img.save("worker_summary_graph.png")
