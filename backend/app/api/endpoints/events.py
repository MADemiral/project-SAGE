from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, or_, and_
from typing import List, Optional
from datetime import datetime

from app.core.database import get_db
from app.models.event import Event
from app.schemas.event import (
    Event as EventSchema,
    EventSearchParams
)
from app.api.endpoints.auth import get_current_active_user
from app.models.user import User

router = APIRouter()


@router.get("", response_model=List[EventSchema])
async def get_events(
    event_type: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    venue_name: Optional[str] = None,
    is_active: bool = True,
    search: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get events with optional filters
    
    - **event_type**: Filter by type (e.g., 'concert', 'theater', 'sports')
    - **start_date**: Show events after this date
    - **end_date**: Show events before this date
    - **venue_name**: Filter by venue
    - **is_active**: Show only active/upcoming events (default: true)
    - **search**: Search in title, description, or venue
    - **limit**: Number of results to return (default: 20, max: 100)
    """
    query = db.query(Event)
    
    # Apply filters
    if is_active:
        query = query.filter(Event.is_active == True)
    
    if event_type:
        query = query.filter(Event.event_type.ilike(f"%{event_type}%"))
    
    if start_date:
        query = query.filter(Event.event_date >= start_date)
    
    if end_date:
        query = query.filter(Event.event_date <= end_date)
    
    if venue_name:
        query = query.filter(Event.venue_name.ilike(f"%{venue_name}%"))
    
    if search:
        search_filter = or_(
            Event.title.ilike(f"%{search}%"),
            Event.description.ilike(f"%{search}%"),
            Event.venue_name.ilike(f"%{search}%")
        )
        query = query.filter(search_filter)
    
    # Order by event date
    query = query.order_by(Event.event_date.asc())
    
    events = query.limit(limit).all()
    return events


@router.get("/{event_id}", response_model=EventSchema)
async def get_event(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get a specific event by ID"""
    event = db.query(Event).filter(Event.id == event_id).first()
    
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    return event


@router.get("/upcoming", response_model=List[EventSchema])
async def get_upcoming_events(
    days: int = Query(30, description="Number of days to look ahead"),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get upcoming events in the next N days"""
    from datetime import timedelta
    
    end_date = datetime.now() + timedelta(days=days)
    
    events = db.query(Event).filter(
        and_(
            Event.is_active == True,
            Event.event_date >= datetime.now(),
            Event.event_date <= end_date
        )
    ).order_by(
        Event.event_date.asc()
    ).limit(limit).all()
    
    return events


@router.get("/types", response_model=List[dict])
async def get_event_types(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get list of available event types with counts"""
    event_types = db.query(
        Event.event_type,
        func.count(Event.id).label('count')
    ).filter(
        and_(
            Event.event_type.isnot(None),
            Event.is_active == True
        )
    ).group_by(
        Event.event_type
    ).order_by(
        func.count(Event.id).desc()
    ).all()
    
    return [{"event_type": t[0], "count": t[1]} for t in event_types]
