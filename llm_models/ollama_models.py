# model for ollama
from langchain_community.chat_models import ChatOllama


def get_ollama_llm(llm_choice):
    #llm_choice example = "Ollama - llama3"
    #So we want to extract the model name from the string (after the last "-")
    try:
        extracted_llm_name = llm_choice.split(" - ")[-1]
        models = {
            "llama3": "llama3",
            "zephyr": "zephyr",
            "gemma:2b": "gemma:2b",
            "llava": "llava",
        }
        model_name = models.get(extracted_llm_name, "llama3")
    except Exception as e:
        print(f"An error occurred: {e}")
        model_name = "llama3"  # Default model in case of an error

    return ChatOllama(
        model=model_name,
        temperature=0,
    )
