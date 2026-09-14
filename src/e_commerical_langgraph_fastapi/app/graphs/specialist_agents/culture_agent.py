import operator
import io
from PIL import Image
from langgraph.graph import END, START, StateGraph
from typing_extensions import TypedDict

from e_commerical_langgraph_fastapi.app.graphs.general_agents.resources_agent import (
    ResourceState,
    build_resources_agent,
)
from e_commerical_langgraph_fastapi.app.graphs.general_agents.summary_agent import (
    SummaryState,
    build_summary_agent,
)
from e_commerical_langgraph_fastapi.app.graphs.general_agents.translation_agent import (
    TranslationState,
    build_translation_agent,
)


####################################################################
#              1. CULTURE STATES
####################################################################


class CultureState(ResourceState, TranslationState, SummaryState):
    pass


####################################################################
#              2. PROCESSOR NODES
####################################################################


def prepare_for_translation(state: CultureState):
    """Convert fetched resource content into translation input."""
    return {
        "string_documents": [str(document) for document in state["data_list"]],
        "target_language": "english",
    }


def prepare_for_summarisation(state: CultureState):
    """Convert the translated document into summary input."""
    return {
        "string_documents": [state["final_translated_document"]],
        "clean_required": "yes",
    }


####################################################################
#              3. CULTURE PARENT GRAPH CONSTRUCTION
####################################################################


resource_parentgraph = build_resources_agent()
compiled_resource_parentgraph = resource_parentgraph.compile()

translation_parentgraph = build_translation_agent()
compiled_translation_parentgraph = translation_parentgraph.compile()

summary_parentgraph = build_summary_agent()
compiled_summary_parentgraph = summary_parentgraph.compile()


culture_graph = StateGraph(CultureState)
culture_graph.add_node("resources_agent", compiled_resource_parentgraph)
culture_graph.add_node("prepare_for_translation", prepare_for_translation)
culture_graph.add_node("translation_agent", compiled_translation_parentgraph)
culture_graph.add_node("prepare_for_summarisation", prepare_for_summarisation)
culture_graph.add_node("summary_agent", compiled_summary_parentgraph)
culture_graph.add_edge(START, "resources_agent")
culture_graph.add_edge("resources_agent", "prepare_for_translation")
culture_graph.add_edge("prepare_for_translation", "translation_agent")
culture_graph.add_edge("translation_agent", "prepare_for_summarisation")
culture_graph.add_edge("prepare_for_summarisation", "summary_agent")
culture_graph.add_edge("summary_agent", END)
compiled_culture_graph = culture_graph.compile()


####################################################################
#              4. IMPORT BUILD
####################################################################


def build_culture_agent():
    """Build the uncompiled culture parent graph."""
    resource_parentgraph = build_resources_agent()
    translation_parentgraph = build_translation_agent()
    summary_parentgraph = build_summary_agent()

    culture_graph = StateGraph(CultureState)
    culture_graph.add_node("resources_agent", resource_parentgraph.compile())
    culture_graph.add_node("prepare_for_translation", prepare_for_translation)
    culture_graph.add_node("translation_agent", translation_parentgraph.compile())
    culture_graph.add_node("prepare_for_summarisation", prepare_for_summarisation)
    culture_graph.add_node("summary_agent", summary_parentgraph.compile())
    culture_graph.add_edge(START, "resources_agent")
    culture_graph.add_edge("resources_agent", "prepare_for_translation")
    culture_graph.add_edge("prepare_for_translation", "translation_agent")
    culture_graph.add_edge("translation_agent", "prepare_for_summarisation")
    culture_graph.add_edge("prepare_for_summarisation", "summary_agent")
    culture_graph.add_edge("summary_agent", END)
    return culture_graph


####################################################################
#              5. SAVING GRAPH IMAGES
####################################################################


def save_culture_agent_graph_png():
    """Save a PNG diagram for the culture parent graph."""
    graph_bytes = io.BytesIO(compiled_culture_graph.get_graph().draw_mermaid_png())
    with Image.open(graph_bytes) as image:
        image.save("culture_agent_graph.png")