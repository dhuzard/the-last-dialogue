import os
import operator
from typing import Annotated, List, TypedDict, Union, Literal
from typing_extensions import TypedDict

from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_community.utilities import ArxivAPIWrapper
from langchain_community.tools.arxiv.tool import ArxivQueryRun
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_core.tools import tool
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command, interrupt

# --- State Definition ---
class GraphState(TypedDict):
    messages: Annotated[List[BaseMessage], operator.add]
    active_player: str  # "Persona A" or "Persona B"
    human_intent: str
    research_notes: str
    draft: str
    manuscript: str  # The full novel so far

# --- Nodes ---

def get_human_input(state: GraphState):
    """
    Breakpoint node. Waits for user input via Command(resume=...).
    """
    # The interrupt value is returned to the client to indicate what we are waiting for.
    human_intent = interrupt(f"Waiting for input from {state['active_player']}")
    
    return {
        "human_intent": human_intent
    }

def research_agent(state: GraphState):
    """
    Research topics based on human intent.
    """
    human_intent = state["human_intent"]
    print(f"Researching: {human_intent}")
    
    # Initialize tools
    tavily = TavilySearchResults(max_results=3)
    arxiv = ArxivQueryRun(api_wrapper=ArxivAPIWrapper())
    
    # Simple simulation of research for now, or use an LLM to call tools.
    # For scaffolding, we can just call the search directly or define an agent.
    # Let's use a simple LLM call that *can* use tools.
    
    # Note: In a real app with dynamic keys, we'd initialize the LLM here using
    # keys passed in `config` or state. For scaffolding, we'll assume env vars or mocks.
    # We will just simulate the "Agent" behavior with a direct call for simplicity
    # or use a prebuilt agent if keys are available.
    
    search_results = f"Research findings for '{human_intent}':\n"
    try:
        # This will fail without keys, so we wrap in try/except or mock
        # For the scaffolding, we structure the logic.
        search_results += f"- [Mock Tavily Result] relevant to {human_intent}\n"
    except Exception as e:
        search_results += f"Search failed: {e}\n"
        
    return {"research_notes": search_results}

def structurer_agent(state: GraphState):
    """
    Structures the argument based on research and persona.
    """
    active_player = state["active_player"]
    research = state["research_notes"]
    intent = state["human_intent"]
    
    structure = f"Structure for {active_player}:\n"
    structure += f"1. Premise: Based on {intent}\n"
    structure += f"2. Evidence: {research[:50]}...\n"
    structure += f"3. Conclusion: Therefore, {active_player} prevails."
    
    return {"draft": structure}

def novelist_agent(state: GraphState):
    """
    Writes the prose.
    """
    draft = state["draft"]
    active_player = state["active_player"]
    
    # In reality, call LLM here (GPT-4 / Claude)
    prose = f"\n\n[{active_player}'s Turn]\n"
    prose += f"The system hummed. {draft}\n"
    
    return {"manuscript": prose} # Append handled by operator.add if we used it, or we just append manually

def state_update(state: GraphState):
    """
    Updates the active player.
    """
    current_player = state["active_player"]
    next_player = "Persona B" if current_player == "Persona A" else "Persona A"
    return {"active_player": next_player}

def supervisor(state: GraphState):
    """
    Routes execution.
    """
    # Simple linear flow for this turn-based game
    return "research"

# --- Graph Construction ---
workflow = StateGraph(GraphState)

workflow.add_node("human_input", get_human_input)
workflow.add_node("researcher", research_agent)
workflow.add_node("structurer", structurer_agent)
workflow.add_node("novelist", novelist_agent)
workflow.add_node("state_update", state_update)

# Edges
workflow.add_edge(START, "human_input")
workflow.add_edge("human_input", "researcher")
workflow.add_edge("researcher", "structurer")
workflow.add_edge("structurer", "novelist")
workflow.add_edge("novelist", "state_update")
workflow.add_edge("state_update", "human_input") # Loop back for next turn

# Checkpointer
message_checkpoint = MemorySaver()

# Compile
app = workflow.compile(checkpointer=message_checkpoint)
