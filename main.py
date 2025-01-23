import operator
import chainlit as cl
from chainlit.input_widget import Select, Switch
from dotenv import load_dotenv
from typing import Annotated, Sequence, TypedDict
from langchain_core.messages import (
    BaseMessage,
    HumanMessage,
    SystemMessage,
)
from langgraph.graph import END, StateGraph

# own imports
from tools import list_tables, describe_table
from agents.agents import (
    query_generator_agent,
    run_query_agent,
    revise_results_agent,
    web_search_agent,
)
from llm_models import get_ollama_llm, get_openai_llm
from schemas import GraphState

load_dotenv()

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

    # Create an initial GraphState with a system message about the tables
    initial_state = GraphState(
        user_input="",
        messages=[
            SystemMessage(content=table_descriptions),
        ],
        iterations=0,
    )

    # Store in the user session so we can retrieve and update it on each user message
    cl.user_session.set("graph_state", initial_state)

    await cl.Message(content="Hello! How can I assist you today 🤖").send()


@cl.on_settings_update
async def on_settings_update(settings):
    cl.user_session.set("llm_choice", settings["llm"])
    cl.user_session.set("allow_web_search", settings["rag_internet"])


# TypedDict-based approach
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]


# Build the workflow
workflow = StateGraph(GraphState)


async def create_query(state):
    return await query_generator_agent(state, tables, table_descriptions, llm)


async def run_query(state):
    return await run_query_agent(state, table_descriptions, llm)


async def revise(state):
    return await revise_results_agent(state, llm)


async def web_search(state):
    return await web_search_agent(state, llm)


workflow.add_node("analyze", create_query)
workflow.add_node("query", run_query)
workflow.add_node("revise", revise)
workflow.add_node("web_search", web_search)


# If question was not database related, then no query is needed
def is_query_needed(state):
    if state["query_needed"]:
        return "query"
    else:
        return END


workflow.add_conditional_edges("analyze", is_query_needed)
workflow.add_edge("query", "revise")
workflow.add_edge("web_search", "analyze")


# If you want to enable the web search, you can use the following code (remove return from begin)
def is_done(state):
    return END
    if state["done"].done:
        return "END"
    elif state["iterations"] > 2:
        return "END"
    return "web_search"


workflow.add_conditional_edges("revise", is_done)
workflow.set_entry_point("analyze")

graph = workflow.compile()
graph.get_graph().draw_mermaid_png(output_file_path="images/graphs/chainlit_graph.png")


@cl.on_message
async def run_convo(message: cl.Message):
    print("\n********ON MESSAGE**********")

    # Pick the LLM
    global llm
    llm_choice = cl.user_session.get("llm_choice", "OpenAI")
    if llm_choice == "OpenAI":
        llm = get_openai_llm()
    else:
        llm = get_ollama_llm(llm_choice)

    # Retrieve our conversation state from session
    state = cl.user_session.get("graph_state")
    if not state:
        # Fallback if it's missing for some reason
        state = GraphState(
            user_input="",
            messages=[SystemMessage(content=table_descriptions)],
            iterations=0,
        )

    # Append the new user message to the conversation
    state["messages"].append(HumanMessage(content=message.content))
    state["user_input"] = message.content

    # Invoke the workflow
    updated_state = await graph.ainvoke(state)

    # Retrieve the final assistant output from the updated state
    response_message_markdown = updated_state["db_formatted_results"]

    # Check if the response is valid before appending or sending
    if response_message_markdown is not None:
        # Append the valid response to the conversation history
        updated_state["messages"].append(
            SystemMessage(content=response_message_markdown)
        )

        # Save updated state back to user session
        cl.user_session.set("graph_state", updated_state)

        # Send the response only if it's not None
        await cl.Message(response_message_markdown).send()
    else:
        # Do not append or send anything if the response is None
        print("No response sent as the result is None.")
