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

from dotenv import load_dotenv
load_dotenv()

# --- Nodes ---

def get_human_input(state: GraphState):
    """
    Breakpoint node. Waits for user input via Command(resume=...).
    """
    human_intent = interrupt(f"Waiting for input from {state['active_player']}")
    return {"human_intent": human_intent}

def research_agent(state: GraphState):
    """
    Research topics based on human intent.
    """
    human_intent = state["human_intent"]
    print(f"Researching: {human_intent}")
    
    # Initialize basic LLM
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    # Search Tools
    # Note: Requires TAVILY_API_KEY env var
    tools = []
    try:
        tavily = TavilySearchResults(max_results=2)
        tools.append(tavily)
    except Exception:
        print("Tavily not configured, skipping")

    # Arxiv
    arxiv = ArxivQueryRun(api_wrapper=ArxivAPIWrapper())
    tools.append(arxiv)

    # Create a researcher agent
    # For simplicity/robustness in scaffolding, we just do a direct search/summarize chain 
    # instead of a full ReAct agent loop which might be slow/complex.
    
    search_query_prompt = f"Generate 1 specific search query to find scientific or philosophical support for this argument: '{human_intent}'. Return ONLY the query."
    search_query = llm.invoke(search_query_prompt).content.strip().replace('"', '')
    
    print(f"Executing Search Query: {search_query}")
    
    try:
        # Try Tavily first/primary
        # We manually invoke tool to avoid agent overhead for this scoped task
        if os.environ.get("TAVILY_API_KEY"):
            tavily_res = TavilySearchResults(max_results=2).invoke(search_query)
            # Tavily returns a list of dictionaries
            search_content = "\n".join([f"- {r.get('content', '')}" for r in tavily_res])
        else:
            # Fallback mock if no API key (prevent crash during scaffolding demo)
            search_content = f"Simulated search results for: {search_query}. (Set TAVILY_API_KEY for real results)"
    except Exception as e:
        search_content = f"Search error: {e}"

    return {"research_notes": search_content}

def structurer_agent(state: GraphState):
    """
    Structures the argument based on research and persona.
    """
    active_player = state["active_player"]
    research = state["research_notes"]
    intent = state["human_intent"]
    
    llm = ChatOpenAI(model="gpt-4o", temperature=0.7)
    
    persona_prompt = ""
    if active_player == "Persona A":
        persona_prompt = "You are The Biocentrist. You believe in the supremacy of organic chaos, empathy, and biological mastery. You despise sterile metal."
    else:
        persona_prompt = "You are The Technocentrist. You believe in the perfection of silicon, mechanical immortality, and cold logic. You despise rotting flesh."
        
    prompt = f"""{persona_prompt}
    
    Your goal is to structure a short philosophical rebuttal argument based on the Director's Intent: "{intent}"
    
    Use these research notes for credibility:
    {research}
    
    Output a structured draft (bullet points) for the argument. Call out specific concepts to include.
    """
    
    response = llm.invoke(prompt)
    return {"draft": response.content}

def novelist_agent(state: GraphState):
    """
    Writes the prose.
    """
    draft = state["draft"]
    active_player = state["active_player"]
    
    llm = ChatOpenAI(model="gpt-4o", temperature=0.8)
    
    prompt = f"""You are a master sci-fi novelist writing 'The Last Dialogue'.
    
    Current Speaker: {active_player}
    
    Draft Plan:
    {draft}
    
    Write a single, atmospheric paragraph (approx 100-150 words) of dialogue or monologue for {active_player}. 
    Style: Lush, haunting, high-concept sci-fi.
    Do NOT include "Persona A:" labels. Just the prose.
    """
    
    response = llm.invoke(prompt)
    manuscript_chunk = f"\n\n**[{active_player}]**\n{response.content}"
    
    return {"manuscript": manuscript_chunk}

def state_update(state: GraphState):
    """
    Updates the active player.
    """
    current_player = state["active_player"]
    next_player = "Persona B" if current_player == "Persona A" else "Persona A"
    return {"active_player": next_player}

def supervisor(state: GraphState):
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
workflow.add_edge("state_update", "human_input")

# Checkpointer
message_checkpoint = MemorySaver()

# Compile
app = workflow.compile(checkpointer=message_checkpoint)
