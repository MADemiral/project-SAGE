from fastapi import APIRouter

router = APIRouter()

@router.get("/status")
async def embeddings_status():
    """Get status of embeddings system"""
    return {
        "status": "not_configured",
        "message": "Embedding system will be configured soon"
    }
