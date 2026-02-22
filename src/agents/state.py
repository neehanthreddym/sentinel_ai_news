from typing import TypedDict, List, Annotated
from pydantic import BaseModel, Field
import operator

# Define the strict JSON structure the Researcher should output.
# This prevents hallucinations and ensures our API has clean data.
class SynthesizedStory(BaseModel):
    title: str = Field(description="A professional, engaging title for the daily digest.")
    summary: str = Field(description="The comprehensive synthesized news story in Markdown format.")
    source_article_ids: List[str] = Field(description="List of database UUIDs of the articles referenced.")

# Define the State of the Graph
class AgentState(TypedDict):
    raw_articles: List[dict]      # The input data from database
    draft_story: SynthesizedStory | None  # The output from the Researcher
    editor_feedback: str | None   # The critique from the Editor
    is_approved: bool             # The guardrail flag
    iteration_count: int          # To prevent infinite loops