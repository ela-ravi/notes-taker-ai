-- Meeting Notes Taker - Initial Database Schema
-- Run this in Supabase SQL Editor: https://supabase.com/dashboard/project/_/sql

-- ============================================
-- PROFILES TABLE
-- Extends Supabase auth.users with app-specific data
-- ============================================
create table if not exists public.profiles (
  id uuid references auth.users on delete cascade primary key,
  email text,
  full_name text,
  subscription_tier text default 'free' check (subscription_tier in ('free', 'pro')),
  subscription_status text default 'active' check (subscription_status in ('active', 'canceled', 'past_due', 'expired')),
  dodo_customer_id text,
  dodo_subscription_id text,
  meetings_this_month integer default 0,
  meetings_reset_date timestamp with time zone default (date_trunc('month', now()) + interval '1 month'),
  created_at timestamp with time zone default now(),
  updated_at timestamp with time zone default now()
);

-- ============================================
-- USAGE LOGS TABLE
-- Track meeting summarization usage for analytics
-- ============================================
create table if not exists public.usage_logs (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references public.profiles on delete cascade,
  meeting_title text,
  tokens_used integer default 0,
  model_used text,
  duration_seconds integer,
  created_at timestamp with time zone default now()
);

-- ============================================
-- ROW LEVEL SECURITY (RLS)
-- ============================================

-- Enable RLS on all tables
alter table public.profiles enable row level security;
alter table public.usage_logs enable row level security;

-- Profiles policies
create policy "Users can view own profile"
  on public.profiles for select
  using (auth.uid() = id);

create policy "Users can update own profile"
  on public.profiles for update
  using (auth.uid() = id);

create policy "Users can insert own profile"
  on public.profiles for insert
  with check (auth.uid() = id);

-- Usage logs policies
create policy "Users can view own usage logs"
  on public.usage_logs for select
  using (auth.uid() = user_id);

create policy "Users can insert own usage logs"
  on public.usage_logs for insert
  with check (auth.uid() = user_id);

-- ============================================
-- FUNCTIONS
-- ============================================

-- Function to automatically create profile on user signup
create or replace function public.handle_new_user()
returns trigger
language plpgsql
security definer set search_path = public
as $$
begin
  insert into public.profiles (id, email, full_name)
  values (
    new.id,
    new.email,
    coalesce(new.raw_user_meta_data->>'full_name', split_part(new.email, '@', 1))
  );
  return new;
end;
$$;

-- Trigger to call function on new user
drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
  after insert on auth.users
  for each row execute procedure public.handle_new_user();

-- Function to reset monthly meeting count
create or replace function public.reset_monthly_meetings()
returns void
language plpgsql
security definer
as $$
begin
  update public.profiles
  set
    meetings_this_month = 0,
    meetings_reset_date = date_trunc('month', now()) + interval '1 month'
  where meetings_reset_date <= now();
end;
$$;

-- Function to increment meeting count (called by edge function)
create or replace function public.increment_meeting_count(user_uuid uuid)
returns json
language plpgsql
security definer
as $$
declare
  profile_record record;
  meeting_limit integer;
begin
  -- Reset monthly counts if needed
  perform public.reset_monthly_meetings();

  -- Get current profile
  select * into profile_record
  from public.profiles
  where id = user_uuid;

  if not found then
    return json_build_object('error', 'Profile not found');
  end if;

  -- Determine meeting limit based on tier
  if profile_record.subscription_tier = 'pro' then
    meeting_limit := 999999; -- Effectively unlimited
  else
    meeting_limit := 3; -- Free tier limit
  end if;

  -- Check if limit reached
  if profile_record.meetings_this_month >= meeting_limit then
    return json_build_object(
      'error', 'limit_reached',
      'current', profile_record.meetings_this_month,
      'limit', meeting_limit,
      'tier', profile_record.subscription_tier
    );
  end if;

  -- Increment count
  update public.profiles
  set
    meetings_this_month = meetings_this_month + 1,
    updated_at = now()
  where id = user_uuid;

  return json_build_object(
    'success', true,
    'meetings_used', profile_record.meetings_this_month + 1,
    'meetings_limit', meeting_limit,
    'tier', profile_record.subscription_tier
  );
end;
$$;

-- ============================================
-- INDEXES
-- ============================================
create index if not exists idx_profiles_email on public.profiles(email);
create index if not exists idx_profiles_dodo_customer on public.profiles(dodo_customer_id);
create index if not exists idx_usage_logs_user_id on public.usage_logs(user_id);
create index if not exists idx_usage_logs_created_at on public.usage_logs(created_at);

-- ============================================
-- GRANTS
-- ============================================
grant usage on schema public to anon, authenticated;
grant all on public.profiles to anon, authenticated;
grant all on public.usage_logs to anon, authenticated;
