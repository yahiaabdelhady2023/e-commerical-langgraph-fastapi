from langgraph.graph import StateGraph, START, END
from typing_extensions import TypedDict, List, Literal
from typing import Optional, Annotated
import operator
from langchain.chat_models import init_chat_model
from dotenv import load_dotenv
import sys

for x in sys.path:
    print(x)

from e_commerical_langgraph_fastapi.app.graphs.general_agents.resources_agent import build_resources_agent
from e_commerical_langgraph_fastapi.app.graphs.general_agents.summary_agent import build_summary_agent
from e_commerical_langgraph_fastapi.app.graphs.general_agents.translation_agent import build_translation_agent
from PIL import Image
import io

load_dotenv()


# inputs = {
#     "messages": [
#         {
#             "role": "user", 
#             "content": "Use this url to extract http://books.toscrape.com/ and from the following api   https://api.escuelajs.co/api/v1/products"
#         }
#     ]
# }




# resource_agent = build_resources_agent()
# result = resource_agent.invoke(inputs)


# with open("documents/llm_test_document.txt","r") as f:
#     text = f.read()

# string_docs=[text]
# summary_agent = build_summary_agent()
# summary_agent = summary_agent.compile()
# inputs = {"string_documents":string_docs,"clean_required":"yes"}
# result = summary_agent.invoke(inputs)

# print(result["final_summary"])

# with Image.open(io.BytesIO(resource_agent.get_graph().draw_mermaid_png())) as img:
#     img.show()


with open("documents/french_translation.txt","r",encoding='utf-8') as f:
    text = f.read()

string_docs=[text]

translation_graph = build_translation_agent()
translation_graph = translation_graph.compile()

inputs = {"string_documents":string_docs,"target_language":"english"}
result = translation_graph.invoke(
inputs
)

print(result["final_translated_document"])