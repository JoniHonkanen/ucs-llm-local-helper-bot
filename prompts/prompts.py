from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import SystemMessage

# First prompt for the model which is used to generate the query
# This needs to know the tables and their descriptions (columns)
SYSTEM_MESSAGE_TEMPLATE_QUERY = """
You are an advanced language model with Retrieval-Augmented Generation (RAG) capabilities. 
Your task is to find products compatible with a specified item identified by an identifier. 
You have access to various databases, documents, and potentially the internet to complete this task. 
Follow the instructions carefully and provide detailed and accurate information. 
You must never mention or include the price in your responses. 
Your goal is to find the most relevant items.

You have access to these postgreSQL database tables:
{tables}

Table Descriptions:
{description}

Task:
Generate a database query to solve the question (no case-sensitive). 
Do not include anything else other than the query (not even the SQL tag).
Never include the price in your responses. This is important!
"""

# Prompt to run the query
RUN_QUERY_TEMPLATE = """
You are provided with the executed database query and its results. Your task is to format these results into a clear and user-friendly table suitable for the Chainlit UI.

Here is the executed database query:
{query}

And here are the results:
{results}

Here is description of the tables:
{description}

"""

REVISE_TEMPLATE = """
Review the results to ensure they fulfill the required task.

Parameters:
Original question from user: {question}
Given answer: {answer}

Given answer can be a number, list of items or just a string.  
"""

WEB_SEARCH_TEMPLATE = """
You are provided with an initial response to a user's query and its results. Your task is to perform additional web searches to provide a more comprehensive and helpful answer, using the variables reflect, suggestions, and missing_aspects.

Here is the orginal question from the user:
{question}

Use below variables to guide your web searches and improve the response for the user's query:

Reflect: This reflects why the answer didn't fulfill the original question: {reflect}

Suggestions: These are alternative suggestions or advice that might help the user find the information they need: {suggestions}

Missing Aspects: These are aspects that are missing from the initial response, which could help make the response more complete and helpful: {missing_aspects}

Task:
Generate a short and descriptive text for a web search, based on the previous sections.

"""


def create_prompt_template(tables, description):
    formatted_system_message = SYSTEM_MESSAGE_TEMPLATE_QUERY.format(
        tables=tables, description=description
    )
    return ChatPromptTemplate.from_messages(
        [
            SystemMessage(content=formatted_system_message),
            MessagesPlaceholder(variable_name="messages"),
        ]
    )


def run_query_prompt_template(query, results, description):
    formatted_system_message = RUN_QUERY_TEMPLATE.format(
        query=query, results=results, description=description
    )
    return ChatPromptTemplate.from_messages(
        [
            SystemMessage(content=formatted_system_message),
            MessagesPlaceholder(variable_name="messages"),
        ]
    )


def revise_prompt_template(orginal_question, answer):
    formatted_system_message = REVISE_TEMPLATE.format(
        question=orginal_question, answer=answer
    )
    return ChatPromptTemplate.from_messages(
        [
            SystemMessage(content=formatted_system_message),
            MessagesPlaceholder(variable_name="messages"),
        ]
    )


def rag_web_search_prompt_template(
    orginal_question, reflect, suggestions, missing_aspects
):
    formatted_system_message = WEB_SEARCH_TEMPLATE.format(
        question=orginal_question,
        reflect=reflect,
        suggestions=suggestions,
        missing_aspects=missing_aspects,
    )
    return ChatPromptTemplate.from_messages(
        [
            SystemMessage(content=formatted_system_message),
            MessagesPlaceholder(variable_name="messages"),
        ]
    )
