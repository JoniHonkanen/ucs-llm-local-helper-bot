from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers.openai_tools import (
    JsonOutputToolsParser,
    PydanticToolsParser,
)

from schemas import Answer

# For the testing, we will use the OpenAI API to generate the answer


load_dotenv()
# Chains used in the graph
llm = ChatOpenAI(model="gpt-3.5-turbo-0125")
parser = JsonOutputToolsParser(return_id=True)  # transform it from json to dictionary
parser_pydantic = PydanticToolsParser(tools=[Answer])

# this is the prompt template that will be used to generate the prompt
prompt_template = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """You are an advanced language model with Retrieval-Augmented Generation (RAG) capabilities. 
Just answer the human question
""",
        ),
        MessagesPlaceholder(variable_name="messages"),
    ]
)

# HERE IS EXAMPLE HOW TO USE CHEMA
first_responder = prompt_template.partial(
    first_instruction="Provide a detailed ~50 word answer."
)


# Function to create the first responder
def create_first_responder(instruction):
    prompt = prompt_template.partial(instruction=instruction)
    response = prompt | llm.bind_tools(tools=[Answer], tool_choice="Answer")
    return response


# Modified query_generator_agent to use prompt template
def query_generator_agent(instruction):
    # Format the instruction using the prompt template
    formatted_prompt = prompt_template.format(content=[instruction])

    # Invoke the language model with the formatted prompt
    # response = llm.invoke(formatted_prompt)
    response = llm.bind_tools(tools=[Answer], tool_choice="Answer")

    return response


if __name__ == "__main__":
    human_message = HumanMessage(content="What is bengla cat?")
    chain = (
        first_responder
        | llm.bind_tools(tools=[Answer], tool_choice="Answer")
        | parser_pydantic
    )
    res = chain.invoke(input={"messages": [human_message]})
    print(res)
