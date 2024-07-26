#format response when using Ollama
def format_ollama_response(response):
    if "data" in response:
        formatted_response = "\n".join([str(item) for item in response["data"]])
    else:
        formatted_response = str(response)
    return formatted_response

#format response when using OpenAI
def format_openai_response(response):
    if "choices" in response and len(response["choices"]) > 0:
        formatted_response = response["choices"][0]["text"].strip()
    else:
        formatted_response = str(response)
    return formatted_response

