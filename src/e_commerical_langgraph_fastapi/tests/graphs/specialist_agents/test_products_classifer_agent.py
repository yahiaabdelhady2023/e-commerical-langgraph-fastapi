from langgraph.checkpoint.memory import MemorySaver

from app.graphs.specialist_agents.products_classifer_agent import build_product_classifier_agent


def test_product_classifer_agent():
    """Ensure the classifier graph can evaluate a culture summary and choose products."""
    checkpointer = MemorySaver()
    graph = build_product_classifier_agent()
    compile_graph = graph.compile(checkpointer=checkpointer)

    culture_summary = (
        "Japan's culture is a masterclass in blending ancient traditions with futuristic "
        "innovation. At its core lies the concept of 'Wa' (harmony), which shapes social "
        "interactions, emphasizing community, respect, and politeness over individualism. "
        "Traditional arts like the tea ceremony (Chado), flower arranging (Ikebana), and "
        "classical theater (Noh and Kabuki) remain deeply respected, reflecting Zen Buddhist "
        "philosophies of mindfulness and appreciating impermanence (Wabi-Sabi). Simultaneously, "
        "Japan is a global pop-culture powerhouse. Anime, manga, and gaming are not just "
    )

    articles_summary = (
        "Recent headlines from Japan highlight significant shifts across its economic landscape "
        "and technology sector. Economically, the Bank of Japan continues to navigate a delicate "
        "transition away from its long-standing ultra-loose monetary policy, responding to steady "
        "wage growth and mild inflation. Despite persistent demographic headwinds from an aging "
        "population, Tokyo's financial markets have shown robust resilience, attracting surging "
        "foreign investment. On the technological front, Japan is accelerating its domestic "
        "semiconductor manufacturing capabilities, backed by massive government  "
    )


    phone_brands = [
        # South Korean
        "phone_Samsung",
        "phone_LG",
        "phone_Pantech",
        # Japanese
        "phone_Sony",
        "phone_Sharp",
        "phone_Kyocera",
        "phone_Panasonic",
        "phone_Fujitsu",
    ]
    product_info_list = [
        {
            "name": product_name,
            "price": 499.99,
            "description": f"{product_name} smartphone with modern performance and connectivity features.",
            "category": "Smartphone",
            "rating": 4.0,
            "source_address": None,
        }
        for product_name in phone_brands
    ]
    mocked_state = {
        "product_name_list": phone_brands,
        "product_info_list": str(product_info_list),
        "culture_summary": culture_summary,
        "articles_summary": articles_summary,
    }
    config = {"configurable": {"thread_id": "1"}}
    compile_graph.update_state(
        config,
        mocked_state,
        as_node="fetch_products"
    )
    result = compile_graph.invoke(None, config)

    assert "top_candidates" in result
    assert len(result["top_candidates"]) > 0
    assert "feedback" in result
    assert len(result["feedback"]) > 0
