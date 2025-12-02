from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.core.security import get_current_user
from src.models.user import User
from src.schemas.chat import ChatRequest, ChatResponse
from src.services import chat_service

router = APIRouter(tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        # Pass user_id, db, and conversation_id to chat service
        # The service handles history loading and message saving
        response = await chat_service.process_chat(
            request.message, current_user.id, db, request.conversation_id
        )

        return ChatResponse(response=response)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
