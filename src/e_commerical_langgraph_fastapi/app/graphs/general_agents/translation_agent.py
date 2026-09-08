import operator
from typing import Any, Literal
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langgraph.graph import END, START, StateGraph
from langgraph.types import Send
from pydantic import BaseModel, Field
from typing_extensions import Annotated, TypedDict
import io
from PIL import Image
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
#              1. TRANSLATION STATES
####################################################################

def take_last(left: str, right: str) -> str:
    return right or left


class TranslationState(TypedDict):
    target_language: Annotated[str, take_last]
    string_documents: list[str]
    documents: list[Document]
    splitted_documents: list[str]
    translated_documents_list: Annotated[list[Document], operator.add]
    final_translated_document: str

class TranslationWorkerState(TypedDict):
    target_language: str
    current_document_language: str
    current_clean_document: str
    current_translated_document: str
    critique_feedback: str
    translated_documents_list: Annotated[list[Document], operator.add]


class TranslationProcessingSchema(BaseModel):
    """Detects the source language of the current document."""

    current_document_language: str = Field(
        description="Write only the name of the document language."
    )

class TranslationOutputSchema(BaseModel):
    """Contains the translated document."""

    current_translated_document: str = Field(
        description="Translate the current document to the target language."
    )

class TranslationFeedbackSchema(BaseModel):
    """Contains feedback about translation accuracy."""

    critique_feedback: str = Field(
        description="Critique the translation and provide feedback if it is inaccurate."
    )

class TranslationImproveSchema(BaseModel):
    """Contains the improved translated document."""

    improved_translation: str = Field(
        description="Return only the improved translated document."
    )

class FinalTranslationSchema(BaseModel):
    """returns the final translated document"""
    final_translated_document: str = Field(
        description="Return the final translated document"
    )


####################################################################
#              3. ROUTER NODES
####################################################################


def translation_task_splitter_router(state: TranslationState):
    """Create a translation subgraph task for each split document."""
    target_language = state["target_language"]
    return [
        Send(
            "translation_subgraph",
            {
                "current_clean_document": current_clean_document,
                "target_language": target_language,
            },
        )
        for current_clean_document in state["splitted_documents"]
    ]

def check_language_router(state: TranslationWorkerState):
    if state["current_document_language"] == state["target_language"]:
        return "yes"
    return "no"

####################################################################
#              4. PROCESSOR NODES
####################################################################

def string_to_documents(state: dict[str, Any]):
    """Convert string documents to LangChain Document objects."""
    documents = [
        Document(page_content=string_document)
        for string_document in state["string_documents"]
    ]
    return {"documents": documents}

def split_documents(state: dict[str, Any]):
    """Split documents into chunks for translation worker nodes."""
    return {"splitted_documents": [doc.page_content for doc in text_splitter.split_documents(state["documents"])]}


def check_target_language(state: TranslationWorkerState):
    """Detect whether the document already uses the requested language."""
    current_clean_document = state["current_clean_document"]
    lang_llm = general_llm.with_structured_output(TranslationProcessingSchema)
    
    msg = [{"role": "user", "content": current_clean_document}]
    result = lang_llm.invoke(msg)
    return {"current_document_language": result.current_document_language}

def translate_document(state: TranslationWorkerState):
    """Translate one document to the requested target language."""
    current_clean_document = state["current_clean_document"]
    target_language =  state["target_language"]
    lang_llm = general_llm.with_structured_output(TranslationOutputSchema)
    
    msg = [
        {
            "role": "system",
            "content": f"Translate the document to {target_language} and return a Document.",
        },
        {"role": "user", "content": current_clean_document},
    ]
    result = lang_llm.invoke(msg)
    return {"current_translated_document": result.current_translated_document}

def critique_translation(state: TranslationWorkerState):
    """Compare the source and translation and provide accuracy feedback."""
    current_translated_document = state["current_translated_document"]
    current_clean_document = state["current_clean_document"]
    lang_llm = general_llm.with_structured_output(TranslationFeedbackSchema)
    
    msg = [{
        "role": "user",
        "content": (
            "Original document: "
            + current_clean_document
            + "\nTranslated document: "
            + current_translated_document
        ),
    }]
    result = lang_llm.invoke(msg)
    return {"critique_feedback": result.critique_feedback}

def improve_translation(state: TranslationWorkerState):
    """Improve the translation using the critique feedback."""
    current_clean_document = state["current_clean_document"]
    current_translated_document = state["current_translated_document"]
    critique_feedback = state["critique_feedback"]
    lang_llm = general_llm.with_structured_output(TranslationImproveSchema)
    msg = [
        {
            "role": "user",
            "content": (
                "Original document: "
                + current_clean_document
                + "\nTranslated document: "
                + current_translated_document
                + "\nFeedback: "
                + critique_feedback
                + "\nReturn only the improved translated document."
            ),
        }
    ]
    result = lang_llm.invoke(msg)
    return {"translated_documents_list": [result.improved_translation]}

