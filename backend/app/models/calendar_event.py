from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class CalendarEvent(Base):
    """Model for calendar events extracted from emails"""
    __tablename__ = "calendar_events"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    event_date = Column(DateTime(timezone=True), nullable=False, index=True)
    end_date = Column(DateTime(timezone=True))
    location = Column(String(255))
    event_type = Column(String(50), index=True)  # exam, deadline, meeting, class, assignment, etc.
    priority = Column(String(20), default='normal')  # low, normal, high, urgent
    source = Column(String(50), default='email')  # email, manual, imported
    email_id = Column(String(255), index=True)  # Original email message ID
    email_subject = Column(Text)
    raw_email_content = Column(Text)  # Store original email content
    llm_extraction_data = Column(JSON)  # Store full LLM response
    is_confirmed = Column(Boolean, default=False, index=True)  # User can confirm/reject
    reminder_sent = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationship to user
    user = relationship("User", back_populates="calendar_events")
