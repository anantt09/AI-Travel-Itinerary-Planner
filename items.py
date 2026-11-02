from fastapi import APIRouter, HTTPException
import uuid

from app.models.schemas import ActivityItemCreate, ActivityItemUpdate
from app.models.database import storage_service

router = APIRouter(prefix="/api/itineraries", tags=["Items"])

@router.post("/{itinerary_id}/days/{day_number}/items")
async def add_item_to_day(itinerary_id: str, day_number: int, item_data: ActivityItemCreate):
    """Add a new custom activity, meal, or attraction to a specific day."""
    itinerary = await storage_service.get_itinerary_by_id(itinerary_id)
    if not itinerary:
        raise HTTPException(status_code=404, detail="Itinerary not found")

    target_day = next(
        (d for d in itinerary.get("days", []) if d.get("day_number") == day_number),
        None
    )
    if not target_day:
        raise HTTPException(status_code=404, detail=f"Day {day_number} not found")

    new_item = item_data.model_dump()
    new_item["id"] = str(uuid.uuid4())
    if not new_item.get("map_query"):
        new_item["map_query"] = f"{new_item['location_name']}, {itinerary['destination']}"

    target_day.setdefault("items", []).append(new_item)

    # Recalculate day cost
    target_day["estimated_day_cost"] = round(
        sum(item.get("estimated_cost", 0) for item in target_day["items"]), 2
    )

    saved = await storage_service.save_itinerary(itinerary)
    return {"message": "Item added successfully", "item": new_item, "itinerary": saved}

@router.put("/{itinerary_id}/items/{item_id}")
async def update_item(itinerary_id: str, item_id: str, update_data: ActivityItemUpdate):
    """Update details of an activity/dining item."""
    itinerary = await storage_service.get_itinerary_by_id(itinerary_id)
    if not itinerary:
        raise HTTPException(status_code=404, detail="Itinerary not found")

    found_item = None
    target_day = None

    for day in itinerary.get("days", []):
        for item in day.get("items", []):
            if item.get("id") == item_id:
                found_item = item
                target_day = day
                break
        if found_item:
            break

    if not found_item:
        raise HTTPException(status_code=404, detail="Activity item not found")

    # Apply updates
    updates = update_data.model_dump(exclude_unset=True)
    for key, val in updates.items():
        found_item[key] = val

    # Recalculate day cost
    target_day["estimated_day_cost"] = round(
        sum(it.get("estimated_cost", 0) for it in target_day["items"]), 2
    )

    saved = await storage_service.save_itinerary(itinerary)
    return {"message": "Item updated successfully", "item": found_item, "itinerary": saved}

@router.delete("/{itinerary_id}/items/{item_id}")
async def delete_item(itinerary_id: str, item_id: str):
    """Delete an activity/dining item from a day."""
    itinerary = await storage_service.get_itinerary_by_id(itinerary_id)
    if not itinerary:
        raise HTTPException(status_code=404, detail="Itinerary not found")

    deleted = False
    for day in itinerary.get("days", []):
        original_len = len(day.get("items", []))
        day["items"] = [it for it in day.get("items", []) if it.get("id") != item_id]
        if len(day["items"]) < original_len:
            deleted = True
            day["estimated_day_cost"] = round(
                sum(it.get("estimated_cost", 0) for it in day["items"]), 2
            )
            break

    if not deleted:
        raise HTTPException(status_code=404, detail="Item not found")

    saved = await storage_service.save_itinerary(itinerary)
    return {"message": "Item deleted successfully", "itinerary": saved}
