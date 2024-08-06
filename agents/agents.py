import json
import chainlit as cl
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage, AIMessage
from langchain_community.tools.tavily_search import TavilySearchResults

# Own imports
from schemas import CreateDatabaseQuerySchema, AfterQuerySchema, ReflectionSchema, WebSearchSchema
from tools.sql import run_query_tool
from prompts import create_prompt_template, run_query_prompt_template, revise_prompt_template, rag_web_search_prompt_template
from utils import format_query_results

# Utility function to invoke LLM with bound tools and return response
async def invoke_llm(llm, messages, tool_schema):
    llm_call = llm.bind_tools(tools=[tool_schema], tool_choice=tool_schema.__name__)
    response = llm_call.invoke(messages)
    tool_call_args = response.tool_calls[0]["args"]
    tool_call_id = response.tool_calls[0]["id"]
    return tool_call_args, tool_call_id

# Agent to generate a query - create_query
async def query_generator_agent(state, tables, table_descriptions, llm):
    last_message = state["messages"][-1]
    prompt_template = create_prompt_template(tables, table_descriptions)
    formatted_messages = prompt_template.format(messages=[last_message])
    tool_call_args, tool_call_id = await invoke_llm(llm, formatted_messages, CreateDatabaseQuerySchema)

    query = tool_call_args["query"]
    info = tool_call_args["info"]

    await cl.Message(content=info).send()
    await cl.Message(content=query, author="query", language="sql").send()

    return {"messages": [ToolMessage(content=json.dumps(tool_call_args), tool_call_id=tool_call_id)]}

# Agent to run the generated database query - run_query
async def run_query_agent(state, table_descriptions, llm):
    tool_message_data = json.loads(state["messages"][2].content)
    query = tool_message_data["query"]
    results = run_query_tool.func(query)
    formatted_results = format_query_results(results)

    prompt_template = run_query_prompt_template(query, formatted_results, table_descriptions)
    formatted_messages = prompt_template.format(messages=state["messages"])
    tool_call_args, tool_call_id = await invoke_llm(llm, formatted_messages, AfterQuerySchema)

    await cl.Message(content="Query executed successfully.").send()
    return {"messages": [ToolMessage(content=json.dumps(tool_call_args), tool_call_id=tool_call_id)]}

# Agent to revise the generated query - revise
async def revise_results_agent(state, llm):
    original_question = state["messages"][0].content
    revised_answer = json.loads(state["messages"][-1].content)["response"]

    prompt_template = revise_prompt_template(original_question, revised_answer)
    formatted_messages = prompt_template.format(messages=state["messages"])
    tool_call_args, tool_call_id = await invoke_llm(llm, formatted_messages, ReflectionSchema)

    return {"messages": [ToolMessage(content=json.dumps(tool_call_args), tool_call_id=tool_call_id)]}

# Agent to handle web search - web_search
async def web_search_agent(state, llm):
    original_question = state["messages"][0].content
    last_message_data = json.loads(state["messages"][-1].content)
    reflect = last_message_data["reflect"]
    suggestions = last_message_data["suggestions"]
    missing_aspects = last_message_data["missing_aspects"]

    prompt_template = rag_web_search_prompt_template(original_question, reflect, suggestions, missing_aspects)
    formatted_messages = prompt_template.format(messages=state["messages"])
    tool_call_args, tool_call_id = await invoke_llm(llm, formatted_messages, WebSearchSchema)

    web_search_query = tool_call_args["web_search"]
    search_tool = TavilySearchResults(max_results=1)
    search_results = search_tool.invoke(web_search_query)
    search_result_content = search_results[0]["content"]

    return {
        "messages": [
            ToolMessage(content=json.dumps(tool_call_args), tool_call_id=tool_call_id),
            AIMessage(content=search_result_content)
        ]
    }
