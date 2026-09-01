from pydantic import BaseModel, Field
from typing import List, Literal, Optional, Dict, Any
from typing_extensions import Annotated, TypedDict
from langgraph.graph.message import add_messages
import operator
from requests import request
from bs4 import BeautifulSoup
from html_to_markdown import convert
from langchain.chat_models import init_chat_model
from dotenv import load_dotenv
import csv

import sys
print(sys.path)

from app.graphs.custom_functions.utility_functions import handle_web_requests, get_encoding, locate_file, pythonic_text_clean
from langgraph.types import Send
from langgraph.graph import StateGraph, START, END
import io
from PIL import Image



load_dotenv()
FAIL="failed"
SUCCESS="success"

general_llm = init_chat_model(model="gemini-3.1-flash-lite", model_provider="google_genai")

####################################################################
#              1. RESOURCES STATE
####################################################################
class ResourceWorkerState(TypedDict): #private state
    current_resource: str
    type_resource: Literal["json_file","html","api","txt","csv"]
    messages: Annotated[list[str], add_messages]
    data_list : Annotated[list[str], add_messages]
    error_messages : Annotated[list[str], add_messages]
    processed_resource_list: Annotated[list[str], operator.add]

class ResourceState(TypedDict):
    messages: Annotated[list[str], add_messages]
    data_list : Annotated[list[str], add_messages]
    resource_list : list[str] 
    processed_resource_list: Annotated[list[str], operator.add]
    error_messages : Annotated[list[str], add_messages]
    feedback_message : str

####################################################################
#              2. Validation Models
####################################################################

class ResourceExtractSchema(BaseModel):
    """runs once, it intialises resource_list"""
    resource_list : list[str] = Field(description="given a message extract urls and datasets csv/txt/json filenames from that message and store them in list")

class ResourceProcessingSchema(BaseModel):
    """changes throughout nodes"""
    type_resource: Literal["json_file","html","txt","api","csv"] = Field(description="Based on resource if it has api word in it assume it returns 'api' , if it is a normal webpage assume it returns 'html' , else check its file extension type and select appropriate data type'")

####################################################################
#              3. Classifier nodes
####################################################################
def manager_task_classifier(state: ResourceState):
    """given a list of resources, and list of processed resources, it checks if they are equal then terminates,
    however if an error took place it will retry to fetch it again, if it failed again it will write error message explaining
    what happened then it will exit"""
    
    print("manager_task_classifier() --> Analysis --->")
    print("============================================")
    print("len: processed_resource_list",len(state["processed_resource_list"]))
    print("len: resource_list",len(state["resource_list"]))
    print("resource_list ",state["resource_list"])
    print("processed_resource_list ",state["processed_resource_list"])
    print("current_resource ",state["current_resource"])
    print("============================================")

    if len(state["processed_resource_list"]) == len(state["resource_list"]):
        work_status = "finished"
    else:
        work_status = "inprogress"

    return {"work_status":work_status}


#router node
def resource_router(state: ResourceWorkerState):
    return state["type_resource"]

def resource_task_splitter_router(state: ResourceState):
    return [Send("resource_subgraph",{"current_resource":resource}) for resource in state["resource_list"]]

def task_manager_router(state: ResourceState):
    return state["work_status"]

#regular nodes
def extract_resources(state: ResourceState):
    """given user message, it extracts all urls,txt file names, etc , also it returns data type for each url in a list"""
    last_message = state["messages"][-1].content
    structured_output_llm = general_llm.with_structured_output(ResourceExtractSchema)
    msg = [
        {"role":"user","content":last_message}
    ]
    result = structured_output_llm.invoke(msg)
    print("extract_resources --> resource_list",result.resource_list)
    return {"resource_list":result.resource_list}

####################################################################
#              4. PROCESSOR NODES
####################################################################

def classify_resource(state: ResourceWorkerState):
    """given a resoruce, it will determine its data type"""
    current_resource = state["current_resource"]
    print("classify_resource  current_resource-->",current_resource)
    structured_output_llm = general_llm.with_structured_output(ResourceProcessingSchema)
    msg = [
        {"role":"user","content":current_resource}
    ]
    result = structured_output_llm.invoke(msg)
    return {"type_resource":result.type_resource}

def fetch_api(state: ResourceWorkerState):
    """given a current url resource, it extracts data from that resource, which will be generally in json"""
    print("state is",state)
    print("state is",type(state))

    current_resource = state["current_resource"]
    response, status_flag = handle_web_requests(current_resource)
    try:
        if status_flag == SUCCESS:
            return {"data_list":[str(response.json())], "processed_resource_list":[current_resource]}
        else:
            return {"error_messages":response}
    except Exception as e:
        return {"error_messages":f"error failed to fetch_api from {current_resource} reason {e}"}

def fetch_html(state: ResourceWorkerState):
    """given a current url resource that is not an api, it will be assumed that we want to web scrape it"""
    current_resource = state["current_resource"]
    response, status_flag = handle_web_requests(current_resource)
    try:
        if status_flag == SUCCESS:
            exclude_tags=["script","head","title","style","svg","!doctype","meta"]
            soup =  BeautifulSoup(response.text, "html.parser")
            for tag in exclude_tags:
                    for match in soup.find_all(tag):
                        match.extract()
            return {"messages":[str(soup)], "processed_resource_list":[current_resource]}
        else:
            return {"error_messages":response}
    except Exception as e:
        return {"error_messages":f"error failed to fetch html data from {current_resource} reason {e}"}

