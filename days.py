from fastapi import APIRouter, HTTPException
import uuid
from typing import Dict, Any

from app.models.schemas import DayRegenerateRequest
from app.services.gemini_service import gemini_service
from app.models.database import storage_service

router = APIRouter(prefix="/api/itineraries", tags=["Days"])

@router.post("/{itinerary_id}/days/{day_number}/regenerate")
async def regenerate_day(itinerary_id: str, day_number: int, req: DayRegenerateRequest):
    """Regenerate a single day of an itinerary based on user instructions while preserving the rest."""
    itinerary = await storage_service.get_itinerary_by_id(itinerary_id)
    if not itinerary:
        raise HTTPException(status_code=404, detail="Itinerary not found")

    target_day_index = next(
        (i for i, d in enumerate(itinerary.get("days", [])) if d.get("day_number") == day_number),
        None
    )
    if target_day_index is None:
        raise HTTPException(status_code=404, detail=f"Day {day_number} not found in this itinerary")

    if not gemini_service.is_configured():
        raise HTTPException(
            status_code=400,
            detail="Gemini API Key is missing. Please set GEMINI_API_KEY in backend/.env."
        )

    try:
        new_day_data = await gemini_service.regenerate_single_day(itinerary, day_number, req)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Day regeneration failed: {str(e)}")

    # Ensure IDs for new items
    new_day_data["id"] = itinerary["days"][target_day_index].get("id", str(uuid.uuid4()))
    new_day_data["day_number"] = day_number
    new_day_data["date"] = itinerary["days"][target_day_index].get("date")

    for item in new_day_data.get("items", []):
        if not item.get("id"):
            item["id"] = str(uuid.uuid4())

    # Replace day in itinerary
    itinerary["days"][target_day_index] = new_day_data

    # Recalculate total estimated cost
    total_cost = sum(d.get("estimated_day_cost", 0) for d in itinerary.get("days", []))
    # Add accommodation average
    if itinerary.get("accommodations"):
        total_cost += 100 * itinerary.get("duration_days", 1)
    itinerary["total_estimated_cost"] = round(total_cost, 2)

    saved = await storage_service.save_itinerary(itinerary)
    return {
        "message": f"Day {day_number} regenerated successfully",
        "day": new_day_data,
        "itinerary": saved
    }

@router.put("/{itinerary_id}/days/{day_number}")
async def update_day_metadata(itinerary_id: str, day_number: int, data: Dict[str, Any]):
    """Update title or summary for a specific day."""
    itinerary = await storage_service.get_itinerary_by_id(itinerary_id)
    if not itinerary:
        raise HTTPException(status_code=404, detail="Itinerary not found")

    target_day = next(
        (d for d in itinerary.get("days", []) if d.get("day_number") == day_number),
        None
    )
    if not target_day:
        raise HTTPException(status_code=404, detail=f"Day {day_number} not found")

    if "title" in data:
        target_day["title"] = data["title"]
    if "summary" in data:
        target_day["summary"] = data["summary"]

    saved = await storage_service.save_itinerary(itinerary)
    return saved
