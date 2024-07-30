import json
import chainlit as cl
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage, AIMessage
from langchain_community.tools.tavily_search import TavilySearchResults

# own imports
from schemas import CreateDatabaseQyerySchema, AfterQuerySchema, ReflectionSchema
from tools.sql import run_query_tool
from prompts import (
    create_prompt_template,
    run_query_prompt_template,
    revise_prompt_template,
)
from utils import format_query_results

# Initialize the language model
# llm = ChatOpenAI(model="gpt-4o-mini")


# Agent to generate a query - create_query
async def query_generator_agent(state, tables, table_descriptions, llm):
    print("--------QUERY GENERATOR AGENT------------")
    messages = state["messages"]
    # Create the prompt template with table descriptions
    prompt_template = create_prompt_template(tables, table_descriptions)
    # Format messages using the prompt template
    # Extract message content
    messages_content = [msg.content for msg in messages]
    formatted_messages = prompt_template.format(messages=messages_content)

    # Call the language model using tool which is defined in schemas.py
    llm_call = llm.bind_tools(
        tools=[CreateDatabaseQyerySchema], tool_choice="CreateDatabaseQyerySchema"
    )
    response = llm_call.invoke(formatted_messages)

    # Extract the generated query and info
    tool_call_args = response.tool_calls[0]["args"]
    tool_call_id = response.tool_calls[0]["id"]

    query = tool_call_args["query"]
    info = tool_call_args["info"]

    await cl.Message(content=info).send()
    await cl.Message(content=query, author="query", language="sql").send()

    return {
        "messages": [
            ToolMessage(content=json.dumps(tool_call_args), tool_call_id=tool_call_id)
        ]
    }


# Agent to run the generated database query - run_query
def run_query_agent(state, table_descriptions, llm):
    print("--------RUN QUERY AGENT------------")
    # first message from user
    # second message is sytem message wich describe the tables
    # then tool message which contains the query + other info
    print(state["messages"])
    messages = state["messages"][2].content
    # Parse the JSON content
    tool_message_data = json.loads(messages)
    # Extract the query
    query = tool_message_data["query"]

    results = run_query_tool.func(query)
    formatted_results = format_query_results(results)

    prompt_template = run_query_prompt_template(
        query, formatted_results, table_descriptions
    )

    # TÄÄ VARMAAN TURHA... KATO MITÄ MESSAGES KOHTAAN TULEE
    messages_content = state["messages"][0].content
    formatted_messages = prompt_template.format(messages=[messages_content])
    # llm_call = llm.invoke(formatted_messages)

    llm_call = llm.bind_tools(tools=[AfterQuerySchema], tool_choice="AfterQuerySchema")
    response = llm_call.invoke(formatted_messages)

    # Extract the generated query and info
    tool_call_args = response.tool_calls[0]["args"]
    tool_call_id = response.tool_calls[0]["id"]

    # markdown = tool_call_args["formatted_response"]
    # response1 = tool_call_args["response"]

    return {
        "messages": [
            ToolMessage(content=json.dumps(tool_call_args), tool_call_id=tool_call_id)
        ]
    }

    # return {"messages": [AIMessage(content=llm_call.content)]}


# Agent to revise the generated query - revise
def revise_results_agent(state, llm):
    print("\n--------REVISE AGENT------------")
    orginal_question = state["messages"][0].content
    mes2 = state["messages"][-1].content
    revised_answer = json.loads(mes2)  # ["response"]

    prompt_template = revise_prompt_template(
        orginal_question, revised_answer["response"]
    )
    # TÄÄ VARMAAN TURHA... KATO MITÄ MESSAGES KOHTAAN TULEE
    messages_content = state["messages"][0].content
    formatted_messages = prompt_template.format(messages=[messages_content])

    llm_call = llm.bind_tools(tools=[ReflectionSchema], tool_choice="ReflectionSchema")
    response = llm_call.invoke(formatted_messages)

    # Extract the generated query and info
    tool_call_args = response.tool_calls[0]["args"]
    tool_call_id = response.tool_calls[0]["id"]

    return {
        "messages": [
            ToolMessage(content=json.dumps(tool_call_args), tool_call_id=tool_call_id)
        ]
    }


def web_search_agent(state, llm):
    print("------------WEB SEARCH AGENT---------------")
    # create web search tool using tavily_search
    search_tool = TavilySearchResults(max_results=5)
    search_results = search_tool.invoke("What is bengalcat")
    print(search_results)
