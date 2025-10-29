from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from app.core.database import get_db
from app.models.user import User
from app.models.conversation import Conversation, Message
from app.schemas.conversation import (
    ConversationCreate,
    ConversationUpdate,
    ConversationResponse,
    MessageCreate,
    MessageResponse,
    ConversationWithMessageCount
)
from app.api.endpoints.auth import get_current_active_user

router = APIRouter()


@router.get("", response_model=List[ConversationResponse])
async def get_conversations(
    assistant_type: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get all conversations for current user"""
    query = db.query(Conversation).filter(Conversation.user_id == current_user.id)
    
    if assistant_type:
        query = query.filter(Conversation.assistant_type == assistant_type)
    
    conversations = query.order_by(Conversation.updated_at.desc()).all()
    return conversations


@router.post("", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    conversation: ConversationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new conversation"""
    db_conversation = Conversation(
        user_id=current_user.id,
        assistant_type=conversation.assistant_type,
        title=conversation.title
    )
    
    db.add(db_conversation)
    db.commit()
    db.refresh(db_conversation)
    
    return db_conversation


@router.get("/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get a specific conversation with messages"""
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id
    ).first()
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    return conversation


@router.put("/{conversation_id}", response_model=ConversationResponse)
async def update_conversation(
    conversation_id: int,
    conversation_update: ConversationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update conversation title"""
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id
    ).first()
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    if conversation_update.title:
        conversation.title = conversation_update.title
    
    db.commit()
    db.refresh(conversation)
    
    return conversation


@router.delete("/{conversation_id}")
async def delete_conversation(
    conversation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete a conversation"""
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id
    ).first()
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    db.delete(conversation)
    db.commit()
    
    return {"message": "Conversation deleted successfully"}


@router.post("/{conversation_id}/messages", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def add_message(
    conversation_id: int,
    message: MessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Add a message to a conversation"""
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id
    ).first()
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    db_message = Message(
        conversation_id=conversation_id,
        role=message.role,
        content=message.content
    )
    
    db.add(db_message)
    
    # Update conversation title from first message if needed
    if conversation.title == "New conversation" and message.role == "user":
        conversation.title = message.content[:50] + "..." if len(message.content) > 50 else message.content
    
    db.commit()
    db.refresh(db_message)
    
    return db_message


@router.get("/stats/user", response_model=dict)
async def get_user_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get conversation statistics for current user"""
    total_conversations = db.query(func.count(Conversation.id)).filter(
        Conversation.user_id == current_user.id
    ).scalar()
    
    total_messages = db.query(func.count(Message.id)).join(Conversation).filter(
        Conversation.user_id == current_user.id
    ).scalar()
    
    messages_by_assistant = db.query(
        Conversation.assistant_type,
        func.count(Message.id).label('count')
    ).join(Message).filter(
        Conversation.user_id == current_user.id
    ).group_by(Conversation.assistant_type).all()
    
    return {
        "total_conversations": total_conversations,
        "total_messages": total_messages,
        "messages_by_assistant": {item[0]: item[1] for item in messages_by_assistant}
    }
