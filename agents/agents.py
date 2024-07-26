import json
import chainlit as cl
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage, AIMessage
from schemas import CreateDatabaseQyerySchema, AfterQuerySchema, AfterQuerySchema2
from tools.sql import run_query_tool
from prompts import create_prompt_template, run_query_prompt_template

# Initialize the language model
# llm = ChatOpenAI(model="gpt-4o-mini")


# Agent to generate a query - create_query
async def query_generator_agent(state, tables, table_descriptions, llm):
    print("QUERY GENERATOR AGENT")
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
    print("RUN QUERY AGENT")
    #first message from user
    #second message is sytem message wich describe the tables
    #then tool message which contains the query + other info
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

    # orginal question messages from user
    messages_content = state["messages"][0].content
    formatted_messages = prompt_template.format(messages=[messages_content])
    llm_call = llm.invoke(formatted_messages)

    return {"messages": [AIMessage(content=llm_call.content)]}


# Format the query results
def format_query_results(results):
    print("format_query_results")
    if not results:
        return "No results found."
    elif len(results) == 1 and isinstance(results[0], tuple) and len(results[0]) == 1:
        return f"Query Result: {results[0][0]}"
    else:
        return "\n".join([str(row) for row in results])


# Agent to revise the generated query - revise
def revise_results_agent(state, llm):
    print("REVISE AGENT")
    print(state)
    return state
