import asyncio
import operator
import chainlit as cl
from chainlit.input_widget import Select
from dotenv import load_dotenv
from typing import Annotated, Sequence, TypedDict
from langchain_core.messages import (
    BaseMessage,
    HumanMessage,
    ToolMessage,
    SystemMessage,
)
from langgraph.graph import END, StateGraph
from langchain_core.runnables import RunnableConfig
from langchain_openai import ChatOpenAI
from langchain_core.pydantic_v1 import BaseModel, Field
import json

# own imports
from tools import list_tables, describe_table
from agents.agents import (
    query_generator_agent,
    run_query_agent,
    revise_results_agent,
    web_search_agent,
)
from llm_models import get_ollama_llm, get_openai_llm
from utils import format_openai_response, format_ollama_response


load_dotenv()

# Initialize global LLM variable
# llm can be either Ollama or OpenAI
llm = get_openai_llm()


# Initialize database information
def initialize_database():
    global tables, table_descriptions
    tables = list_tables()
    table_names = [line.strip() for line in tables.strip().split("\n") if line.strip()]
    table_descriptions = describe_table(table_names)


initialize_database()


# Streamlit when starting the chat
@cl.on_chat_start
async def on_chat_start():
    # TODO: use ollama-python to get the list of available models and display them in the select widget -> ollama.list()
    await cl.ChatSettings(
        [
            Select(
                id="llm",
                label="Select the server you want to use:",
                values=[
                    "OpenAI",
                    "Ollama - llama3",
                    "Ollama - zephyr",
                    "Ollama - gemma:2b",
                    "Ollama - llava",
                ],
                initial_index=0,
            )
        ]
    ).send()
    await cl.Message(content="Hello! How can I assist you today 🤖").send()


@cl.on_settings_update
async def on_settings_update(settings):
    llm_choice = settings["llm"]
    cl.user_session.set("llm_choice", llm_choice)


# State
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    # messages: Sequence[BaseMessage] THIS COULD BE BETTER - SO MAYBE CHANGE TO IT


workflow = StateGraph(AgentState)


# this is the first function to call, it generates a database query based on the user input
def create_query(state):
    print("CREATE QUERY ALKAA")
    return asyncio.run(query_generator_agent(state, tables, table_descriptions, llm))


# this function runs the query and returns the results
def run_query(state):
    print("RUN QUERY ALKAA")
    return run_query_agent(state, table_descriptions, llm)


# this function revises the result and uses conditional edges to determine if task should be repeated with new input
def revise(state):
    print("REVISE ALKAA")
    return revise_results_agent(state, llm)

def web_search(state):
    print("WEB SEARCH ALKAA")
    return web_search_agent(state, llm)


# Nodes
workflow.add_node("analyze", create_query)
workflow.add_node("query", run_query)
workflow.add_node("revise", revise)
workflow.add_node("web_search", web_search)
workflow.set_entry_point("analyze")
# Edges
workflow.add_edge("analyze", "query")
workflow.add_edge("query", "revise")


def event_loop(state):
    print("******EVENT LOOP*******")
    print(state)
    count_tool_visits = sum(isinstance(item, ToolMessage) for item in state["messages"])
    print("COUNT TOOL VISITS: ", count_tool_visits)
    # Extracting the "done" part from the last message
    last_message_content = state['messages'][-1].content
    fulfilled = json.loads(last_message_content)['done']
    print("FULFILLED: ", fulfilled)

    if fulfilled:
        return END
    else:
        cl.user_session.state["messages"].append(SystemMessage(content="Lets search from web"))
        return "web_search"


workflow.add_conditional_edges("revise", event_loop)


# Initialize memory to persist state between graph runs
graph = workflow.compile()
graph.get_graph().draw_mermaid_png(output_file_path="images/graphs/chainlit_graph.png")


@cl.on_message
async def run_convo(message: cl.Message):
    print("********ON MESSAGE**********")
    # LLM to use
    global llm
    llm_choice = cl.user_session.get("llm_choice", "OpenAI")

    if llm_choice == "OpenAI":
        llm = get_openai_llm()
    else:
        llm = get_ollama_llm(llm_choice)

    # Initialize the state if not already done
    if not hasattr(cl.user_session, "state"):
        cl.user_session.state = AgentState(messages=[])

    # Add the new human message to the state
    cl.user_session.state["messages"].append(HumanMessage(content=message.content))
    cl.user_session.state["messages"].append(SystemMessage(content=table_descriptions))

    # inputs = {"messages": [HumanMessage(content=message.content)]}

    res = graph.invoke(
        # inputs,
        cl.user_session.state,
        config=RunnableConfig(
            callbacks=[cl.LangchainCallbackHandler()],
        ),
        debug=True,
    )
    # res comes after when whole graph is done
    print("RES", res)

    #response_message = res["messages"][-1].content
    #Last message with formatted response
    response_message2 = json.loads(res["messages"][-2].content)['formatted_response']

    # Openai and Ollama have different response formats, so we need to format them differently
    if llm_choice == "OpenAI":
        formatted_response = format_openai_response(response_message2)
    else:
        formatted_response = format_ollama_response(response_message2)

    await cl.Message(formatted_response).send()

    # reset state
    cl.user_session.state = AgentState(messages=[])
