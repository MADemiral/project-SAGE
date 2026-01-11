from typing import Optional
from pydantic import BaseModel, HttpUrl
from datetime import datetime


class EventBase(BaseModel):
    title: str
    description: Optional[str] = None
    event_type: Optional[str] = None
    venue_name: Optional[str] = None
    venue_address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    event_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    event_url: Optional[str] = None
    image_url: Optional[str] = None
    price_info: Optional[str] = None
    is_active: bool = True
    source: str = 'bubilet'
    external_id: Optional[str] = None


class EventCreate(EventBase):
    pass


class EventUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    event_type: Optional[str] = None
    venue_name: Optional[str] = None
    venue_address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    event_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    event_url: Optional[str] = None
    image_url: Optional[str] = None
    price_info: Optional[str] = None
    is_active: Optional[bool] = None


class Event(EventBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class EventSearchParams(BaseModel):
    event_type: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    venue_name: Optional[str] = None
    is_active: bool = True
    limit: int = 20
