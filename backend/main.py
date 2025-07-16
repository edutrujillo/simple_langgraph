# FastAPI backend for the Salesforce LangGraph chat application
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn
from langgraph_logic import run_langgraph

# Create FastAPI app
app = FastAPI()

# Enable CORS for all origins (for development/demo purposes)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic model for chat request body
class ChatRequest(BaseModel):
    message: str

# Main chat endpoint: receives user message, runs LangGraph, returns response and MCP log
@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    response = run_langgraph(request.message)
    return JSONResponse(response)

# Run the server if executed directly
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000) 