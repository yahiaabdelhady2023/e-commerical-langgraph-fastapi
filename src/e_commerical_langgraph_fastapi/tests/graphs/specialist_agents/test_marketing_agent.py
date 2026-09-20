from langgraph.checkpoint.memory import MemorySaver

from app.graphs.specialist_agents.marketing_agent import build_marketing_agent


def test_marketing_agent():
    """Ensure the marketing agent works."""
    checkpointer = MemorySaver()
    graph = build_marketing_agent()
    compile_graph = graph.compile(checkpointer=checkpointer)
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

    top_candidates=["SonicWave Mini Bluetooth Speaker","LuminaGlow Smart LED Bulb"
                    ,"TrailBlazer Ergonomic Backpack"
                    ,"PulseFit Fitness Tracker"]
    top_candidates_dict = [
        {
            "name": "SonicWave Mini Bluetooth Speaker",
            "price": 19.99,
            "description": "Pocket-sized speaker with surprisingly deep bass. IPX7 waterproof rating.",
            "category": "Audio",
            "rating": 4.1,
            "source_address": None
        },
        {
            "name": "LuminaGlow Smart LED Bulb",
            "price": 14.50,
            "description": "Color-changing smart bulb compatible with Alexa and Google Assistant. 800 lumens.",
            "category": "Smart Home",
            "rating": 4.5,
            "source_address": None
        },
        {
            "name": "AeroCharge Wireless Charging Pad",
            "price": 24.99,
            "description": "15W fast wireless charging pad with non-slip surface and LED indicator.",
            "category": "Accessories",
            "rating": 4.3,
            "source_address": None
        },
        {
            "name": "PulseFit Fitness Tracker",
            "price": 39.99,
            "description": "Lightweight fitness tracker with heart rate monitor, step counter, and sleep tracking.",
            "category": "Wearables",
            "rating": 4.0,
            "source_address": None
        }
    ]
    mocked_state={"culture_summary":culture_summary,"articles_summary":articles_summary
            ,"top_candidates":top_candidates,
            "top_candidates_dict":top_candidates_dict,
            "marketing_scripts":[]}

    config = {"configurable": {"thread_id": "1"}}

    compile_graph.update_state(
        config,
        mocked_state,
        as_node="fetch_target_products"
    )
    result = compile_graph.invoke(None, config)

    assert len(result["marketing_scripts"]) == 4
    assert isinstance(result["marketing_scripts"][0], str)