def aggregate_translations(state: TranslationState):
    """Combine translated document chunks into one complete document."""
    translated_documents_list = state["translated_documents_list"]
    system_prompt = """
    You are an expert document reconstruction and localization assistant. Your sole task is to take an ordered sequence of translated document segments and merge them into a single, cohesive, full-length document.

    CRITICAL INSTRUCTIONS:
    1. DO NOT summarize, condense, or omit any content. This is a full document translation reconstruction, not a summary.
    2. Maintain strict fidelity to the original meaning, tone, formatting, and structural intent of the source segments.
    3. Ensure smooth, natural transitions and narrative flow between the text where the segment boundaries met, making the final output read as if the entire document was translated flawlessly in a single pass.
    4. Deliver only the final, fully combined translation. Do not include any introductory text, explanations, or meta-commentary.

    """
    msg = [
        {"role": "system", "content": system_prompt},
        {
            "role": "user",
            "content": [document for document in translated_documents_list],
        },
    ]
    formatted_llm = general_llm.with_structured_output(FinalTranslationSchema)
    result = formatted_llm.invoke(msg)
    return {"final_translated_document": result.final_translated_document}

####################################################################
#              5. TRANSLATION SUBGRAPH CONSTRUCTION
####################################################################


translation_subgraph = StateGraph(TranslationWorkerState)
translation_subgraph.add_node("check_target_language", check_target_language)
translation_subgraph.add_node("translate_document", translate_document)
translation_subgraph.add_node("critique_translation", critique_translation)
translation_subgraph.add_node("improve_translation", improve_translation)
translation_subgraph.add_edge(START, "check_target_language")
translation_subgraph.add_conditional_edges(
    "check_target_language",
    check_language_router,
    {"yes": END, "no": "translate_document"},
)
translation_subgraph.add_edge("translate_document", "critique_translation")
translation_subgraph.add_edge("critique_translation", "improve_translation")
translation_subgraph.add_edge("improve_translation", END)
translation_subgraph_compiled = translation_subgraph.compile()

####################################################################
#              6. PARENT TRANSLATION GRAPH CONSTRUCTION
####################################################################


translation_parentgraph = StateGraph(TranslationState)
translation_parentgraph.add_node("string_to_documents", string_to_documents)
translation_parentgraph.add_node("split_documents", split_documents)
translation_parentgraph.add_node("translation_subgraph", translation_subgraph_compiled)
translation_parentgraph.add_node("aggregate_translations", aggregate_translations)
translation_parentgraph.add_edge(START, "string_to_documents")
translation_parentgraph.add_edge("string_to_documents", "split_documents")
translation_parentgraph.add_conditional_edges(
    "split_documents",
    translation_task_splitter_router,
    ["translation_subgraph"],
)
translation_parentgraph.add_edge("translation_subgraph", "aggregate_translations")
translation_parentgraph.add_edge("aggregate_translations", END)
translation_parentgraph_compiled = translation_parentgraph.compile()

####################################################################
#              7. IMPORT BUILD
####################################################################

def build_translation_agent():
    """Build the uncompiled parent translation graph."""
    translation_parentgraph = StateGraph(TranslationState)
    translation_parentgraph.add_node("string_to_documents", string_to_documents)
    translation_parentgraph.add_node("split_documents", split_documents)
    translation_parentgraph.add_node("translation_subgraph", translation_subgraph_compiled)
    translation_parentgraph.add_node("aggregate_translations", aggregate_translations)
    translation_parentgraph.add_edge(START, "string_to_documents")
    translation_parentgraph.add_edge("string_to_documents", "split_documents")
    translation_parentgraph.add_conditional_edges(
        "split_documents",
        translation_task_splitter_router,
        ["translation_subgraph"],
    )
    translation_parentgraph.add_edge("translation_subgraph", "aggregate_translations")
    translation_parentgraph.add_edge("aggregate_translations", END)
    return translation_parentgraph

def build_translation_subgraph_agent():
    """Build the uncompiled translation worker graph."""
    translation_subgraph = StateGraph(TranslationWorkerState)
    translation_subgraph.add_node("check_target_language", check_target_language)
    translation_subgraph.add_node("translate_document", translate_document)
    translation_subgraph.add_node("critique_translation", critique_translation)
    translation_subgraph.add_node("improve_translation", improve_translation)
    translation_subgraph.add_edge(START, "check_target_language")
    translation_subgraph.add_conditional_edges(
        "check_target_language",
        check_language_router,
        {"yes": END, "no": "translate_document"},
    )
    translation_subgraph.add_edge("translate_document", "critique_translation")
    translation_subgraph.add_edge("critique_translation", "improve_translation")
    translation_subgraph.add_edge("improve_translation", END)
    return translation_subgraph

####################################################################
#              8. SAVING GRAPH IMAGES
####################################################################

def save_translation_agent_png():
    """Save PNG diagrams for the parent and worker translation graphs."""
    graph_bytes = io.BytesIO(
        translation_parentgraph_compiled.get_graph().draw_mermaid_png()
    )
    with Image.open(graph_bytes) as image:
        image.save("parent_translation_graph.png")

    graph_bytes = io.BytesIO(
        translation_subgraph_compiled.get_graph().draw_mermaid_png()
    )
    with Image.open(graph_bytes) as image:
        image.save("worker_translation_graph.png")