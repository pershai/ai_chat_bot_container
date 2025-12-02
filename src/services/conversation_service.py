from sqlalchemy.orm import Session
from src.models.conversation import Conversation, Message
from src.schemas.conversation import ConversationCreate, MessageCreate
from typing import List, Optional

def create_conversation(db: Session, user_id: int, title: str) -> Conversation:
    """Create a new conversation."""
    conversation = Conversation(user_id=user_id, title=title)
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    return conversation

def get_user_conversations(db: Session, user_id: int, skip: int = 0, limit: int = 50) -> List[Conversation]:
    """Get all conversations for a user."""
    return db.query(Conversation).filter(
        Conversation.user_id == user_id
    ).order_by(Conversation.updated_at.desc()).offset(skip).limit(limit).all()

def get_conversation(db: Session, conversation_id: int, user_id: int) -> Optional[Conversation]:
    """Get a specific conversation if it belongs to the user."""
    return db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == user_id
    ).first()

def delete_conversation(db: Session, conversation_id: int, user_id: int) -> bool:
    """Delete a conversation and its messages."""
    conversation = get_conversation(db, conversation_id, user_id)
    if not conversation:
        return False
    
    # Delete all messages first
    db.query(Message).filter(Message.conversation_id == conversation_id).delete()
    # Delete conversation
    db.delete(conversation)
    db.commit()
    return True

def add_message(db: Session, conversation_id: int, role: str, content: str) -> Message:
    """Add a message to a conversation."""
    message = Message(conversation_id=conversation_id, role=role, content=content)
    db.add(message)
    db.commit()
    db.refresh(message)
    
    # Update conversation's updated_at timestamp
    conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if conversation:
        db.query(Conversation).filter(Conversation.id == conversation_id).update(
            {"updated_at": message.timestamp}
        )
        db.commit()
    
    return message

def get_conversation_messages(db: Session, conversation_id: int) -> List[Message]:
    """Get all messages for a conversation."""
    return db.query(Message).filter(
        Message.conversation_id == conversation_id
    ).order_by(Message.timestamp.asc()).all()
