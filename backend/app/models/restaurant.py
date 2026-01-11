from sqlalchemy import Column, Integer, String, Float, Text, DateTime, JSON
from sqlalchemy.sql import func
from app.core.database import Base


class Restaurant(Base):
    __tablename__ = "restaurants"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    cuisine_type = Column(String(100))  # Turkish, Italian, Fast Food, etc.
    category = Column(String(100))  # restaurant, cafe, fast_food, etc.
    address = Column(Text)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    phone = Column(String(50))
    website = Column(String(500))
    opening_hours = Column(JSON)  # Store hours as JSON
    price_range = Column(String(20))  # $, $$, $$$, $$$$
    rating = Column(Float)
    distance_from_campus = Column(Float)  # in km
    tags = Column(JSON)  # vegetarian, halal, outdoor seating, etc.
    description = Column(Text)
    osm_id = Column(String(100), unique=True)  # OpenStreetMap ID
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<Restaurant {self.name}>"
