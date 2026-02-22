import os
import pytest
from src.agents.graph import app
from src.agents.state import SynthesizedStory
from dotenv import load_dotenv
load_dotenv()

# Pro-tip: We add a safeguard. If the CI environment is missing the API key, 
# the test will be marked as "skipped" instead of "failed".
@pytest.mark.skipif(not os.getenv("GROQ_API_KEY"), reason="GROQ_API_KEY is not set in environment")
def test_workflow_graph_execution():
    """
    Integration test to ensure the Multi-Agent workflow can successfully 
    read articles, generate a draft, and pass the editor's review.
    """
    # 1. Arrange: Setup the initial state with mock database records
    initial_state = {
        "raw_articles": [
            {
                "id": "1",
                "title": "AI hits a new milestone",
                "content": "Artificial intelligence has reached a new milestone in reasoning capabilities according to a recent paper. This will change how developers write code."
            },
            {
                "id": "2",
                "title": "The future of LLMs",
                "content": "Large language models are expected to become more efficient and smaller in size over the coming years, making edge-computing a reality."
            }
        ],
        "draft_story": None,
        "editor_feedback": None,
        "is_approved": False,
        "iteration_count": 0
    }
    
    # 2. Act: Invoke the LangGraph workflow
    final_state = app.invoke(initial_state)
    
    # 3. Assert: Validate the state transitions and outputs FIRST
    assert final_state is not None, "Workflow returned None"
    
    # The workflow should increment the iteration count
    assert final_state["iteration_count"] > 0, "Iteration count did not increment"
    
    # Validate the Researcher Agent's output structure
    draft = final_state.get("draft_story")
    assert draft is not None, "Researcher Agent failed to produce a draft"
    assert isinstance(draft, SynthesizedStory), "Draft is not a SynthesizedStory Pydantic object"
    assert len(draft.title) > 0, "Generated title is empty"
    assert len(draft.summary) > 0, "Generated summary is empty"
    
    # Validate that the Editor Agent ran and made a decision
    # (It will either be True if approved, or False if rejected and hit max iterations)
    assert isinstance(final_state["is_approved"], bool)

    # 4. Only print output if all assertions passed safely
    print("\n\n" + "="*50)
    print("🤖 AI NEWS DIGEST OUTPUT")
    print("="*50)
    
    print(f"\nTITLE: {draft.title}\n")
    print(f"SUMMARY:\n{draft.summary}\n")
    print(f"SOURCES USED: {draft.source_article_ids}\n")
    
    print(f"Total Iterations (Editor Revisions): {final_state['iteration_count']}")
    print(f"Approved by Editor? {final_state['is_approved']}")
    print("="*50 + "\n")