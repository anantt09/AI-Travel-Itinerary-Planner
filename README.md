# 🌍 WanderCraft — Personalized Travel Itinerary Planner

An intelligent, full-stack travel planner powered by **React 19**, **Vite**, **Tailwind CSS**, **Python FastAPI**, **Supabase**, and **Google Gemini 2.5 Flash**.

---

## ✨ Features

1. **AI-Powered Day-Wise Itineraries**: Rich morning, afternoon, evening, and night schedules with verified attractions, authentic restaurants, and localized transit.
2. **Traveler Profile Dynamics**: Tailored pacing and venues for **Solo**, **Couple / Romantic**, **Family with Kids**, **Friends Groups**, and **Business Travelers**.
3. **Budget-Based Recommendations**: Strict budget tiers (**Backpacker**, **Moderate**, **Luxury**) with multi-currency support (USD, EUR, GBP, INR, JPY, CAD, AUD).
4. **Single-Day Regeneration**: Re-prompt and regenerate any single day with custom instructions (e.g., *"Focus on street food and sunset views"*) without altering the rest of your trip.
5. **Interactive Itinerary Dashboard**:
   - Day-switcher tabs with day themes and cost previews.
   - Interactive timeline cards with Google Maps direct navigation.
   - Accommodation recommendations with neighborhood vibes and booking links.
   - Visual budget & expense breakdown graphs.
   - Interactive packing checklist (mark items as packed).
   - Weather advisories, local customs, and emergency contacts.
6. **In-place Customization**: Add custom activities, edit timings, descriptions, costs, or delete items.
7. **Supabase Persistence & Resilient Fallback**: Cloud sync with PostgreSQL RLS + local persistence engine.
8. **Print & PDF Export**: Instant print-optimized travel schedule.

---

## 🚀 Quick Start (How to Run)

### Option 1: 1-Click Launch (Recommended)
Open PowerShell in the project directory and run:
```powershell
.\run.ps1
```
*(Or double-click `run.bat` in Windows File Explorer)*

---

### Option 2: Manual Terminal Launch

#### Step 1: Start Backend (FastAPI)
In Terminal 1:
```powershell
$env:PYTHONPATH = "backend"
backend\venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
API Documentation will be live at: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

#### Step 2: Start Frontend (React + Vite)
In Terminal 2:
```powershell
$env:Path = "C:\Program Files\nodejs;" + $env:Path
cd frontend
npm run dev
```
Open your browser at: **[http://localhost:5173](http://localhost:5173)**

---

## 🔑 Configuration (Gemini API & Supabase)

### 1. Google Gemini API Key
- Get a free API key from [Google AI Studio](https://aistudio.google.com/app/apikey).
- You can either:
  - Enter it in `backend/.env`:
    ```env
    GEMINI_API_KEY=your_actual_key_here
    GEMINI_MODEL=gemini-2.5-flash
    ```
  - **Or enter it directly in the web UI** by clicking the **"Configure Key"** button in the top right navbar!

### 2. Supabase Setup (Optional for Cloud Sync)
1. Create a project at [supabase.com](https://supabase.com).
2. Go to **SQL Editor** and paste the contents of `supabase/migrations/001_initial_schema.sql`.
3. Add your `SUPABASE_URL` and `SUPABASE_KEY` in `backend/.env` or the web UI settings.
*(If omitted, WanderCraft automatically uses the local persistence store).*

---

## 📂 Project Structure

```text
travel-itinerary-planner/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app & endpoints
│   │   ├── config.py            # Pydantic environment configuration
│   │   ├── models/
│   │   │   ├── schemas.py       # Pydantic data schemas
│   │   │   └── database.py      # Supabase & resilient store
│   │   ├── services/
│   │   │   └── gemini_service.py# Google Gemini 2.5 Flash engine
│   │   └── routers/
│   │       ├── itineraries.py   # Full itinerary generation & CRUD
│   │       ├── days.py          # Single-day regeneration
│   │       └── items.py         # Activity CRUD
│   ├── requirements.txt
│   └── .env
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Navbar.jsx       # Header & API status
│   │   │   ├── Wizard.jsx       # 5-step interactive trip creator
│   │   │   ├── Dashboard.jsx    # Interactive schedule & expense viewer
│   │   │   ├── LoadingOverlay.jsx# Generation progress screen
│   │   │   ├── RegenerateDayModal.jsx # Day customization
│   │   │   ├── ActivityModal.jsx# Add / Edit stop modal
│   │   │   ├── SettingsModal.jsx# API keys configuration
│   │   │   └── SavedTripsModal.jsx # Saved itineraries manager
│   │   ├── services/api.js      # Backend API client
│   │   ├── App.jsx
│   │   └── index.css
├── supabase/
│   └── migrations/
│       └── 001_initial_schema.sql # PostgreSQL schema & RLS
├── run.ps1                      # 1-Click PowerShell launcher
├── run.bat                      # 1-Click Batch launcher
└── README.md
```
