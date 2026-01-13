"""
IMAP Email Calendar Endpoints - No OAuth Required
Simple username/password authentication
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from datetime import datetime

from app.services.imap_email_service import imap_service
from app.core.database import get_db
from app.models.calendar_event import CalendarEvent


router = APIRouter()


# Request/Response models
class IMAPLoginRequest(BaseModel):
    email: EmailStr
    password: str


class FetchEmailsRequest(BaseModel):
    days: int = 30
    max_results: int = 50


class ExtractEventsRequest(BaseModel):
    user_id: int
    days: int = 30
    max_results: int = 50


class SaveEventRequest(BaseModel):
    user_id: int
    title: str
    description: Optional[str] = None
    event_date: str  # ISO format
    end_date: Optional[str] = None
    location: Optional[str] = None
    event_type: Optional[str] = "other"
    priority: Optional[str] = "medium"
    organizer: Optional[str] = None
    requirements: Optional[str] = None


@router.post("/imap/login")
async def imap_login(request: IMAPLoginRequest):
    """
    Login to email via IMAP (username/password)
    No OAuth or Azure AD required!
    """
    try:
        success = imap_service.connect(request.email, request.password)
        
        return {
            "success": True,
            "authenticated": True,
            "email": request.email,
            "message": "Successfully connected via IMAP"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/imap/status")
async def imap_status():
    """Check if IMAP connection is active"""
    return {
        "authenticated": imap_service.is_connected,
        "email": imap_service.email_address if imap_service.is_connected else None
    }


@router.post("/imap/logout")
async def imap_logout():
    """Disconnect IMAP"""
    imap_service.disconnect()
    return {"success": True, "message": "Disconnected"}


@router.post("/imap/fetch-emails")
async def fetch_emails_imap(request: FetchEmailsRequest):
    """
    Fetch emails via IMAP
    """
    if not imap_service.is_connected:
        raise HTTPException(status_code=401, detail="Not authenticated. Please login first.")
    
    try:
        emails = imap_service.fetch_emails(
            days=request.days,
            max_results=request.max_results
        )
        
        return {
            "success": True,
            "count": len(emails),
            "emails": emails
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/imap/extract-events")
async def extract_events_imap(request: ExtractEventsRequest, db: Session = Depends(get_db)):
    """
    Fetch emails via IMAP and extract events with LLM (does NOT save to database yet)
    Returns events for user review
    """
    if not imap_service.is_connected:
        raise HTTPException(status_code=401, detail="Not authenticated. Please login first.")
    
    try:
        # Fetch emails
        emails = imap_service.fetch_emails(
            days=request.days,
            max_results=request.max_results
        )
        
        if not emails:
            return {
                "success": True,
                "message": "No emails found",
                "extraction": {"events": []}
            }
        
        # Extract events with LLM
        extraction_result = imap_service.extract_events_with_llm(emails)
        
        if not extraction_result.get("success"):
            raise Exception(extraction_result.get("error", "Event extraction failed"))
        
        return {
            "success": True,
            "message": f"Found {len(extraction_result.get('events', []))} potential events. Review and approve them.",
            "emails_processed": len(emails),
            "extraction": extraction_result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/imap/events")
async def save_event_to_calendar(request: SaveEventRequest, db: Session = Depends(get_db)):
    """
    Save a single event to calendar after user approval
    """
    try:
        # Parse dates - handle both date and datetime formats
        event_date_str = request.event_date
        if 'T' in event_date_str or ' ' in event_date_str:
            # Has time component
            for fmt in ["%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"]:
                try:
                    event_date = datetime.strptime(event_date_str.replace('T', ' ').split('.')[0], fmt)
                    break
                except:
                    continue
            else:
                # Fallback to date only
                event_date = datetime.strptime(event_date_str.split()[0], "%Y-%m-%d")
        else:
            # Date only
            event_date = datetime.strptime(event_date_str, "%Y-%m-%d")
        
        end_date = None
        if request.end_date:
            end_date_str = request.end_date
            if 'T' in end_date_str or ' ' in end_date_str:
                for fmt in ["%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"]:
                    try:
                        end_date = datetime.strptime(end_date_str.replace('T', ' ').split('.')[0], fmt)
                        break
                    except:
                        continue
                else:
                    end_date = datetime.strptime(end_date_str.split()[0], "%Y-%m-%d")
            else:
                end_date = datetime.strptime(end_date_str, "%Y-%m-%d")
        
        # Create event
        calendar_event = CalendarEvent(
            user_id=request.user_id,
            title=request.title,
            description=request.description,
            event_date=event_date,
            end_date=end_date,
            location=request.location,
            event_type=request.event_type or "other",
            priority=request.priority or "medium",
            source="imap_email",
            email_subject=request.title,
            llm_extraction_data={
                "organizer": request.organizer,
                "requirements": request.requirements
            },
            is_confirmed=False
        )
        
        db.add(calendar_event)
        db.commit()
        db.refresh(calendar_event)
        
        return {
            "success": True,
            "message": "Event saved successfully",
            "event": {
                "id": calendar_event.id,
                "title": calendar_event.title,
                "event_date": str(calendar_event.event_date),
                "event_type": calendar_event.event_type
            }
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to save event: {str(e)}")


@router.get("/imap/events/{user_id}")
async def get_imap_events(user_id: int, db: Session = Depends(get_db)):
    """Get calendar events for user (from IMAP source)"""
    try:
        events = db.query(CalendarEvent).filter(
            CalendarEvent.user_id == user_id,
            CalendarEvent.source == "imap_email"
        ).order_by(CalendarEvent.event_date.desc()).all()
        
        return {
            "success": True,
            "count": len(events),
            "events": [
                {
                    "id": e.id,
                    "title": e.title,
                    "description": e.description,
                    "event_date": str(e.event_date),
                    "end_date": str(e.end_date) if e.end_date else None,
                    "location": e.location,
                    "event_type": e.event_type,
                    "priority": e.priority,
                    "is_confirmed": e.is_confirmed,
                    "created_at": str(e.created_at)
                }
                for e in events
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
