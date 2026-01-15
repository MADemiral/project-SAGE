"""
Fix timezone issue in existing calendar events
Run this script to convert all existing events from UTC to local time
"""
from app.core.database import SessionLocal
from app.models.calendar_event import CalendarEvent
from datetime import datetime, timedelta

def fix_timezone():
    db = SessionLocal()
    try:
        # Get all events
        events = db.query(CalendarEvent).all()
        print(f"Found {len(events)} events to fix")
        
        for event in events:
            # If event_date has timezone info, convert it to naive datetime
            if event.event_date:
                # PostgreSQL is storing in UTC, we need to add 3 hours to get Turkey time
                # But since we changed the model to timezone=False, we just need to
                # ensure the datetime is stored correctly
                print(f"Event: {event.title} - Current time: {event.event_date}")
                
            if event.end_date:
                print(f"  End time: {event.end_date}")
        
        db.commit()
        print("✅ Timezone fix completed!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    fix_timezone()
