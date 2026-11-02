from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import date, datetime
import uuid

# ----------------- Sub-models for AI Output & Database ----------------- #

class ActivityItem(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    time_slot: str = Field(..., description="'morning', 'afternoon', 'evening', or 'night'")
    start_time: Optional[str] = Field(None, description="e.g. '09:00 AM'")
    end_time: Optional[str] = Field(None, description="e.g. '11:30 AM'")
    title: str = Field(..., description="Name of the activity, venue, or sight")
    description: str = Field(..., description="Actionable, vivid description of what to experience")
    category: str = Field(..., description="'attraction', 'restaurant', 'accommodation', 'transport', 'leisure', or 'activity'")
    location_name: str = Field(..., description="Venue or landmark name")
    location_address: Optional[str] = Field(None, description="Neighborhood or street address")
    map_query: Optional[str] = Field(None, description="Search term for Google Maps lookup")
    estimated_cost: float = Field(0.0, description="Estimated cost in specified currency")
    currency: str = Field("USD", description="Currency symbol/code")
    booking_tip: Optional[str] = Field(None, description="Pro tips, peak hours, reservations needed")
    order_index: int = Field(0, description="Display order within time slot")

class ItineraryDay(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    day_number: int = Field(..., description="Day index (1, 2, ...)")
    date: Optional[str] = Field(None, description="Formatted date string e.g. '2026-06-15'")
    title: str = Field(..., description="Catchy day theme (e.g. 'Historic Highlights & Riverfront Dining')")
    summary: str = Field(..., description="Brief day preview and vibe")
    estimated_day_cost: float = Field(0.0, description="Total estimated cost for this day")
    items: List[ActivityItem] = Field(default_factory=list)

class AccommodationOption(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = Field(..., description="Hotel, boutique stay, or resort name")
    type: str = Field(..., description="e.g. 'Boutique Hotel', 'Eco Lodge', 'Luxury Resort', 'Budget Hostel'")
    neighborhood: str = Field(..., description="Area or district")
    price_range: str = Field(..., description="e.g. '$60 - $90 / night'")
    vibe: str = Field(..., description="Why it fits this travel style")
    booking_query: Optional[str] = Field(None, description="Map or search query")

class ExpenseItem(BaseModel):
    category: str = Field(..., description="'Accommodation', 'Food & Dining', 'Activities & Sightseeing', 'Transportation', 'Buffer & Contingency'")
    estimated_amount: float = Field(..., description="Estimated total for this category")
    percentage: Optional[int] = Field(0, description="Percentage of total budget")
    currency: str = Field("USD")
    details: Optional[str] = Field(None, description="Breakdown notes")

class LogisticsOverview(BaseModel):
    packing_list: List[str] = Field(default_factory=list, description="Curated packing essentials for destination and season")
    weather_notes: str = Field("", description="Expected weather, temperatures, and seasonal advice")
    transit_advice: str = Field("", description="Best local transport methods (subway, ride-hailing, walking)")
    local_etiquette: List[str] = Field(default_factory=list, description="Crucial cultural tips, dress codes, tipping etiquette")
    emergency_contacts: str = Field("", description="Local emergency services, police, ambulance numbers")

# ----------------- Full Itinerary Model ----------------- #

class Itinerary(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: Optional[str] = None
    title: str
    destination: str
    country: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    duration_days: int
    travel_group: str  # 'solo', 'couple', 'family', 'friends', 'business'
    budget_tier: str   # 'budget', 'moderate', 'luxury'
    currency: str = "USD"
    total_estimated_cost: float = 0.0
    pace: str = "balanced"  # 'relaxed', 'balanced', 'packed'
    interests: List[str] = Field(default_factory=list)
    dietary_preferences: List[str] = Field(default_factory=list)
    cover_image_url: Optional[str] = None
    logistics_overview: LogisticsOverview = Field(default_factory=LogisticsOverview)
    accommodations: List[AccommodationOption] = Field(default_factory=list)
    days: List[ItineraryDay] = Field(default_factory=list)
    expenses: List[ExpenseItem] = Field(default_factory=list)
    status: str = "active"
    is_public: bool = False
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

# ----------------- Request Payloads ----------------- #

class ItineraryCreateRequest(BaseModel):
    destination: str = Field(..., min_length=2, max_length=150)
    origin: Optional[str] = Field(None, description="Starting city for transit advice")
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    duration_days: int = Field(3, ge=1, le=14)
    travel_group: str = Field("solo", description="'solo', 'couple', 'family', 'friends', 'business'")
    budget_tier: str = Field("moderate", description="'budget', 'moderate', 'luxury'")
    currency: str = Field("USD")
    interests: List[str] = Field(default_factory=list)
    dietary_preferences: List[str] = Field(default_factory=list)
    pace: str = Field("balanced", description="'relaxed', 'balanced', 'packed'")
    specific_notes: Optional[str] = Field(None, description="Any specific requests, allergies, or must-see spots")

class DayRegenerateRequest(BaseModel):
    custom_instructions: Optional[str] = Field(None, description="Refinement prompt for this day")
    interests: Optional[List[str]] = None
    pace: Optional[str] = None

class ActivityItemCreate(BaseModel):
    time_slot: str
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    title: str
    description: str
    category: str
    location_name: str
    location_address: Optional[str] = None
    map_query: Optional[str] = None
    estimated_cost: float = 0.0
    currency: str = "USD"
    booking_tip: Optional[str] = None
    order_index: int = 0

class ActivityItemUpdate(BaseModel):
    time_slot: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    location_name: Optional[str] = None
    location_address: Optional[str] = None
    map_query: Optional[str] = None
    estimated_cost: Optional[float] = None
    currency: Optional[str] = None
    booking_tip: Optional[str] = None
    order_index: Optional[int] = None

class ItineraryUpdateRequest(BaseModel):
    title: Optional[str] = None
    status: Optional[str] = None
    is_public: Optional[bool] = None
    cover_image_url: Optional[str] = None
