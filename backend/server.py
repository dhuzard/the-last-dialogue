from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
import uuid
import uvicorn
from typing import Dict, Any, List

from graph import app as graph_app

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="The Last Dialogue API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store for active sessions (in memory for scaffolding, use Redis/DB in prod)
# Actually LangGraph MemorySaver handles the threads if we use the same checkpointer instance.
# Since `graph.py` instantiates `memory = MemorySaver()`, it is persistent in memory *for the process process*.

class StartSessionRequest(BaseModel):
    player_1_name: str = "Persona A"
    player_2_name: str = "Persona B"

class TurnRequest(BaseModel):
    thread_id: str
    human_intent: str

@app.post("/start_session")
async def start_session(request: StartSessionRequest):
    """
    Starts a new game session.
    Initializing the graph with the first player.
    """
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    
    initial_state = {
        "active_player": request.player_1_name,
        "messages": [],
        "manuscript": ""
    }
    
    # Run the graph until the first interrupt (waiting for input)
    # We use invoke which will stop at the interrupt
    # The graph starts at START -> human_input -> interrupt
    # So it will stop almost immediately, waiting for the first input.
    events = graph_app.invoke(initial_state, config)
    
    return {
        "thread_id": thread_id,
        "status": "started",
        "current_state": graph_app.get_state(config).values
    }

@app.post("/turn")
async def submit_turn(request: TurnRequest):
    """
    Submits a human intent to resume the graph.
    """
    thread_id = request.thread_id
    config = {"configurable": {"thread_id": thread_id}}
    
    # Check if thread exists logic can be added here
    
    # Resume the graph with the human intent
    # We use Command(resume=value) to provide the value to the `interrupt` function
    from langgraph.types import Command
    
    # invoke with Command resumes execution from the interrupt
    events = graph_app.invoke(
        Command(resume=request.human_intent), 
        config
    )
    
    # Get the new state after execution pauses again (at the next interrupt)
    final_state = graph_app.get_state(config).values
    
    return {
        "thread_id": thread_id,
        "status": "paused", # It's always paused at interrupt after invoke returns
        "manuscript": final_state.get("manuscript", ""),
        "active_player": final_state.get("active_player"),
        "research_notes": final_state.get("research_notes", "")
    }

@app.get("/state/{thread_id}")
async def get_state(thread_id: str):
    config = {"configurable": {"thread_id": thread_id}}
    return graph_app.get_state(config).values

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
