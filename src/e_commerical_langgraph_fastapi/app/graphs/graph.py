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
from e_commerical_langgraph_fastapi.app.graphs.specialist_agents.products_agent import build_product_agent
from e_commerical_langgraph_fastapi.app.graphs.specialist_agents.article_synthesizer import build_article_synthesizer
from e_commerical_langgraph_fastapi.app.graphs.specialist_agents.products_classifer_agent import build_product_classifier_agent
from e_commerical_langgraph_fastapi.app.graphs.specialist_agents.marketing_agent import build_marketing_agent

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


# with open("documents/french_translation.txt","r",encoding='utf-8') as f:
#     text = f.read()

# string_docs=[text]

# translation_graph = build_translation_agent()
# translation_graph = translation_graph.compile()

# inputs = {"string_documents":string_docs,"target_language":"english"}
# result = translation_graph.invoke(
# inputs
# )

# print(result["final_translated_document"])


# inputs = {
#     "messages": [
#         {
#             "role": "user", 
#             "content": "extract data from single_product.json and product_intelligence_report_v2.txt" 
#         }
#     ]
# }

# product_graph = build_product_agent()
# product_graph = product_graph.compile()

# result = product_graph.invoke(
# inputs
# )
# print("result is",result)
# print(result["processed_resource_list"])

# article_synthesizer_graph = build_article_synthesizer()
# article_synthesizer_graph_compiled = article_synthesizer_graph.compile()

# inputs = {
#     "messages": [
#         {
#             "role": "user", 
#             "content": "Use this documents/china_test_10k_dataset.txt to get information about china"
#         }
#     ]
# }
# result = article_synthesizer_graph_compiled.invoke(
#     inputs
# )

# print(result)
def main():
    # Japan Culture Summary (Approx. 1,000 characters)
    culture_summary = (
        "Japan's culture is a masterclass in blending ancient traditions with futuristic "
        "innovation. At its core lies the concept of 'Wa' (harmony), which shapes social "
        "interactions, emphasizing community, respect, and politeness over individualism. "
        "Traditional arts like the tea ceremony (Chado), flower arranging (Ikebana), and "
        "classical theater (Noh and Kabuki) remain deeply respected, reflecting Zen Buddhist "
        "philosophies of mindfulness and appreciating impermanence (Wabi-Sabi). Simultaneously, "
        "Japan is a global pop-culture powerhouse. Anime, manga, and gaming are not just "
        "major exports but integral parts of daily life, influencing fashion, art, and language "
        "worldwide. The cuisine, or 'Washoku'—recognized by UNESCO—focuses on seasonal, fresh "
        "ingredients and meticulous presentation, ranging from street food like Takoyaki to elite "
        "Sushi. Shintoism and Buddhism coexist seamlessly, with modern citizens celebrating Shinto "
        "festivals (Matsuri) and visiting shrines for New Year, while adopting Buddhist rituals "
        "for funerals. This unique cultural duality creates a society where high-tech bullet trains "
        "speed past centuries-old wooden temples, and neon-lit skyscrapers stand alongside quiet, "
        "moss-covered stone gardens."
    )

    # # Japan Articles & Tech/Economy Summary (Approx. 1,000 characters)
    articles_summary = (
        "Recent headlines from Japan highlight significant shifts across its economic landscape "
        "and technology sector. Economically, the Bank of Japan continues to navigate a delicate "
        "transition away from its long-standing ultra-loose monetary policy, responding to steady "
        "wage growth and mild inflation. Despite persistent demographic headwinds from an aging "
        "population, Tokyo's financial markets have shown robust resilience, attracting surging "
        "foreign investment. On the technological front, Japan is accelerating its domestic "
        "semiconductor manufacturing capabilities, backed by massive government subsidies aimed at "
        "rebuilding its chip-making dominance and securing global supply chains. Innovation in "
        "artificial intelligence is booming, with Japanese tech giants focusing on specialized AI "
        "models designed for automation, eldercare robotics, and smart manufacturing to counter "
        "labor shortages. Green technology is another major frontier; automakers are ramping up "
        "investments in next-generation solid-state batteries and hydrogen fuel cells, aiming to "
        "revolutionize the global EV market. Meanwhile, smart city initiatives in Osaka and Tokyo "
        "are integrating IoT and 5G networks to optimize public transit and energy efficiency, "
        "solidifying Japan's status as a leader in sustainable urban tech."
    )

    # # Constructing the final message dictionary
    # msg = {
    #     "culture_summary": culture_summary,
    #     "articles_summary": articles_summary,
    # }
    # product_classifer_graph = build_product_classifier_agent()
    # product_classifer_graph_compiled = product_classifer_graph.compile()

    # # Example print to verify lengths
    # print(f"Culture Summary Length: {len(msg['culture_summary'])} characters")
    # print(f"Articles Summary Length: {len(msg['articles_summary'])} characters")

    # msg={"culture_summary":culture_summary,"articles_summary":articles_summary}

    # result = product_classifer_graph_compiled.invoke(
    # msg
    # )
    # print(result)

    top_candidates=["SonicWave Mini Bluetooth Speaker","LuminaGlow Smart LED Bulb"
                    ,"TrailBlazer Ergonomic Backpack"
                    ,"PulseFit Fitness Tracker"]
    msg={"culture_summary":culture_summary,"articles_summary":articles_summary,"top_candidates":top_candidates}
    marketing_agent = build_marketing_agent()
    marketing_graph_compiled = marketing_agent.compile()
    result = marketing_graph_compiled.invoke(
    msg
    )
    result
    print(result["marketing_scripts"])
if __name__ == "__main__":
    main()