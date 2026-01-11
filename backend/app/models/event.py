from sqlalchemy import Column, Integer, String, Text, DateTime, Date, Boolean, Float
from sqlalchemy.sql import func
from app.core.database import Base


class Event(Base):
    __tablename__ = "events"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False, index=True)
    description = Column(Text)
    event_type = Column(String(100))  # concert, theater, sports, exhibition, etc.
    venue_name = Column(String(255))
    venue_address = Column(Text)
    latitude = Column(Float)
    longitude = Column(Float)
    event_date = Column(DateTime)
    end_date = Column(DateTime)
    event_url = Column(String(1000), unique=True)  # Link to bubilet page
    image_url = Column(String(1000))
    price_info = Column(String(255))
    is_active = Column(Boolean, default=True)  # Event hasn't passed
    source = Column(String(50), default='bubilet')  # Where we scraped it from
    external_id = Column(String(255))  # Bilet ID from bubilet
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<Event {self.title}>"
