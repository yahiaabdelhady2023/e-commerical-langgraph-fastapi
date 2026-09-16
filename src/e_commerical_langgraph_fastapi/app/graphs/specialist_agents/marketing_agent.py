
import io
import json
import operator

from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langgraph.graph import END, START, StateGraph
from PIL import Image
from pydantic import BaseModel, Field
from typing_extensions import Annotated, Literal, TypedDict

load_dotenv()

MARKETING_LLM = init_chat_model(model="gemini-3.1-flash-lite", model_provider="google_genai")

####################################################################
#              1. MARKETING STATES
####################################################################


class MarketingState(TypedDict):
    """State carried through the product marketing workflow."""

    top_candidates: list[str]
    articles_summary: str
    culture_summary: str
    top_candidates_dict: list[dict]
    current_candidate_dict: dict
    marketing_scripts: Annotated[list[str], operator.add]
    work_status: Literal["inprogress", "done"]


####################################################################
#              2. VALIDATION MODELS
####################################################################


class MarketingScript(BaseModel):
    """Generate a general marketing script for one selected product."""

    general_script: str = Field(
        description=(
            "Use the culture summary, articles summary, and current product to generate "
            "a general product marketing script. Connect the product to the culture and "
            "current trends, keep it platform-independent, and include its price, "
            "description, and category."
        )
    )


####################################################################
#              3. PROCESSOR NODES
####################################################################


def marketing_manager_classifer(state: MarketingState):
    """Select the next product to process or finish the workflow."""
    marketing_scripts = state.get("marketing_scripts", [])
    if len(marketing_scripts) >= len(state["top_candidates"]):
        return {"work_status": "done"}

    top_candidates_dict = state.get("top_candidates_dict", [])
    current_candidate_dict = top_candidates_dict[0] if top_candidates_dict else {}

    return {
        "work_status": "inprogress",
        "current_candidate_dict": current_candidate_dict,
        "top_candidates_dict": top_candidates_dict[1:],
    }


def marketing_manager_router(state: MarketingState):
    """Route to script generation while products remain, otherwise finish."""
    return state["work_status"]


def fetch_target_products(state: MarketingState):
    """Load the full records for the selected product names."""
    with open("products.json", "r", encoding="utf-8") as file:
        product_catalog = json.load(file)

    top_candidates_dict = [
        product for product in product_catalog
        if product.get("name") in state["top_candidates"]
    ]
    return {
        "top_candidates_dict": top_candidates_dict,
        "marketing_scripts": [],
    }


def create_general_marketing_script(state: MarketingState):
    """Generate one marketing script for the current product."""
    message = [
        {
            "role": "system",
            "content": "Create a concise, persuasive, platform-independent product marketing script.",
        },
        {
            "role": "user",
            "content": (
                f"Current product:\n{state['current_candidate_dict']}\n\n"
                f"Culture summary:\n{state['culture_summary']}\n\n"
                f"Articles summary:\n{state['articles_summary']}"
            ),
        },
    ]
    marketing_llm = MARKETING_LLM.with_structured_output(MarketingScript)
    result = marketing_llm.invoke(message)
    return {"marketing_scripts": [result.general_script]}


####################################################################
#              4. MARKETING GRAPH CONSTRUCTION
####################################################################


marketing_graph = StateGraph(MarketingState)
marketing_graph.add_node("fetch_target_products", fetch_target_products)
marketing_graph.add_node("create_general_marketing_script", create_general_marketing_script)
marketing_graph.add_node("marketing_manager_classifer", marketing_manager_classifer)
marketing_graph.add_edge(START, "fetch_target_products")
marketing_graph.add_edge("fetch_target_products", "marketing_manager_classifer")
marketing_graph.add_conditional_edges(
    "marketing_manager_classifer",
    marketing_manager_router,
    {"inprogress": "create_general_marketing_script", "done": END},
)
marketing_graph.add_edge("create_general_marketing_script", "marketing_manager_classifer")
compiled_marketing_graph = marketing_graph.compile()


####################################################################
#              5. IMPORT BUILD
####################################################################


def build_marketing_agent():
    """Build the uncompiled marketing graph."""
    marketing_graph = StateGraph(MarketingState)
    marketing_graph.add_node("fetch_target_products", fetch_target_products)
    marketing_graph.add_node("create_general_marketing_script", create_general_marketing_script)
    marketing_graph.add_node("marketing_manager_classifer", marketing_manager_classifer)
    marketing_graph.add_edge(START, "fetch_target_products")
    marketing_graph.add_edge("fetch_target_products", "marketing_manager_classifer")
    marketing_graph.add_conditional_edges(
        "marketing_manager_classifer",
        marketing_manager_router,
        {"inprogress": "create_general_marketing_script", "done": END},
    )
    marketing_graph.add_edge("create_general_marketing_script", "marketing_manager_classifer")
    return marketing_graph


####################################################################
#              6. SAVING GRAPH IMAGES
####################################################################


def save_marketing_agent_graph_png():
    """Save a PNG diagram for the marketing graph."""
    graph_bytes = io.BytesIO(compiled_marketing_graph.get_graph().draw_mermaid_png())
    with Image.open(graph_bytes) as image:
        image.save("marketing_agent_graph.png")