from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from src.agents.state import AgentState, SynthesizedStory
from src.config.config import LLM, LLM_TEMPERATURE

from src.logger.custom_logger import get_logger
logger = get_logger(__name__)

# --- NODES (The Agents) ---
def researcher_agent(state: AgentState):
    logger.info("🧠 Researcher Agent: Synthesizing articles...")
    
    # Initialize Groq LLM locally (Lazy Initialization)
    researcher_llm = ChatGroq(temperature=LLM_TEMPERATURE, model_name=LLM)
    structured_researcher = researcher_llm.with_structured_output(SynthesizedStory)
    
    articles = state["raw_articles"]
    feedback = state.get("editor_feedback")
    
    # Format the articles for the prompt
    context = ""
    for art in articles:
        context += f"ID: {art['id']}\nTitle: {art['title']}\nContent: {art['content'][:1000]}...\n\n"

    # If the editor rejected a previous draft, we include the feedback
    feedback_prompt = f"\nEDITOR FEEDBACK TO ADDRESS: {feedback}" if feedback else ""

    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are an expert AI News Analyst. Synthesize the provided articles into a single, cohesive daily digest. "
                   "Only include facts present in the articles. You MUST return the IDs of the articles you used."),
        ("user", f"Here are the articles:\n{context}{feedback_prompt}")
    ])
    
    chain = prompt | structured_researcher
    result = chain.invoke({})
    
    return {
        "draft_story": result,
        "iteration_count": state.get("iteration_count", 0) + 1
    }

def editor_agent(state: AgentState):
    logger.info("🧐 Editor Agent: Reviewing draft...")
    
    # Initialize Groq LLM locally (Lazy Initialization)
    editor_llm = ChatGroq(temperature=LLM_TEMPERATURE, model_name=LLM)
    
    draft = state["draft_story"]
    articles = state["raw_articles"]
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a strict Managing Editor. Review the draft story against the provided source articles. "
                   "Look for hallucinations, bias, or poor formatting. "
                   "If it is perfect, reply with exactly 'APPROVED'. "
                   "If it needs work, provide 1-2 sentences of specific feedback."),
        ("user", f"DRAFT TITLE: {draft.title}\n\nDRAFT SUMMARY:\n{draft.summary}\n\nDo you approve?")
    ])
    
    chain = prompt | editor_llm
    result = chain.invoke({})
    feedback = result.content.strip()
    
    if "APPROVED" in feedback.upper():
        logger.info("✅ Editor Agent: Story Approved!")
        return {"is_approved": True, "editor_feedback": None}
    else:
        logger.warning(f"❌ Editor Agent: Revision needed - {feedback}")
        return {"is_approved": False, "editor_feedback": feedback}