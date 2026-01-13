from fastapi import APIRouter
from app.api.endpoints import documents, health, auth, users, conversations, embeddings, courses, restaurants, events, imap_calendar

router = APIRouter()

router.include_router(auth.router, prefix="/auth", tags=["authentication"])
router.include_router(users.router, prefix="/users", tags=["users"])
router.include_router(conversations.router, prefix="/conversations", tags=["conversations"])
router.include_router(documents.router, prefix="/documents", tags=["documents"])
router.include_router(embeddings.router, prefix="/ai", tags=["embeddings"])
router.include_router(courses.router, prefix="/courses", tags=["courses"])
router.include_router(restaurants.router, prefix="/restaurants", tags=["restaurants"])
router.include_router(events.router, prefix="/events", tags=["events"])
router.include_router(imap_calendar.router, prefix="/calendar", tags=["calendar-imap"])
router.include_router(health.router, prefix="/health", tags=["health"])
