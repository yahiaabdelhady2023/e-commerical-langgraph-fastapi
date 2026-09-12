import json
import operator

from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langgraph.graph import END, START, StateGraph
from langgraph.types import Send
from pydantic import BaseModel, Field
from typing_extensions import Annotated
import io
from PIL import Image
from e_commerical_langgraph_fastapi.app.graphs.general_agents.resources_agent import (
    ResourceState,
    ResourceWorkerState,
    build_resources_agent,
)

load_dotenv()

FAIL = "failed"
SUCCESS = "success"

general_llm = init_chat_model(model="gemini-3.1-flash-lite", model_provider="google_genai")

####################################################################
#              1. PRODUCT STATES
####################################################################

class Product(BaseModel):
    name: str
    price: float
    description: str
    category: str | None = Field(
        description=(
            "The product category extracted from the webpage. If not explicitly described, "
            "generate a suitable general category name."
        )
    )
    rating: float | None = Field(
        description=(
            "Extract the rating of the product only if it exists in the webpage content. "
            "Do not invent a rating."
        )
    )
    source_address: str | None = Field(
        description="The URL or physical address where this content was extracted."
    )

class ProductState(ResourceState):
    products_list: Annotated[list[Product], operator.add]

class ProductWorkerState(ResourceWorkerState):
    product_resource_content: str
    products_list: Annotated[list[Product], operator.add]

####################################################################
#              2. VALIDATION MODELS
####################################################################

class ProductCatalogSchema(BaseModel):
    products: list[Product] = Field(description="A list of e-commerce products.")

####################################################################
#              3. ROUTER NODES
####################################################################

def product_task_splitter_router(state: ProductState):
    """Create a product subgraph task for each product resource item."""
    return [
        Send("product_subgraph", {"product_resource_content": product_resource_content})
        for product_resource_content in state["data_list"]
    ]

####################################################################
#              4. PROCESSOR NODES
####################################################################

def extract_products(state: ProductWorkerState):
    """Extract structured product data from a single resource payload."""
    product_resource_content = state["product_resource_content"]
    content = (
        product_resource_content.content
        if hasattr(product_resource_content, "content")
        else str(product_resource_content)
    )

    product_llm = general_llm.with_structured_output(ProductCatalogSchema)
    msg = [{"role": "user", "content": content}]
    result = product_llm.invoke(msg)
    product_list = result.products
    product_list_python = [product.model_dump() for product in product_list]

    with open("products.json", "w", encoding="utf-8") as file:
        json.dump(product_list_python, file, indent=4)

    return {"products_list": product_list}

####################################################################
#              5. PRODUCT SUBGRAPH CONSTRUCTION
####################################################################

product_subgraph = StateGraph(ProductWorkerState)
product_subgraph.add_node("extract_products", extract_products)
product_subgraph.add_edge(START, "extract_products")
product_subgraph.add_edge("extract_products", END)
compiled_product_subgraph = product_subgraph.compile()

####################################################################
#              6. PRODUCT PARENT GRAPH CONSTRUCTION
####################################################################

resource_parentgraph = build_resources_agent()
compiled_resource_parentgraph = resource_parentgraph.compile()

product_parentgraph = StateGraph(ProductState)
product_parentgraph.add_node("resources_agent", compiled_resource_parentgraph)
product_parentgraph.add_node("product_subgraph", compiled_product_subgraph)
product_parentgraph.add_edge(START, "resources_agent")
product_parentgraph.add_conditional_edges(
    "resources_agent",
    product_task_splitter_router,
    ["product_subgraph"],
)
product_parentgraph.add_edge("product_subgraph", END)
compiled_product_parentgraph = product_parentgraph.compile()

####################################################################
#              7. IMPORT BUILD
####################################################################

def build_product_agent():
    """Build the uncompiled product parent graph."""
    resource_parentgraph = build_resources_agent()
    compiled_resource_parentgraph = resource_parentgraph.compile()
    product_parentgraph = StateGraph(ProductState)
    product_parentgraph.add_node("resources_agent", compiled_resource_parentgraph)
    product_parentgraph.add_node("product_subgraph", compiled_product_subgraph)
    product_parentgraph.add_edge(START, "resources_agent")
    product_parentgraph.add_conditional_edges(
        "resources_agent",
        product_task_splitter_router,
        ["product_subgraph"],
    )
    product_parentgraph.add_edge("product_subgraph", END)
    return product_parentgraph


def build_product_subgraph_agent():
    """Build the uncompiled product worker graph."""
    product_subgraph = StateGraph(ProductWorkerState)
    product_subgraph.add_node("extract_products", extract_products)
    product_subgraph.add_edge(START, "extract_products")
    product_subgraph.add_edge("extract_products", END)
    return product_subgraph


####################################################################
#              8. Saving Graph Images
####################################################################
def save_products_agent_graph_png():
    graph_bytes = io.BytesIO(compiled_product_parentgraph.get_graph().draw_mermaid_png())

    with Image.open(graph_bytes) as img:
        img.save("parent_products_agent_graph.png")
