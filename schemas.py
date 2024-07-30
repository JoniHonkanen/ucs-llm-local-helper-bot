from typing import List
from langchain_core.pydantic_v1 import BaseModel, Field

# Schema - define the structure of the answer to the question
# Example answer:
"""
{
    "answer": "Here is list of search results",
    "is_correct": "True",
    "search_result": [
        {
            "name": "item1",
            "quantity": 1,
            "info": "info1"
        },
        {
            "name": "item2",
            "quantity": 2,
            "info": "info2"
        }
    ]
}
"""


# Schema used for creating the database query
class CreateDatabaseQyerySchema(BaseModel):
    query: str = Field(description="Used database query without anything else")
    info: str = Field(description="Why the query was used")
    is_correct: str = Field(
        description="Does this answer the question correctly? Yes/No"
    )


class AfterQuerySchema(BaseModel):
    formatted_response: str = Field(
        description="""
Your formatted response should include:
- A clear and concise table displaying key data points
- Use of markdown or other suitable formatting for readability
- Use real table names and column names where possible

**Note:** Do not use `\n` within the markdown table, as it breaks the table formatting. Instead, use the pipe `|` symbol to separate columns and create new rows directly.
**Note:** Dont use `\n` for line breaks. Use markdown formatting for line breaks.

For example:
| Parts       | 
|-------------|
| Brake Pads  | 
| Spark Plugs | 
| Gearbox     | 

Use markdown to format the table / answers. """
    )
    response: str = Field(description="Just the straigt response from the database")


# Reflection schema
class ReflectionSchema(BaseModel):
    done: bool = Field(
        description="The generated answer fulfills the original question? True = Yes, False = No"
    )
    reflect: str = Field(
        description="Why the answer fulfills / does not fulfill the question"
    )


# SCHEMAS FROM BELOW NOT USED YET...


class SearchedItem(BaseModel):
    name: str = Field(description="The name of the item")
    quantity: int = Field(description="The quantity of the searched result")
    info: str = Field(description="The information of the searched ")


""" class AfterQuerySchema(BaseModel):
    info: str = Field(description="The information after running the query")
    search_result: List[SearchedItem] = Field(
        description="The search result for the answer"
    )
    require_more_info: str = Field("Do you require more information? Yes/No") """


class WebSearchSchema(BaseModel):
    answer: str = Field(description="The answer to the question.")
    reflection: ReflectionSchema = Field(
        description="Your reflection on the initial answer."
    )
    search_queries: List[str] = Field(
        description="1-3 search queries to research information and improve your answer."
    )
