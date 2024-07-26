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


class SearchedItem(BaseModel):
    name: str = Field(description="The name of the item")
    quantity: int = Field(description="The quantity of the searched result")
    info: str = Field(description="The information of the searched ")


class CreateDatabaseQyerySchema(BaseModel):
    query: str = Field(description="Used database query without anything else")
    info: str = Field(description="Why the query was used")
    is_correct: str = Field(
        description="Does this answer the question correctly? Yes/No"
    )


class AfterQuerySchema(BaseModel):
    info: str = Field(description="The information after running the query")
    search_result: List[SearchedItem] = Field(
        description="The search result for the answer"
    )
    require_more_info: str = Field("Do you require more information? Yes/No")
    
class AfterQuerySchema2(BaseModel):
    formatted_response: str = Field(description="""Your formatted response should include:
- A clear and concise table displaying key data points
- Use of markdown or other suitable formatting for readability
- Use real table names and column names where possible

Use markdown to format the table / answers.""")
    info: str = Field(description="The information after running the query")
    result: str = Field(description="The search result for the answer")
    require_more_info: bool = Field(description="Are you satisfied with the result? Answer as boolean")
