import operator
import chainlit as cl
from chainlit.input_widget import Select, Switch
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
from typing import List
from pprint import pprint

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
from schemas import ReflectionSchema


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
            Switch(
                id="rag_internet",
                label="Allow complete responses by using web searches",
                initial=True,
            ),
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
            ),
        ]
    ).send()

    await cl.Message(content="Hello! How can I assist you today 🤖").send()


@cl.on_settings_update
async def on_settings_update(settings):
    # Update the LLM choice
    cl.user_session.set("llm_choice", settings["llm"])
    # Enable or disable web search
    # TODO: NOT IMPLEMENTED YET
    cl.user_session.set("allow_web_search", settings["rag_internet"])


# State
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    # messages: Sequence[BaseMessage] THIS COULD BE BETTER - SO MAYBE CHANGE TO IT


class GraphState(TypedDict):
    user_input: str
    messages: List
    db_query: str
    db_results: str
    db_formatted_results: str
    db_tables: str
    iterations: int
    done: ReflectionSchema


# workflow = StateGraph(AgentState)
workflow = StateGraph(GraphState)


# Define node functions
async def create_query(state):
    return await query_generator_agent(state, tables, table_descriptions, llm)


async def run_query(state):
    return await run_query_agent(state, table_descriptions, llm)


async def revise(state):
    return await revise_results_agent(state, llm)


async def web_search(state):
    return await web_search_agent(state, llm)


# Nodes
workflow.add_node("analyze", create_query)
workflow.add_node("query", run_query)
workflow.add_node("revise", revise)
workflow.add_node("web_search", web_search)

# Edges
workflow.add_edge("analyze", "query")
workflow.add_edge("query", "revise")
workflow.add_edge("web_search", "analyze")


def is_done(state):
    # Determ next steps after the first run
    if state["done"].done:
        return "END"
    else:
        if state["iterations"] > 2:
            return "END"
        return "web_search"


workflow.add_conditional_edges("revise", is_done)
workflow.set_entry_point("analyze")


# Initialize memory to persist state between graph runs
graph = workflow.compile()
graph.get_graph().draw_mermaid_png(output_file_path="images/graphs/chainlit_graph.png")


@cl.on_message
async def run_convo(message: cl.Message):
    print("\n********ON MESSAGE**********")
    # LLM to use
    global llm
    llm_choice = cl.user_session.get("llm_choice", "OpenAI")

    if llm_choice == "OpenAI":
        llm = get_openai_llm()
    else:
        llm = get_ollama_llm(llm_choice)

    res = await graph.ainvoke(
        {
            "messages": [
                SystemMessage(content=table_descriptions),
                HumanMessage(content=message.content),
            ],
            "user_input": message.content,
            "iterations": 0,
        }
    )

    response_message_markdown = res["db_formatted_results"]

    await cl.Message(response_message_markdown).send()
    print("\nDONE\n\n\n")
