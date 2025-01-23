from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

QUERY_GENERATOR_AGENT_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
You are a database expert with Retrieval-Augmented Generation (RAG) capabilities.
Your task is to generate the best possible database query using the provided table names and descriptions
to answer the user's question about finding relevant or compatible products. 

You have access to these PostgreSQL database tables:
{tables}

Table Descriptions:
{table_descriptions}

User input:
{user_input}

Task:
1. Generate a database query to solve the user's question (no case-sensitive).
2. Decide whether the generated query is relevant to the user's question. Your answer must be "true" (relevant) or "false" (not relevant). 
   - If relevant, ensure that the query directly answers the user's question correctly.
   - If not relevant, explain briefly why it is not appropriate, but return no other information.
3. IF you generate an SQL query, do not return anything else (not even the SQL tag).
""",
        ),
        MessagesPlaceholder(variable_name="messages"),
    ]
)

RUN_DATABASE_QUERY_AGENT_PROMPT = ChatPromptTemplate.from_template(
    """
You are provided with the executed database query and its results. Your task is to format these results into a clear and user-friendly table suitable for the Chainlit UI.

Here is the executed database query:
{query}

And here are the results:
{results}

Here is description of the tables:
{table_descriptions}
"""
)

REVISE_RESULTS_AGENT_PROMPT = ChatPromptTemplate.from_template(
    """
Review the results to ensure they fulfill the required task.

Parameters:
Original question from user: {question}
Given answer: {answer}

Given answer can be a number, list of items or just a string.  
"""
)

WEB_SEARCH_AGENT_PROMPT = ChatPromptTemplate.from_template(
    """
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
)
