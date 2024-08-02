# format response when using Ollama
def format_ollama_response(response):
    if "data" in response:
        formatted_response = "\n".join([str(item) for item in response["data"]])
    else:
        formatted_response = str(response)
    return formatted_response


# format response when using OpenAI
def format_openai_response(response):
    if "choices" in response and len(response["choices"]) > 0:
        formatted_response = response["choices"][0]["text"].strip()
    else:
        formatted_response = str(response)
    return formatted_response


# Format the query results (used in agents.py)
""" def format_query_results(results):
    print("format_query_results")
    if not results:
        return "No results found."
    elif len(results) == 1 and isinstance(results[0], tuple) and len(results[0]) == 1:
        return f"Query Result: {results[0][0]}"
    else:
        return "\n".join([str(row) for row in results]) """


def format_query_results(results):
    print("format_query_results")
    if not results:
        return "No results found."
    elif len(results) == 1 and isinstance(results[0], tuple) and len(results[0]) == 1:
        return results[0][0]
    else:
        return "\n".join([", ".join(map(str, row)) for row in results])