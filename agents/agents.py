import json
import chainlit as cl
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage, AIMessage
from langchain_community.tools.tavily_search import TavilySearchResults

# from langchain_core.output_parsers import JsonOutputParser, PydanticOutputParser
# own imports
from schemas import (
    CreateDatabaseQuerySchema,
    AfterQuerySchema,
    ReflectionSchema,
    WebSearchSchema,
)
from tools.sql import run_query_tool
from prompts import (
    create_prompt_template,
    run_query_prompt_template,
    revise_prompt_template,
    rag_web_search_prompt_template,
)
from utils import format_query_results

# Initialize the language model
# llm = ChatOpenAI(model="gpt-4o-mini")

# TODO: Use parsers ??
# parser = JsonOutputParser(return_id=True)
# parser_pydantic = PydanticOutputParser(tools=[CreateDatabaseQuerySchema],type="CreateDatabaseQuerySchema")

# Agent to generate a query - create_query
async def query_generator_agent(state, tables, table_descriptions, llm):
    print("--------QUERY GENERATOR AGENT------------")
    # messages = state["messages"]
    messages = state["messages"][-1]
    print("MESSAGES: ", messages)
    # Create the prompt template with table descriptions
    prompt_template = create_prompt_template(tables, table_descriptions)
    # Format messages using the prompt template
    formatted_messages = prompt_template.format(messages=[messages])

    # Call the language model using tool which is defined in schemas.py
    llm_call = llm.bind_tools(
        tools=[CreateDatabaseQuerySchema], tool_choice="CreateDatabaseQuerySchema"
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
async def run_query_agent(state, table_descriptions, llm):
    print("--------RUN QUERY AGENT------------")
    # second message is sytem message wich describe the tables
    # then tool message which contains the query + other info
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

    formatted_messages = prompt_template.format(messages=state["messages"])

    llm_call = llm.bind_tools(tools=[AfterQuerySchema], tool_choice="AfterQuerySchema")
    response = llm_call.invoke(formatted_messages)

    # Extract the generated query and info
    tool_call_args = response.tool_calls[0]["args"]
    tool_call_id = response.tool_calls[0]["id"]
    
    await cl.Message(content="Query executed successfully.").send()

    return {
        "messages": [
            ToolMessage(content=json.dumps(tool_call_args), tool_call_id=tool_call_id)
        ]
    }

    # return {"messages": [AIMessage(content=llm_call.content)]}


# Agent to revise the generated query - revise
async def revise_results_agent(state, llm):
    print("\n--------REVISE AGENT------------")
    orginal_question = state["messages"][0].content
    mes2 = state["messages"][-1].content
    revised_answer = json.loads(mes2)  # ["response"]

    prompt_template = revise_prompt_template(
        orginal_question, revised_answer["response"]
    )

    formatted_messages = prompt_template.format(messages=state["messages"])

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


async def web_search_agent(state, llm):
    print("------------WEB SEARCH AGENT---------------")
    orginal_question = state["messages"][0].content
    lastMessage = state["messages"][-1].content
    lastMessageParsed = json.loads(lastMessage)
    print("LAST MESSAGE: ", lastMessage)
    print("LAST MESSAGE PARSED: ", lastMessageParsed)
    reflect = lastMessageParsed["reflect"]
    suggestions = lastMessageParsed["suggestions"]
    missing_aspects = lastMessageParsed["missing_aspects"]

    prompt_template = rag_web_search_prompt_template(
        orginal_question, reflect, suggestions, missing_aspects
    )

    formatted_messages = prompt_template.format(messages=state["messages"])
    llm_call = llm.bind_tools(tools=[WebSearchSchema], tool_choice="WebSearchSchema")
    response = llm_call.invoke(formatted_messages)

    # Extract the generated query and info
    tool_call_args = response.tool_calls[0]["args"]
    tool_call_id = response.tool_calls[0]["id"]
    tool_response = ToolMessage(
        content=json.dumps(tool_call_args), tool_call_id=tool_call_id
    )
    web_search = response.tool_calls[0]["args"]["web_search"]
    # create web search tool using tavily_search

    search_tool = TavilySearchResults(max_results=1)
    search_results = search_tool.invoke(web_search)
    #TODO: CHECK THAT tool_response and AI message are correct
    return {"messages": [tool_response, AIMessage(content=search_results[0]["content"])]}
