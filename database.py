import json
import os
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime
from app.config import settings

class StorageService:
    def __init__(self):
        self.supabase_client = None
        self.local_storage_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "data",
            "itineraries.json"
        )
        os.makedirs(os.path.dirname(self.local_storage_path), exist_ok=True)
        if not os.path.exists(self.local_storage_path):
            with open(self.local_storage_path, "w", encoding="utf-8") as f:
                json.dump([], f)

        # Attempt to init Supabase client if configured
        if settings.SUPABASE_URL and settings.SUPABASE_KEY and "supabase.co" in settings.SUPABASE_URL:
            try:
                from supabase import create_client
                self.supabase_client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
                print(f"[Supabase] Connected to {settings.SUPABASE_URL}")
            except Exception as e:
                print(f"[Supabase] Could not connect: {e}. Falling back to local storage.")
                self.supabase_client = None

    def is_supabase_active(self) -> bool:
        return self.supabase_client is not None

    # ---------- Local Storage Helpers ---------- #

    def _read_local(self) -> List[Dict[str, Any]]:
        try:
            with open(self.local_storage_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    def _write_local(self, data: List[Dict[str, Any]]):
        with open(self.local_storage_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    # ---------- Itinerary CRUD ---------- #

    async def save_itinerary(self, itinerary: Dict[str, Any]) -> Dict[str, Any]:
        """Save new or updated full itinerary."""
        if not itinerary.get("id"):
            itinerary["id"] = str(uuid.uuid4())
        
        itinerary["updated_at"] = datetime.utcnow().isoformat()
        if not itinerary.get("created_at"):
            itinerary["created_at"] = itinerary["updated_at"]

        # Ensure all days and items have IDs
        for day in itinerary.get("days", []):
            if not day.get("id"):
                day["id"] = str(uuid.uuid4())
            for item in day.get("items", []):
                if not item.get("id"):
                    item["id"] = str(uuid.uuid4())

        # If Supabase is active, persist to database
        if self.is_supabase_active():
            try:
                # Upsert into itineraries table
                itin_record = {
                    "id": itinerary["id"],
                    "title": itinerary["title"],
                    "destination": itinerary["destination"],
                    "country": itinerary.get("country"),
                    "duration_days": itinerary["duration_days"],
                    "travel_group": itinerary["travel_group"],
                    "budget_tier": itinerary["budget_tier"],
                    "currency": itinerary.get("currency", "USD"),
                    "total_estimated_cost": itinerary.get("total_estimated_cost", 0),
                    "pace": itinerary.get("pace", "balanced"),
                    "interests": itinerary.get("interests", []),
                    "dietary_preferences": itinerary.get("dietary_preferences", []),
                    "cover_image_url": itinerary.get("cover_image_url"),
                    "logistics_overview": itinerary.get("logistics_overview", {}),
                    "status": itinerary.get("status", "active"),
                    "is_public": itinerary.get("is_public", False),
                }
                if itinerary.get("user_id"):
                    itin_record["user_id"] = itinerary["user_id"]

                self.supabase_client.table("itineraries").upsert(itin_record).execute()
            except Exception as e:
                print(f"[Supabase Sync Error]: {e}")

        # Always maintain local store for speed & resilience
        items = self._read_local()
        existing_idx = next((i for i, item in enumerate(items) if item["id"] == itinerary["id"]), None)
        if existing_idx is not None:
            items[existing_idx] = itinerary
        else:
            items.insert(0, itinerary)
        self._write_local(items)
        return itinerary

    async def get_all_itineraries(self, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        # If Supabase is active and user_id is provided
        if self.is_supabase_active():
            try:
                query = self.supabase_client.table("itineraries").select("*").order("created_at", desc=True)
                if user_id:
                    query = query.eq("user_id", user_id)
                res = query.execute()
                if res.data:
                    # Enrich from local store or construct
                    return res.data
            except Exception as e:
                print(f"[Supabase Fetch Error]: {e}")

        # Fallback to local store
        items = self._read_local()
        if user_id:
            items = [item for item in items if item.get("user_id") == user_id or not item.get("user_id")]
        return items

    async def get_itinerary_by_id(self, itinerary_id: str) -> Optional[Dict[str, Any]]:
        items = self._read_local()
        for item in items:
            if item["id"] == itinerary_id:
                return item

        if self.is_supabase_active():
            try:
                res = self.supabase_client.table("itineraries").select("*").eq("id", itinerary_id).single().execute()
                if res.data:
                    return res.data
            except Exception as e:
                print(f"[Supabase Get Error]: {e}")

        return None

    async def delete_itinerary(self, itinerary_id: str) -> bool:
        items = self._read_local()
        items = [item for item in items if item["id"] != itinerary_id]
        self._write_local(items)

        if self.is_supabase_active():
            try:
                self.supabase_client.table("itineraries").delete().eq("id", itinerary_id).execute()
            except Exception as e:
                print(f"[Supabase Delete Error]: {e}")

        return True

storage_service = StorageService()
