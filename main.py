"""
FastAPI RAG application using Azure OpenAI and Azure AI Search

This sample app demonstrates how to build a RAG (Retrieval Augmented Generation) application
that combines the power of Azure OpenAI with Azure AI Search to create an AI assistant
that answers questions based on your own data.

Key components:
1. FastAPI web framework for the backend API
2. Azure OpenAI for AI chat completions
3. Azure AI Search for document retrieval
4. Pydantic for configuration and data validation
5. Bootstrap and JavaScript for the frontend UI
"""
import os
import logging
import uvicorn
from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

from app.models.chat_models import ChatRequest

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Import the RAG chat service after logging to capture any initialization logs
from app.services.rag_chat_service import rag_chat_service

# Create FastAPI app
app = FastAPI(
    title="FastAPI RAG with Azure OpenAI and Azure AI Search",
    description="A FastAPI application that demonstrates retrieval augmented generation using Azure OpenAI and Azure AI Search.",
    version="1.0.0",
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Set up template directory
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def get_home(request: Request):
    """
    Serve the main chat interface
    """
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/api/chat/completion")
async def chat_completion(chat_request: ChatRequest):
    """
    Process a chat completion request with RAG capabilities
    
    This endpoint:
    1. Receives the chat history from the client
    2. Passes it to the RAG service for processing
    3. Returns AI-generated responses with citations
    4. Handles errors gracefully with user-friendly messages
    """
    try:
        if not chat_request.messages:
            raise HTTPException(status_code=400, detail="Messages cannot be empty")
        
        # Get chat completion from RAG service
        openai_response = await rag_chat_service.get_chat_completion(chat_request.messages)
        
        # Extract response content and citations
        response_content = openai_response.choices[0].message.content
        citations = []
        
        # Extract citations from the context if available
        if (hasattr(openai_response.choices[0].message, 'context') and 
            openai_response.choices[0].message.context and 
            'citations' in openai_response.choices[0].message.context):
            citations = openai_response.choices[0].message.context['citations']
        
        # Return formatted response for frontend
        return {
            "response": response_content,
            "citations": citations
        }
        
    except Exception as e:
        error_str = str(e).lower()
        logger.error(f"Error in chat completion: {str(e)}")
        
        # Handle specific error types with friendly messages
        if "rate limit" in error_str or "capacity" in error_str or "quota" in error_str:
            return {
                "response": "The AI service is currently experiencing high demand. Please wait a moment and try again.",
                "citations": []
            }
        else:
            # Return a standard error response for all other errors
            return {
                "response": f"An error occurred: {str(e)}",
                "citations": []
            }


@app.get("/api/health")
async def health_check():
    """
    Health check endpoint
    """
    return {"status": "ok"}


if __name__ == "__main__":
    # This lets you test the application locally with Uvicorn
    # For production deployment, use a proper ASGI server like Gunicorn
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
