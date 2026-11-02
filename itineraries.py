from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
import uuid
from datetime import datetime

from app.models.schemas import (
    ItineraryCreateRequest,
    ItineraryUpdateRequest,
    Itinerary
)
from app.services.gemini_service import gemini_service
from app.models.database import storage_service

router = APIRouter(prefix="/api/itineraries", tags=["Itineraries"])

@router.post("/generate")
async def generate_itinerary(req: ItineraryCreateRequest):
    """Generate a personalized day-wise itinerary with Gemini AI and persist it."""
    if not gemini_service.is_configured():
        raise HTTPException(
            status_code=400,
            detail="Gemini API Key is not configured. Please add GEMINI_API_KEY to backend/.env."
        )

    try:
        raw_itinerary = await gemini_service.generate_itinerary(req)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI generation failed: {str(e)}")

    # Assign IDs and metadata
    raw_itinerary["id"] = str(uuid.uuid4())
    raw_itinerary["start_date"] = req.start_date
    raw_itinerary["end_date"] = req.end_date
    raw_itinerary["created_at"] = datetime.utcnow().isoformat()
    raw_itinerary["updated_at"] = raw_itinerary["created_at"]
    raw_itinerary["interests"] = req.interests
    raw_itinerary["dietary_preferences"] = req.dietary_preferences

    # Assign IDs to days and items
    for day in raw_itinerary.get("days", []):
        if not day.get("id"):
            day["id"] = str(uuid.uuid4())
        for item in day.get("items", []):
            if not item.get("id"):
                item["id"] = str(uuid.uuid4())

    saved = await storage_service.save_itinerary(raw_itinerary)
    return saved

@router.get("")
async def list_itineraries(user_id: Optional[str] = None):
    """List saved travel itineraries."""
    return await storage_service.get_all_itineraries(user_id=user_id)

@router.get("/{itinerary_id}")
async def get_itinerary(itinerary_id: str):
    """Retrieve an itinerary by its unique ID."""
    itinerary = await storage_service.get_itinerary_by_id(itinerary_id)
    if not itinerary:
        raise HTTPException(status_code=404, detail="Itinerary not found")
    return itinerary

@router.put("/{itinerary_id}")
async def update_itinerary(itinerary_id: str, update_data: ItineraryUpdateRequest):
    """Update high-level itinerary details (title, cover image, public status)."""
    itinerary = await storage_service.get_itinerary_by_id(itinerary_id)
    if not itinerary:
        raise HTTPException(status_code=404, detail="Itinerary not found")

    if update_data.title is not None:
        itinerary["title"] = update_data.title
    if update_data.status is not None:
        itinerary["status"] = update_data.status
    if update_data.is_public is not None:
        itinerary["is_public"] = update_data.is_public
    if update_data.cover_image_url is not None:
        itinerary["cover_image_url"] = update_data.cover_image_url

    saved = await storage_service.save_itinerary(itinerary)
    return saved

@router.delete("/{itinerary_id}")
async def delete_itinerary(itinerary_id: str):
    """Delete an itinerary and its days/items."""
    success = await storage_service.delete_itinerary(itinerary_id)
    return {"success": success, "message": "Itinerary deleted successfully"}

@router.post("/{itinerary_id}/duplicate")
async def duplicate_itinerary(itinerary_id: str):
    """Duplicate an existing itinerary for customization."""
    itinerary = await storage_service.get_itinerary_by_id(itinerary_id)
    if not itinerary:
        raise HTTPException(status_code=404, detail="Itinerary not found")

    cloned = json.loads(json.dumps(itinerary))
    cloned["id"] = str(uuid.uuid4())
    cloned["title"] = f"{cloned['title']} (Copy)"
    cloned["created_at"] = datetime.utcnow().isoformat()
    cloned["updated_at"] = cloned["created_at"]

    for day in cloned.get("days", []):
        day["id"] = str(uuid.uuid4())
        for item in day.get("items", []):
            item["id"] = str(uuid.uuid4())

    saved = await storage_service.save_itinerary(cloned)
    return saved
