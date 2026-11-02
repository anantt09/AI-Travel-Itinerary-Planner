-- Supabase PostgreSQL Schema for Personalized Travel Itinerary Planner

-- Enable UUID extension if not enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. Profiles Table (syncs with Supabase auth.users)
CREATE TABLE IF NOT EXISTS public.profiles (
  id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  email TEXT NOT NULL,
  full_name TEXT,
  avatar_url TEXT,
  preferred_currency TEXT DEFAULT 'USD',
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Trigger to automatically create profile when new auth.user signs up
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO public.profiles (id, email, full_name, avatar_url)
  VALUES (
    NEW.id,
    NEW.email,
    COALESCE(NEW.raw_user_meta_data->>'full_name', NEW.email),
    COALESCE(NEW.raw_user_meta_data->>'avatar_url', '')
  )
  ON CONFLICT (id) DO UPDATE
  SET email = EXCLUDED.email,
      full_name = EXCLUDED.full_name,
      updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
  AFTER INSERT OR UPDATE ON auth.users
  FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- 2. Itineraries Table
CREATE TABLE IF NOT EXISTS public.itineraries (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE,
  title TEXT NOT NULL,
  destination TEXT NOT NULL,
  country TEXT,
  start_date DATE,
  end_date DATE,
  duration_days INT NOT NULL CHECK (duration_days BETWEEN 1 AND 30),
  travel_group TEXT NOT NULL CHECK (travel_group IN ('solo', 'couple', 'family', 'friends', 'business')),
  budget_tier TEXT NOT NULL CHECK (budget_tier IN ('budget', 'moderate', 'luxury')),
  currency TEXT NOT NULL DEFAULT 'USD',
  total_estimated_cost NUMERIC(10, 2) DEFAULT 0,
  pace TEXT DEFAULT 'balanced' CHECK (pace IN ('relaxed', 'balanced', 'packed')),
  interests TEXT[] DEFAULT '{}',
  dietary_preferences TEXT[] DEFAULT '{}',
  cover_image_url TEXT,
  logistics_overview JSONB DEFAULT '{}'::jsonb,
  status TEXT DEFAULT 'active' CHECK (status IN ('active', 'archived')),
  is_public BOOLEAN DEFAULT false,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. Itinerary Days Table
CREATE TABLE IF NOT EXISTS public.itinerary_days (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  itinerary_id UUID NOT NULL REFERENCES public.itineraries(id) ON DELETE CASCADE,
  day_number INT NOT NULL,
  date DATE,
  title TEXT NOT NULL,
  summary TEXT,
  estimated_day_cost NUMERIC(10, 2) DEFAULT 0,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE (itinerary_id, day_number)
);

-- 4. Itinerary Items Table (Attractions, Dining, Transit, Accommodations, Activities)
CREATE TABLE IF NOT EXISTS public.itinerary_items (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  day_id UUID NOT NULL REFERENCES public.itinerary_days(id) ON DELETE CASCADE,
  time_slot TEXT NOT NULL CHECK (time_slot IN ('morning', 'afternoon', 'evening', 'night')),
  start_time TEXT,
  end_time TEXT,
  title TEXT NOT NULL,
  description TEXT,
  category TEXT NOT NULL CHECK (category IN ('attraction', 'restaurant', 'accommodation', 'transport', 'leisure', 'activity')),
  location_name TEXT NOT NULL,
  location_address TEXT,
  map_query TEXT,
  estimated_cost NUMERIC(10, 2) DEFAULT 0,
  currency TEXT DEFAULT 'USD',
  booking_tip TEXT,
  order_index INT NOT NULL DEFAULT 0,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 5. Expenses Summary Table
CREATE TABLE IF NOT EXISTS public.expenses (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  itinerary_id UUID NOT NULL REFERENCES public.itineraries(id) ON DELETE CASCADE,
  category TEXT NOT NULL,
  estimated_amount NUMERIC(10, 2) DEFAULT 0,
  currency TEXT DEFAULT 'USD',
  details JSONB DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for lightning fast queries
CREATE INDEX IF NOT EXISTS idx_itineraries_user_id ON public.itineraries(user_id);
CREATE INDEX IF NOT EXISTS idx_itinerary_days_itinerary_id ON public.itinerary_days(itinerary_id);
CREATE INDEX IF NOT EXISTS idx_itinerary_items_day_id ON public.itinerary_items(day_id);
CREATE INDEX IF NOT EXISTS idx_expenses_itinerary_id ON public.expenses(itinerary_id);

-- Enable Row Level Security (RLS)
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.itineraries ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.itinerary_days ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.itinerary_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.expenses ENABLE ROW LEVEL SECURITY;

-- Profiles Policies
CREATE POLICY "Users can view own profile" ON public.profiles
  FOR SELECT USING (auth.uid() = id);

CREATE POLICY "Users can update own profile" ON public.profiles
  FOR UPDATE USING (auth.uid() = id);

-- Itineraries Policies
CREATE POLICY "Users can view own or public itineraries" ON public.itineraries
  FOR SELECT USING (auth.uid() = user_id OR is_public = true OR user_id IS NULL);

CREATE POLICY "Users can insert itineraries" ON public.itineraries
  FOR INSERT WITH CHECK (auth.uid() = user_id OR user_id IS NULL);

CREATE POLICY "Users can update own itineraries" ON public.itineraries
  FOR UPDATE USING (auth.uid() = user_id OR user_id IS NULL);

CREATE POLICY "Users can delete own itineraries" ON public.itineraries
  FOR DELETE USING (auth.uid() = user_id OR user_id IS NULL);

-- Days Policies
CREATE POLICY "Users can view itinerary days" ON public.itinerary_days
  FOR SELECT USING (
    EXISTS (
      SELECT 1 FROM public.itineraries
      WHERE itineraries.id = itinerary_days.itinerary_id
      AND (itineraries.user_id = auth.uid() OR itineraries.is_public = true OR itineraries.user_id IS NULL)
    )
  );

CREATE POLICY "Users can modify itinerary days" ON public.itinerary_days
  FOR ALL USING (
    EXISTS (
      SELECT 1 FROM public.itineraries
      WHERE itineraries.id = itinerary_days.itinerary_id
      AND (itineraries.user_id = auth.uid() OR itineraries.user_id IS NULL)
    )
  );

-- Items Policies
CREATE POLICY "Users can view itinerary items" ON public.itinerary_items
  FOR SELECT USING (
    EXISTS (
      SELECT 1 FROM public.itinerary_days
      JOIN public.itineraries ON itineraries.id = itinerary_days.itinerary_id
      WHERE itinerary_days.id = itinerary_items.day_id
      AND (itineraries.user_id = auth.uid() OR itineraries.is_public = true OR itineraries.user_id IS NULL)
    )
  );

CREATE POLICY "Users can modify itinerary items" ON public.itinerary_items
  FOR ALL USING (
    EXISTS (
      SELECT 1 FROM public.itinerary_days
      JOIN public.itineraries ON itineraries.id = itinerary_days.itinerary_id
      WHERE itinerary_days.id = itinerary_items.day_id
      AND (itineraries.user_id = auth.uid() OR itineraries.user_id IS NULL)
    )
  );

-- Expenses Policies
CREATE POLICY "Users can view expenses" ON public.expenses
  FOR SELECT USING (
    EXISTS (
      SELECT 1 FROM public.itineraries
      WHERE itineraries.id = expenses.itinerary_id
      AND (itineraries.user_id = auth.uid() OR itineraries.is_public = true OR itineraries.user_id IS NULL)
    )
  );

CREATE POLICY "Users can modify expenses" ON public.expenses
  FOR ALL USING (
    EXISTS (
      SELECT 1 FROM public.itineraries
      WHERE itineraries.id = expenses.itinerary_id
      AND (itineraries.user_id = auth.uid() OR itineraries.user_id IS NULL)
    )
  );
