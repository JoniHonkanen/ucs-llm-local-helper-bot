import json
import chainlit as cl
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage, AIMessage
from langchain_community.tools.tavily_search import TavilySearchResults

# Own imports
from schemas import (
    CreateDatabaseQuerySchema,
    AfterQuerySchema,
    ReflectionSchema,
    WebSearchSchema,
)
from tools.sql import run_query_tool
from prompts import (
    QUERY_GENERATOR_AGENT_PROMPT,
    RUN_DATABASE_QUERY_AGENT_PROMPT,
    REVISE_RESULTS_AGENT_PROMPT,
    WEB_SEARCH_AGENT_PROMPT,
)
from utils import format_query_results


# Utility function to invoke LLM with bound tools and return response
async def invoke_llm(llm, messages, tool_schema):
    llm_call = llm.bind_tools(tools=[tool_schema], tool_choice=tool_schema.__name__)
    response = llm_call.invoke(messages)
    tool_call_args = response.tool_calls[0]["args"]
    tool_call_id = response.tool_calls[0]["id"]
    return tool_call_args, tool_call_id


async def query_generator_agent(state, tables, table_descriptions, llm):
    print("\n**QUERY GENERATOR AGENT**")
    last_message = state["messages"][-1]
    structured_llm = llm.with_structured_output(CreateDatabaseQuerySchema)

    prompt = QUERY_GENERATOR_AGENT_PROMPT.format(
        tables=tables,
        table_descriptions=table_descriptions,
        user_input=last_message.content,
    )
    data = structured_llm.invoke(prompt)
    query = data.query
    info = data.info

    await cl.Message(content=info).send()
    await cl.Message(content=query, author="query", language="sql").send()

    state["messages"] += [
        AIMessage(content=f"Description of generated database query: {info}"),
        AIMessage(content=f"Generated database query: {query}"),
    ]
    state["db_query"] = query

    return state


# Agent to run the generated database query - run_query
async def run_query_agent(state, table_descriptions, llm):
    print("\n**RUN DATABASE QUERY AGENT**")
    query = state["db_query"]

    # run the query
    results = run_query_tool.func(query)
    formatted_results = format_query_results(results)

    structured_llm = llm.with_structured_output(AfterQuerySchema)

    prompt = RUN_DATABASE_QUERY_AGENT_PROMPT.format(
        query=query, results=formatted_results, table_descriptions=table_descriptions
    )

    data = structured_llm.invoke(prompt)
    formatted_response = data.formatted_response

    state["db_results"] = results
    state["db_formatted_results"] = formatted_response
    state["messages"] += [
        AIMessage(content=f"Results from database: {results}"),
    ]

    await cl.Message(content="Query executed successfully.").send()
    return state


async def revise_results_agent(state, llm):
    print("\n**REVISE RESULTS AGENT**")
    original_question = state["user_input"]
    db_results = state["db_results"]
    structured_llm = llm.with_structured_output(ReflectionSchema)

    prompt = REVISE_RESULTS_AGENT_PROMPT.format(
        question=original_question, answer=db_results
    )
    data = structured_llm.invoke(prompt)
    done = data.done
    reflection = data.reflect
    state["messages"] += [
        AIMessage(content=f"Is everything done: {done}"),
        AIMessage(content=f"Reflection for this: {reflection}"),
    ]
    state["done"] = data
    state["iterations"] += 1

    return state


async def web_search_agent(state, llm):
    print("\n**WEB SEARCH AGENT**")
    original_question = state["user_input"]

    structured_llm = llm.with_structured_output(WebSearchSchema)

    prompt = WEB_SEARCH_AGENT_PROMPT.format(
        question=original_question,
        reflect=state["done"].reflect,
        suggestions=state["done"].suggestions,
        missing_aspects=state["done"].missing_aspects,
    )

    data = structured_llm.invoke(prompt)

    print(data)

    web_search_query = data.web_search
    search_tool = TavilySearchResults(max_results=1)
    search_results = search_tool.invoke(web_search_query)
    search_result_content = search_results[0]["content"]

    print(search_result_content)

    # TODO: PARANNUKSIA TÄNNE
    # search_result_content KORVAA alkuperäisen kysymyksen, jonka jälkeen luodaan tietokantakysely uudestaan jne.
    # Tähän lopetin 30.8.2024 klo 16:45... jatka tästä

    state["user_input"] = search_result_content
    return state
