import json
from decimal import Decimal
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


# ef format_query_results(results):
#   print("format_query_results")
#   if not results:
#       return "No results found."
#   elif len(results) == 1 and isinstance(results[0], tuple) and len(results[0]) == 1:
#       return results[0][0]
#   else:
#       return "\n".join([", ".join(map(str, row)) for row in results])


def format_query_results(results):
    def converter(val):
        if isinstance(val, Decimal):
            return float(val)
        return val

    if not results:
        return json.dumps({"error": "No results found."})

    # Single row
    if len(results) == 1:
        row = results[0]
        if len(row) == 1:
            return json.dumps(converter(row[0]))
        return json.dumps([converter(item) for item in row])

    # Multiple rows
    return json.dumps([
        [converter(item) for item in row]
        for row in results
    ])
