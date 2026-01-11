from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
import json
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
from app.services.groq_service import GroqAcademicService

router = APIRouter()

# Initialize Groq service
groq_service = GroqAcademicService()


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
    """Add a message to a conversation and get AI response"""
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id
    ).first()
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    # Save user message
    db_message = Message(
        conversation_id=conversation_id,
        role=message.role,
        content=message.content
    )
    
    db.add(db_message)
    
    # Update conversation title from first user message if needed
    if conversation.title == "New conversation" and message.role == "user":
        conversation.title = message.content[:50] + "..." if len(message.content) > 50 else message.content
    
    db.commit()
    db.refresh(db_message)
    
    # Generate AI response for academic assistant
    if message.role == "user" and conversation.assistant_type == "academic":
        try:
            # Get conversation history (excluding the current user message we just added)
            history_messages = db.query(Message).filter(
                Message.conversation_id == conversation_id
            ).order_by(Message.created_at.asc()).all()
            
            # Format history for Groq (include all messages except the last one we just added)
            conversation_history = [
                {"role": msg.role, "content": msg.content}
                for msg in history_messages[:-1]  # Exclude the just-added message
            ]
            
            # Get AI response
            ai_response = groq_service.chat(
                user_message=message.content,
                conversation_history=conversation_history,
                include_courses=True
            )
            
            # Save AI response
            ai_message = Message(
                conversation_id=conversation_id,
                role="assistant",
                content=ai_response
            )
            
            db.add(ai_message)
            db.commit()
            db.refresh(ai_message)
            
            return ai_message
            
        except Exception as e:
            print(f"Error generating AI response: {e}")
            # If AI fails, still return user message
            pass
    
    # Generate AI response for social assistant
    elif message.role == "user" and conversation.assistant_type == "social":
        try:
            # Get conversation history
            history_messages = db.query(Message).filter(
                Message.conversation_id == conversation_id
            ).order_by(Message.created_at.asc()).all()
            
            # Format history for Groq
            conversation_history = [
                {"role": msg.role, "content": msg.content}
                for msg in history_messages[:-1]
            ]
            
            # Get AI response using social assistant
            ai_response = groq_service.chat_social(
                user_message=message.content,
                conversation_history=conversation_history
            )
            
            # Save AI response
            ai_message = Message(
                conversation_id=conversation_id,
                role="assistant",
                content=ai_response
            )
            
            db.add(ai_message)
            db.commit()
            db.refresh(ai_message)
            
            return ai_message
            
        except Exception as e:
            print(f"Error generating social AI response: {e}")
            # If AI fails, still return user message
            pass
    
    return db_message


@router.post("/{conversation_id}/messages/stream")
async def add_message_stream(
    conversation_id: int,
    message: MessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Add a message and stream AI response (for real-time chat)"""
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == current_user.id
    ).first()
    
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    # Save user message
    db_message = Message(
        conversation_id=conversation_id,
        role=message.role,
        content=message.content
    )
    
    db.add(db_message)
    
    # Update conversation title from first user message
    if conversation.title == "New conversation" and message.role == "user":
        conversation.title = message.content[:50] + "..." if len(message.content) > 50 else message.content
    
    db.commit()
    
    # Stream AI response for academic assistant
    if message.role == "user" and conversation.assistant_type == "academic":
        try:
            # Get conversation history
            history_messages = db.query(Message).filter(
                Message.conversation_id == conversation_id
            ).order_by(Message.created_at.asc()).limit(20).all()
            
            conversation_history = [
                {"role": msg.role, "content": msg.content}
                for msg in history_messages[:-1]
            ]
            
            async def generate():
                full_response = ""
                
                for chunk in groq_service.chat_stream(
                    user_message=message.content,
                    conversation_history=conversation_history,
                    include_courses=True
                ):
                    full_response += chunk
                    yield f"data: {json.dumps({'content': chunk})}\n\n"
                
                # Save complete AI response to database
                ai_message = Message(
                    conversation_id=conversation_id,
                    role="assistant",
                    content=full_response
                )
                db.add(ai_message)
                db.commit()
                
                yield f"data: {json.dumps({'done': True})}\n\n"
            
            return StreamingResponse(
                generate(),
                media_type="text/event-stream"
            )
            
        except Exception as e:
            print(f"Error streaming AI response: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error generating response: {str(e)}"
            )
    
    return {"message": "Message saved", "id": db_message.id}


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
