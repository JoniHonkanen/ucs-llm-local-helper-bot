from typing import List
from langchain_core.pydantic_v1 import BaseModel, Field, Extra, validator

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
class CreateDatabaseQuerySchema(BaseModel):
    query: str = Field(
        description="Used database query without anything else. Remember, newer show prices or other sensitive information in the query"
    )
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

    class Config:
        extra = Extra.forbid  # Forbid extra fields not defined in the model


# Reflection schema
class ReflectionSchema(BaseModel):
    done: bool = Field(
        description="The generated answer fulfills the original question? True = Yes, False = No"
    )
    reflect: str = Field(
        description="Why the answer fulfills / does not fulfill the question"
    )
    suggestions: str = Field(
        description="Suggestions for how the query or answer can be improved",
        default="",
    )
    missing_aspects: str = Field(
        description="Specific aspects or information that are missing or could be better addressed",
        default="",
    )
    relevance: float = Field(
        description="A score from 0 to 1 indicating the relevance of the answer to the original question"
    )

    # Set the optional fields to empty string if the done field is True
    @validator("suggestions", "missing_aspects", pre=True, always=True)
    def set_optional_fields(cls, v, values, field):
        if values.get("done", False):
            return ""
        return v


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
    web_search: str = Field(description="Generated web search query")
    #search_queries: List[str] = Field(
    #    description="1-3 search queries to research information and improve your answer."
    #)
