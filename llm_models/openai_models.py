from langchain_openai import ChatOpenAI

def get_openai_llm():
    return ChatOpenAI(model="gpt-4o-mini")