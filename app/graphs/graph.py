from langgraph.graph import StateGraph, START, END
from typing_extensions import TypedDict, List, Literal
from typing import Optional, Annotated
import operator
from langchain.chat_models import init_chat_model
from dotenv import load_dotenv
from general_agents.resources_agent import build_resources_agent
from PIL import Image
import io

load_dotenv()


inputs = {
    "messages": [
        {
            "role": "user", 
            "content": "Use this url to extract http://books.toscrape.com/ and from the following api   https://api.escuelajs.co/api/v1/products"
        }
    ]
}



resource_agent = build_resources_agent()
result = resource_agent.invoke(inputs)


# with Image.open(io.BytesIO(resource_agent.get_graph().draw_mermaid_png())) as img:
#     img.show()
