from langgraph.graph import StateGraph, END
from src.agents.state import AgentState
from src.agents.nodes import researcher_agent, editor_agent
from src.logger.custom_logger import get_logger
logger = get_logger(__name__)


# --- EDGES (The Logic Flow) ---
def should_publish(state: AgentState):
    """Routing logic to decide if we loop back to the researcher or finish."""
    if state["is_approved"]:
        return "publish"
    
    # Guardrail: Prevent infinite loops if the LLMs get stuck arguing
    if state["iteration_count"] >= 3:
        logger.warning("⚠️ Max iterations reached. Forcing approval.")
        return "publish"
        
    return "revise"


# --- BUILD THE GRAPH ---
workflow = StateGraph(AgentState)

# Add nodes (Agents)
workflow.add_node("researcher", researcher_agent)
workflow.add_node("editor", editor_agent)

# Set the entry point
workflow.set_entry_point("researcher")

# Connect researcher to editor
workflow.add_edge("researcher", "editor")

# Conditional logic: Editor either approves (END) or rejects (Back to Researcher)
workflow.add_conditional_edges(
    "editor",
    should_publish,
    {
        "publish": END,
        "revise": "researcher"
    }
)

# Compile the graph into an executable application
app = workflow.compile()