def html_to_markdown(state: ResourceWorkerState):
    """given html it will convert it into markdown which is the format most LLMs prefer for processing data"""
    print("html_to_markdown state --> ",state)
    html_content = state["messages"][-1].content
    markdown_object = convert(str(html_content))
    markdown = markdown_object.content
    return {"data_list":[markdown]}

def fetch_csv(state: ResourceWorkerState):
    """given a valid csv file name, it will be fetch csv data from it"""
    file_path_string = state["current_resource"]
    filepath = locate_file(file_path_string)
    correct_encoding = get_encoding(filepath)
    with open(filepath,mode="r", encoding=correct_encoding) as file:
        reader = csv.DictReader(file,delimiter=",")
        data = list(reader)
        return {"data_list":data, "processed_resource_list":[file_path_string]}

def fetch_txt(state: ResourceWorkerState):
    """given a valid txt file name, it will be fetch text data from it"""
    file_path_string = state["current_resource"]
    filepath = locate_file(file_path_string)
    correct_encoding = get_encoding(filepath)
    with open(filepath,mode="r", encoding=correct_encoding) as file:
        data = file.read()
        return {"data_list":[data], "processed_url_list":[file_path_string]}

def fetch_json_file(state: ResourceWorkerState):
    """given a valid json file, it will fetch json data from it"""
    file_path_string = state["current_resource"]
    filepath = locate_file(file_path_string)
    correct_encoding = get_encoding(filepath)
    with open(filepath,mode="r", encoding=correct_encoding) as file:
        data = file.read()
        return {"data_list":[data], "processed_url_list":[file_path_string]}


####################################################################
#              5. RESOURCE SUBGRAPH CONSTRUCTION
####################################################################

resource_subgraph = StateGraph(ResourceWorkerState)
resource_subgraph.add_node("fetch_api",fetch_api)
resource_subgraph.add_node("fetch_html",fetch_html)
resource_subgraph.add_node("html_to_markdown",html_to_markdown)
resource_subgraph.add_node("fetch_csv",fetch_csv)
resource_subgraph.add_node("fetch_txt",fetch_txt)
resource_subgraph.add_node("fetch_json_file",fetch_json_file)
resource_subgraph.add_node("classify_resource",classify_resource)

resource_subgraph.add_edge(START,"classify_resource")
resource_subgraph.add_conditional_edges("classify_resource",
                            resource_router,
                            {"api":"fetch_api",
                             "html":"fetch_html",
                             "txt":"fetch_txt",
                             "csv":"fetch_csv",
                             "json_file":"fetch_json_file"}
                            )
resource_subgraph.add_edge("fetch_html","html_to_markdown")
resource_subgraph.add_edge("html_to_markdown",END)
resource_subgraph.add_edge("fetch_json_file",END)
resource_subgraph.add_edge("fetch_txt",END)
resource_subgraph.add_edge("fetch_csv",END)
resource_subgraph.add_edge("fetch_api",END)

compiled_resource_subgraph = resource_subgraph.compile()


####################################################################
#              6. PARENT RESOURCE GRAPH CONSTRUCTION
####################################################################

resource_parentgraph = StateGraph(ResourceState)
resource_parentgraph.add_node("extract_resources",extract_resources)
resource_parentgraph.add_node("resource_subgraph",compiled_resource_subgraph)
resource_parentgraph.add_edge(START,"extract_resources")
resource_parentgraph.add_conditional_edges("extract_resources",resource_task_splitter_router,["resource_subgraph"])
resource_parentgraph.add_edge("resource_subgraph",END)

compiled_resource_parentgraph = resource_parentgraph.compile()


####################################################################
#              7. Saving Graph Images
####################################################################

graph_bytes = io.BytesIO(compiled_resource_parentgraph.get_graph().draw_mermaid_png())

with Image.open(graph_bytes) as img:
    img.save("parent_graph.png")

####################################################################
#              8. Import Build
####################################################################


def build_resources_agent():
    resource_parentgraph = StateGraph(ResourceState)
    resource_parentgraph.add_node("extract_resources",extract_resources)
    resource_parentgraph.add_node("resource_subgraph",compiled_resource_subgraph)
    resource_parentgraph.add_edge(START,"extract_resources")
    resource_parentgraph.add_conditional_edges("extract_resources",resource_task_splitter_router,["resource_subgraph"])
    resource_parentgraph.add_edge("resource_subgraph",END)

    # compiled_resource_parentgraph = resource_parentgraph.compile()
    return resource_parentgraph

def build_resources_subgraph_agent():
    resource_subgraph = StateGraph(ResourceWorkerState)
    resource_subgraph.add_node("fetch_api",fetch_api)
    resource_subgraph.add_node("fetch_html",fetch_html)
    resource_subgraph.add_node("html_to_markdown",html_to_markdown)
    resource_subgraph.add_node("fetch_csv",fetch_csv)
    resource_subgraph.add_node("fetch_txt",fetch_txt)
    resource_subgraph.add_node("fetch_json_file",fetch_json_file)
    resource_subgraph.add_node("classify_resource",classify_resource)
    resource_subgraph.add_edge(START,"classify_resource")
    resource_subgraph.add_conditional_edges("classify_resource",
                                resource_router,
                                {"api":"fetch_api",
                                "html":"fetch_html",
                                "txt":"fetch_txt",
                                "csv":"fetch_csv",
                                "json_file":"fetch_json_file"}
                                )
    resource_subgraph.add_edge("fetch_html","html_to_markdown")
    resource_subgraph.add_edge("html_to_markdown",END)
    resource_subgraph.add_edge("fetch_json_file",END)
    resource_subgraph.add_edge("fetch_txt",END)
    resource_subgraph.add_edge("fetch_csv",END)
    resource_subgraph.add_edge("fetch_api",END)
    return resource_subgraph
