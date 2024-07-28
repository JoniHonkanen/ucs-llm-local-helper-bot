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

# Reflection schema    
class Reflection(BaseModel):
    missing: str = Field(description="Critique of what is missing.")
    superfluous: str = Field(description="Critique of what is superfluous.") #superfluous -> unnecessary information

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
    

class WebSearchSchema(BaseModel):
    answer: str = Field(description="The answer to the question.")
    reflection: Reflection = Field(description="Your reflection on the initial answer.")
    search_queries: List[str] = Field(
        description="1-3 search queries to research information and improve your answer."
    )
