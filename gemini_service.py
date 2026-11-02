import json
import re
from typing import Dict, Any, Optional
from app.config import settings
from app.models.schemas import ItineraryCreateRequest, DayRegenerateRequest

# Try importing official new SDK, fallback to legacy if needed
try:
    from google import genai
    from google.genai import types
    USE_NEW_SDK = True
except ImportError:
    import google.generativeai as legacy_genai
    USE_NEW_SDK = False

class GeminiService:
    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        self.model_name = settings.GEMINI_MODEL or "gemini-3.8-flash"

    def is_configured(self) -> bool:
        key = settings.GEMINI_API_KEY or self.api_key
        return bool(key and key.strip() and key != "your_gemini_api_key_here")

    def _clean_json_response(self, text: str) -> str:
        """Strip markdown fences, leading/trailing whitespace, and extract valid JSON."""
        text = text.strip()
        match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
        if match:
            text = match.group(1).strip()
        first_bracket = min(
            [text.find('{')] if '{' in text else [float('inf')] +
            [text.find('[')] if '[' in text else [float('inf')]
        )
        if first_bracket != float('inf') and first_bracket > 0:
            text = text[first_bracket:]
        last_bracket = max(text.rfind('}'), text.rfind(']'))
        if last_bracket != -1 and last_bracket < len(text) - 1:
            text = text[:last_bracket + 1]
        return text

    def _call_gemini(self, prompt: str, temperature: float = 0.4) -> str:
        api_key = settings.GEMINI_API_KEY or self.api_key
        if not api_key:
            raise ValueError(
                "Gemini API Key is not configured. Please enter your API key in the web app settings or backend/.env."
            )

        # NOTE: response_mime_type="application/json" causes indefinite hangs on some API keys.
        # Instead, we instruct the model via prompt and parse the text response as JSON.
        candidate_models = [
            "gemini-3.8-flash",
            settings.GEMINI_MODEL,
            "gemini-2.0-flash",
            "gemini-1.5-flash",
        ]
        # Remove duplicates while preserving order
        candidate_models = list(dict.fromkeys([m for m in candidate_models if m]))

        last_error = None
        for model in candidate_models:
            try:
                if USE_NEW_SDK:
                    client = genai.Client(api_key=api_key)
                    response = client.models.generate_content(
                        model=model,
                        contents=prompt,
                        config=types.GenerateContentConfig(
                            temperature=temperature,
                        )
                    )
                    return response.text
                else:
                    legacy_genai.configure(api_key=api_key)
                    m = legacy_genai.GenerativeModel(
                        model_name=model,
                        generation_config={"temperature": temperature}
                    )
                    response = m.generate_content(prompt)
                    return response.text
            except Exception as e:
                err_str = str(e)
                last_error = e
                # If 404/not found, try next candidate model
                if any(code in err_str for code in ["404", "NOT_FOUND", "deprecated", "no longer available"]):
                    continue
                else:
                    raise e

        raise last_error

    async def generate_itinerary(self, req: ItineraryCreateRequest) -> Dict[str, Any]:
        interests_str = ", ".join(req.interests) if req.interests else "general sightseeing, local culinary culture, photography"
        dietary_str = ", ".join(req.dietary_preferences) if req.dietary_preferences else "no specific restrictions"
        dates_info = f"from {req.start_date} to {req.end_date}" if req.start_date and req.end_date else f"for {req.duration_days} days"
        origin_str = f"Departing from: {req.origin}." if req.origin else ""
        notes_str = f"Specific requests: {req.specific_notes}." if req.specific_notes else ""

        prompt = f"""
You are an elite, world-class travel planner and destination concierge.
Create a detailed, highly personalized, realistic {req.duration_days}-day travel itinerary for:
- Destination: {req.destination}
- Duration: {req.duration_days} days ({dates_info})
- Traveler Profile: {req.travel_group} traveler(s) (tailor pacing, activities, and dining for this dynamic)
- Budget Tier: {req.budget_tier} (budget, moderate, or luxury - ensure all recommendations & cost estimates strictly match this level)
- Currency: {req.currency}
- Interests & Vibes: {interests_str}
- Pace: {req.pace}
- Dietary Preferences: {dietary_str}
{origin_str}
{notes_str}

CRITICAL RULES:
1. Use REAL, verified venues, restaurants, and sights in {req.destination} with accurate neighborhood locations.
2. Group activities logically by neighborhood to minimize transit time.
3. Every day MUST have 3 to 5 distinct items divided between 'morning', 'afternoon', 'evening', and 'night'.
4. Include authentic dining spots matching the budget and dietary preferences.
5. Provide practical booking tips (e.g. skip-the-line tickets, dress code, best viewpoint timing).
6. Provide realistic estimated costs in {req.currency} for activities, dining, and daily totals.
7. Accommodations should offer 2-3 genuine options (name, type, price_range, neighborhood, vibe).
8. Logistics overview must include curated packing essentials, weather advisory, local transit advice, cultural etiquette, and local emergency phone numbers.
9. Expenses breakdown must include realistic totals across Accommodation, Food & Dining, Activities & Sightseeing, Transportation, and Buffer.

Return ONLY a valid JSON object matching this exact schema:
{{
  "title": "Inspiring Trip Title (e.g. Kyoto & Osaka: Zen Temples & Culinary Wonders)",
  "destination": "{req.destination}",
  "country": "Country name",
  "duration_days": {req.duration_days},
  "travel_group": "{req.travel_group}",
  "budget_tier": "{req.budget_tier}",
  "currency": "{req.currency}",
  "total_estimated_cost": 1250.00,
  "pace": "{req.pace}",
  "logistics_overview": {{
    "packing_list": ["item 1", "item 2", "item 3", "item 4", "item 5"],
    "weather_notes": "Detailed weather forecast and what to wear",
    "transit_advice": "Detailed advice on metro, cards, taxi apps, walkability",
    "local_etiquette": ["Etiquette rule 1", "Etiquette rule 2", "Tipping policy"],
    "emergency_contacts": "Police: 110, Medical/Ambulance: 119"
  }},
  "accommodations": [
    {{
      "name": "Exact Hotel Name",
      "type": "Boutique Hotel / Luxury Ryokan / Hostal / Resort",
      "neighborhood": "Area name",
      "price_range": "e.g. $80 - $120 / night",
      "vibe": "Why it's great for {req.travel_group} travelers",
      "booking_query": "Hotel Name Destination"
    }}
  ],
  "days": [
    {{
      "day_number": 1,
      "date": "{req.start_date or ''}",
      "title": "Day 1 Theme Title",
      "summary": "1-2 sentence preview of the day's vibe and flow",
      "estimated_day_cost": 180.00,
      "items": [
        {{
          "time_slot": "morning",
          "start_time": "09:00 AM",
          "end_time": "11:30 AM",
          "title": "Specific Attraction / Landmark Name",
          "description": "Vivid description of what to do and see here",
          "category": "attraction",
          "location_name": "Official Landmark Name",
          "location_address": "Street or Neighborhood",
          "map_query": "Official Landmark Name, {req.destination}",
          "estimated_cost": 25.00,
          "currency": "{req.currency}",
          "booking_tip": "Buy tickets online 3 days ahead",
          "order_index": 0
        }},
        {{
          "time_slot": "afternoon",
          "start_time": "12:30 PM",
          "end_time": "02:00 PM",
          "title": "Specific Restaurant Name",
          "description": "What to order, specialties, vibe",
          "category": "restaurant",
          "location_name": "Restaurant Name",
          "location_address": "Neighborhood",
          "map_query": "Restaurant Name, {req.destination}",
          "estimated_cost": 30.00,
          "currency": "{req.currency}",
          "booking_tip": "Arrive by 12:15 to avoid line",
          "order_index": 1
        }}
      ]
    }}
  ],
  "expenses": [
    {{
      "category": "Accommodation",
      "estimated_amount": 500.00,
      "percentage": 40,
      "currency": "{req.currency}",
      "details": "Average cost based on {req.budget_tier} tier"
    }},
    {{
      "category": "Food & Dining",
      "estimated_amount": 350.00,
      "percentage": 28,
      "currency": "{req.currency}",
      "details": "Breakfast, lunches, local dinners and street food"
    }},
    {{
      "category": "Activities & Sightseeing",
      "estimated_amount": 200.00,
      "percentage": 16,
      "currency": "{req.currency}",
      "details": "Entrance fees, exhibits, guided walks"
    }},
    {{
      "category": "Transportation",
      "estimated_amount": 100.00,
      "percentage": 8,
      "currency": "{req.currency}",
      "details": "Metro passes, trains, local taxis"
    }},
    {{
      "category": "Buffer & Contingency",
      "estimated_amount": 100.00,
      "percentage": 8,
      "currency": "{req.currency}",
      "details": "Emergency cushion & souvenirs"
    }}
  ]
}}
"""
        raw_text = self._call_gemini(prompt, temperature=0.4)
        cleaned = self._clean_json_response(raw_text)
        data = json.loads(cleaned)
        return data

    async def regenerate_single_day(
        self,
        itinerary_context: Dict[str, Any],
        day_number: int,
        req: DayRegenerateRequest
    ) -> Dict[str, Any]:
        destination = itinerary_context.get("destination", "")
        travel_group = itinerary_context.get("travel_group", "solo")
        budget_tier = itinerary_context.get("budget_tier", "moderate")
        currency = itinerary_context.get("currency", "USD")
        existing_days_titles = [f"Day {d.get('day_number')}: {d.get('title')}" for d in itinerary_context.get("days", []) if d.get('day_number') != day_number]
        context_str = "; ".join(existing_days_titles)

        instructions = req.custom_instructions or "Provide fresh, exciting, alternative activities and dining spots for this day."
        interests_str = ", ".join(req.interests) if req.interests else ", ".join(itinerary_context.get("interests", []))

        prompt = f"""
You are an expert travel concierge.
Regenerate ONLY Day {day_number} of a trip to {destination}.

Context of other days in this trip (do NOT repeat these themes/places):
{context_str}

Traveler Profile: {travel_group}
Budget Tier: {budget_tier}
Currency: {currency}
Interests: {interests_str}
User's specific adjustment request for Day {day_number}:
"{instructions}"

Return ONLY a valid JSON object for this single day matching this exact schema:
{{
  "day_number": {day_number},
  "title": "Fresh Engaging Day Title",
  "summary": "1-2 sentence preview of the refreshed flow",
  "estimated_day_cost": 150.00,
  "items": [
    {{
      "time_slot": "morning",
      "start_time": "09:00 AM",
      "end_time": "11:30 AM",
      "title": "Attraction or Activity Name",
      "description": "Vivid description",
      "category": "attraction",
      "location_name": "Landmark Name",
      "location_address": "Neighborhood",
      "map_query": "Landmark Name, {destination}",
      "estimated_cost": 20.00,
      "currency": "{currency}",
      "booking_tip": "Helpful tip",
      "order_index": 0
    }},
    {{
      "time_slot": "afternoon",
      "start_time": "12:30 PM",
      "end_time": "02:00 PM",
      "title": "Restaurant Name",
      "description": "Recommended dish",
      "category": "restaurant",
      "location_name": "Restaurant Name",
      "location_address": "Neighborhood",
      "map_query": "Restaurant Name, {destination}",
      "estimated_cost": 30.00,
      "currency": "{currency}",
      "booking_tip": "Reservation tip",
      "order_index": 1
    }},
    {{
      "time_slot": "evening",
      "start_time": "05:00 PM",
      "end_time": "08:00 PM",
      "title": "Evening Attraction / Experience",
      "description": "Evening vibe and sunset/night view",
      "category": "attraction",
      "location_name": "Experience Name",
      "location_address": "Neighborhood",
      "map_query": "Experience Name, {destination}",
      "estimated_cost": 25.00,
      "currency": "{currency}",
      "booking_tip": "Best lighting timing",
      "order_index": 2
    }}
  ]
}}
"""
        raw_text = self._call_gemini(prompt, temperature=0.5)
        cleaned = self._clean_json_response(raw_text)
        data = json.loads(cleaned)
        return data

gemini_service = GeminiService()
