import pytest
from app.graphs.specialist_agents.create_products_agent import build_product_agent, Product
from langgraph.checkpoint.memory import MemorySaver
from pydantic import BaseModel, Field





def test_product_agent():
    """tests the whole agent system"""
    checkpointer = MemorySaver()
    graph  = build_product_agent()
    compile_graph = graph.compile(checkpointer=checkpointer)
    inputs = {
    "messages": [
        {
            "role": "user", 
            "content": "extract data from  https://api.escuelajs.co/api/v1/products and local file documents/mock_products_100.json"
        }
        ]
    }
    config = {"configurable": {"thread_id": "1"}}

    result = compile_graph.invoke(inputs,config)

    #test if it extracted exactly 2 resources
    # assert len(result["processed_resource_list"]) == 2

    #test if it has extracted data or not
    assert len(result["products_list"]) !=0

def test_product_agent_extraction():
    """tests if agent can extract and create pythonic validation models
    based on a simple json file, and the schema matches with predefined validation pydantic schemas"""
    checkpointer = MemorySaver()
    graph  = build_product_agent()

    compile_graph = graph.compile(checkpointer=checkpointer)
    inputs = {
    "messages": [
        {
            "role": "user", 
            "content": "file documents/single_product.json"
        }
        ]
    }
    config = {"configurable": {"thread_id": "1"}}
    result = compile_graph.invoke(inputs,config)

    
    single_product = Product(
            name='SonicWave Mini Bluetooth Speaker', 
            price=19.99, 
            description='Pocket-sized speaker with surprisingly deep bass. IPX7 waterproof rating.', 
            category='Audio', 
            rating=4.1, 
            source_address=None
        )
    #test if it has extracted data or not
    assert single_product == result["products_list"][0]

    