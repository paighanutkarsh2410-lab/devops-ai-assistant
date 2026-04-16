"""Chat API: Natural language queries about the DevOps system."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from models import get_db
from services.nlp_service import NLPQueryHandler

router = APIRouter(prefix="/chat", tags=["chat"])

# Shared handler instance for conversation context
_handlers: dict = {}


class ChatMessage(BaseModel):
    message: str
    session_id: Optional[str] = "default"


class ChatResponse(BaseModel):
    answer: str
    intent: Optional[dict] = None
    timestamp: Optional[str] = None


class SuggestedQuery(BaseModel):
    text: str
    category: str


@router.post("/query", response_model=ChatResponse)
def chat_query(msg: ChatMessage, db: Session = Depends(get_db)):
    """Process a natural language question about the system."""
    session_id = msg.session_id or "default"

    # Get or create handler for session (preserves conversation history)
    if session_id not in _handlers:
        _handlers[session_id] = NLPQueryHandler()

    handler = _handlers[session_id]
    handler.set_db(db)

    result = handler.query(msg.message)

    # Limit active sessions
    if len(_handlers) > 50:
        oldest = list(_handlers.keys())[0]
        del _handlers[oldest]

    return ChatResponse(
        answer=result.get("answer", "I couldn't process that question."),
        intent=result.get("intent"),
        timestamp=result.get("timestamp"),
    )


@router.get("/suggestions", response_model=List[SuggestedQuery])
def get_suggestions():
    """Get suggested queries for the chat interface."""
    return [
        SuggestedQuery(text="System status?", category="status"),
        SuggestedQuery(text="Show recent incidents", category="incidents"),
        SuggestedQuery(text="Any predictions?", category="predictions"),
        SuggestedQuery(text="Cost forecast for next month", category="predictions"),
        SuggestedQuery(text="Why is the API slow?", category="diagnostic"),
        SuggestedQuery(text="Show metrics for api-server", category="metrics"),
        SuggestedQuery(text="How is the system doing?", category="summary"),
        SuggestedQuery(text="List critical incidents", category="incidents"),
    ]
