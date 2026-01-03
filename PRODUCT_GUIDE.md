# Meeting Notes Taker - Product Guide

## Overview

Meeting Notes Taker is a desktop application that automatically captures, transcribes, and summarizes meetings in real-time using AI. It's designed as a SaaS product with subscription-based monetization.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           DESKTOP APPLICATION                            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │
│  │   Audio     │  │  Whisper    │  │    LLM      │  │   Notes     │    │
│  │  Capture    │──▶│Transcription│──▶│ Summarizer │──▶│  Generator  │    │
│  │ (BlackHole) │  │  (Local)    │  │  (Cloud)    │  │  (MD/HTML)  │    │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘    │
│                                           │                              │
│  ┌─────────────┐                          │                              │
│  │    Auth     │                          │                              │
│  │  Manager    │──────────────────────────┼──────────────────────────────│
│  └─────────────┘                          │                              │
└───────────────────────────────────────────┼──────────────────────────────┘
                                            │
                                            ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                              SUPABASE BACKEND                            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │
│  │    Auth     │  │  Database   │  │    Edge     │  │   Webhook   │    │
│  │  (Email/    │  │ (Profiles,  │  │  Functions  │  │  (Payment   │    │
│  │  Password)  │  │  Usage)     │  │ (Groq Proxy)│  │  Events)    │    │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘    │
└───────────────────────────────────────────┼──────────────────────────────┘
                                            │
                    ┌───────────────────────┼───────────────────────┐
                    ▼                       ▼                       ▼
            ┌─────────────┐         ┌─────────────┐         ┌─────────────┐
            │   Groq API  │         │    Dodo     │         │  PostgreSQL │
            │  (Fast LLM) │         │  Payments   │         │  (Supabase) │
            └─────────────┘         └─────────────┘         └─────────────┘
```

## Features

### Core Features

| Feature | Description |
|---------|-------------|
| **Live Audio Capture** | Captures system audio via BlackHole (Mac) or VB-Cable (Windows) |
| **Real-time Transcription** | Uses OpenAI Whisper for accurate speech-to-text |
| **Speaker Diarization** | Identifies different speakers in the meeting |
| **AI Summarization** | Generates concise meeting summaries using LLM |
| **Action Item Extraction** | Automatically extracts tasks and assigns owners |
| **Decision Tracking** | Identifies and documents decisions made |
| **Meeting Type Detection** | Classifies meetings (standup, planning, review, etc.) |
| **Multi-format Export** | Outputs notes in Markdown and HTML formats |

### SaaS Features

| Feature | Description |
|---------|-------------|
| **User Authentication** | Email/password signup and login via Supabase |
| **Subscription Tiers** | Free (3 meetings/month) and Pro (unlimited) |
| **Usage Tracking** | Monitors meetings per user per month |
| **Payment Integration** | Dodo Payments for subscription billing |
| **Secure API Proxy** | Edge Function protects API keys from exposure |

### LLM Providers

| Provider | Type | Best For |
|----------|------|----------|
| **Cloud (Subscription)** | SaaS | Production users - uses your Groq API via backend |
| **Groq** | Cloud | Direct API access - fast & cheap |
| **Ollama** | Local | Privacy-focused users - runs on device |
| **HuggingFace** | Cloud | Alternative cloud option |

---

## User Journeys

### Journey 1: New User Signup

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  Open App    │────▶│ Login Screen │────▶│  Click       │────▶│ Enter Email  │
│              │     │  Displayed   │     │  "Sign Up"   │     │ & Password   │
└──────────────┘     └──────────────┘     └──────────────┘     └──────────────┘
                                                                       │
                                                                       ▼
┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  Main App    │◀────│   Profile    │◀────│   Confirm    │◀────│  Check       │
│  Ready       │     │   Created    │     │   Email      │     │  Email Inbox │
└──────────────┘     └──────────────┘     └──────────────┘     └──────────────┘
```

### Journey 2: Recording a Meeting

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  Select or   │────▶│ Configure    │────▶│   Click      │────▶│  Meeting     │
│  Create      │     │  Audio       │     │  "Start      │     │  Recording   │
│  Preset      │     │  Settings    │     │  Recording"  │     │  In Progress │
└──────────────┘     └──────────────┘     └──────────────┘     └──────────────┘
                                                                       │
                                                                       ▼
┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  Open Notes  │◀────│   Notes      │◀────│    AI        │◀────│   Click      │
│  in Browser  │     │  Generated   │     │ Summarizes   │     │   "Stop"     │
│  (HTML)      │     │  (MD + HTML) │     │  Transcript  │     │              │
└──────────────┘     └──────────────┘     └──────────────┘     └──────────────┘
```

### Journey 3: Free User Hits Limit

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  User has    │────▶│ Tries to     │────▶│  Error:      │────▶│ Subscription │
│  used 3      │     │  Start 4th   │     │  "Limit      │     │  Screen      │
│  meetings    │     │  Meeting     │     │  Reached"    │     │  Shown       │
└──────────────┘     └──────────────┘     └──────────────┘     └──────────────┘
                                                                       │
                                                                       ▼
┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  Unlimited   │◀────│  Webhook     │◀────│  Complete    │◀────│   Click      │
│  Access      │     │  Updates     │     │  Payment     │     │  "Upgrade"   │
│  Granted     │     │  Profile     │     │  Flow        │     │              │
└──────────────┘     └──────────────┘     └──────────────┘     └──────────────┘
```

### Journey 4: Returning User

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  Open App    │────▶│   Session    │────▶│  Main App    │
│              │     │   Restored   │     │  Ready       │
│              │     │  (Auto-login)│     │              │
└──────────────┘     └──────────────┘     └──────────────┘
```

---

## Subscription Tiers

| Feature | Free | Pro ($10/month) |
|---------|------|-----------------|
| Meetings per month | 3 | Unlimited |
| AI Summarization | Yes | Yes |
| Action Items | Yes | Yes |
| Decision Tracking | Yes | Yes |
| Speaker Diarization | Yes | Yes |
| Export (MD + HTML) | Yes | Yes |
| Priority Support | No | Yes |

---

## Monitoring & Analytics

### 1. Supabase Dashboard

Access your Supabase dashboard to monitor:

**URL:** https://supabase.com/dashboard/project/YOUR_PROJECT_REF

#### User Management
- **Authentication > Users**: View all registered users
- See signup dates, last sign-in, email confirmation status

#### Database Analytics
Navigate to **Table Editor** to view:

**`profiles` table:**
| Column | Description |
|--------|-------------|
| `id` | User UUID |
| `email` | User email |
| `subscription_tier` | 'free' or 'pro' |
| `subscription_status` | 'active', 'canceled', 'past_due', 'expired' |
| `meetings_this_month` | Current month usage |
| `meetings_reset_date` | When counter resets |
| `dodo_customer_id` | Payment customer ID |
| `created_at` | Registration date |

**`usage_logs` table:**
| Column | Description |
|--------|-------------|
| `id` | Log entry UUID |
| `user_id` | User who made the request |
| `meeting_title` | Title of the meeting |
| `tokens_used` | LLM tokens consumed |
| `model_used` | Which model was used |
| `created_at` | Timestamp |

### 2. SQL Queries for Analytics

Run these in **SQL Editor** (https://supabase.com/dashboard/project/_/sql):

#### Total Users
```sql
SELECT COUNT(*) as total_users FROM public.profiles;
```

#### Users by Subscription Tier
```sql
SELECT
  subscription_tier,
  COUNT(*) as user_count
FROM public.profiles
GROUP BY subscription_tier;
```

#### Monthly Active Users (meetings recorded)
```sql
SELECT
  DATE_TRUNC('month', created_at) as month,
  COUNT(DISTINCT user_id) as active_users
FROM public.usage_logs
GROUP BY month
ORDER BY month DESC;
```

#### Total Meetings This Month
```sql
SELECT
  COUNT(*) as total_meetings,
  SUM(tokens_used) as total_tokens
FROM public.usage_logs
WHERE created_at >= DATE_TRUNC('month', NOW());
```

#### Top Users by Usage
```sql
SELECT
  p.email,
  p.subscription_tier,
  COUNT(u.id) as meetings_count,
  SUM(u.tokens_used) as total_tokens
FROM public.profiles p
LEFT JOIN public.usage_logs u ON p.id = u.user_id
GROUP BY p.id, p.email, p.subscription_tier
ORDER BY meetings_count DESC
LIMIT 10;
```

#### Revenue Potential (Free users at limit)
```sql
SELECT
  COUNT(*) as users_at_limit,
  COUNT(*) * 10 as potential_mrr
FROM public.profiles
WHERE subscription_tier = 'free'
  AND meetings_this_month >= 3;
```

### 3. Edge Function Logs

Monitor API calls and errors:

**URL:** https://supabase.com/dashboard/project/YOUR_PROJECT_REF/functions

- View invocation counts
- Check error rates
- See execution times
- Review logs for debugging

### 4. Dodo Payments Dashboard

Monitor payments and subscriptions:

- View active subscriptions
- Track revenue
- See failed payments
- Manage refunds

---

## File Structure

```
zoom-notes-taker/
├── backend/                      # Supabase backend
│   ├── supabase/
│   │   ├── functions/
│   │   │   ├── summarize/       # Groq API proxy
│   │   │   ├── create-checkout/ # Payment checkout
│   │   │   └── webhook/         # Payment webhooks
│   │   └── migrations/
│   │       └── 001_initial_schema.sql
│   └── README.md
│
├── src/
│   ├── audio/                   # Audio capture
│   ├── auth/                    # Authentication
│   │   ├── __init__.py
│   │   ├── supabase_client.py
│   │   └── auth_manager.py
│   ├── llm/                     # LLM providers
│   │   ├── base.py              # Abstract base class
│   │   ├── factory.py           # Provider factory
│   │   ├── cloud_client.py      # Supabase Edge proxy
│   │   ├── groq_client.py       # Direct Groq API
│   │   ├── ollama_client.py     # Local Ollama
│   │   ├── huggingface_client.py
│   │   ├── summarizer.py        # Meeting summarization
│   │   └── prompts.py           # LLM prompts
│   ├── notes/                   # Notes generation
│   │   ├── generator.py         # Main pipeline
│   │   ├── models.py            # Data models
│   │   └── templates.py         # Output templates
│   ├── transcription/           # Speech-to-text
│   ├── ui/                      # Desktop UI
│   │   ├── app.py               # Main application
│   │   └── login_screen.py      # Auth UI
│   └── config.py                # Configuration
│
├── .env                         # Environment variables
├── .env.example                 # Example config
├── pyproject.toml               # Dependencies
└── PRODUCT_GUIDE.md            # This file
```

---

## Environment Variables

### Desktop App (.env)

```bash
# Supabase (required for SaaS mode)
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_ANON_KEY=eyJ...

# Dodo Payments
DODO_PRODUCT_ID=your_product_id

# Audio
ZNT_AUDIO_DEVICE="Aggregate Device"

# Whisper
ZNT_WHISPER_MODEL=base

# LLM (for local/direct mode)
GROQ_API_KEY=gsk_...          # Optional if using cloud mode
```

### Supabase Secrets

```bash
supabase secrets set GROQ_API_KEY=gsk_...
supabase secrets set DODO_API_KEY=...
supabase secrets set DODO_WEBHOOK_SECRET=...
```

---

## Cost Analysis

### Per-Meeting Costs (Cloud Mode)

| Component | Cost |
|-----------|------|
| Groq API (8K tokens avg) | ~$0.0005 |
| Supabase (within free tier) | $0.00 |
| Total per meeting | ~$0.001 |

### Revenue Model

| Tier | Price | Margin per Meeting |
|------|-------|-------------------|
| Free | $0 | -$0.001 (up to 3) |
| Pro | $10/month | ~$9.99 (unlimited usage) |

### Break-even Analysis

- Free tier cost: 3 meetings × $0.001 = $0.003/user/month
- Pro subscriber using 100 meetings: $0.10 cost, $9.90 profit
- Target: Convert 5% of free users to Pro

---

## Security Considerations

1. **API Keys**: Never exposed to client - proxied through Edge Functions
2. **Authentication**: Supabase handles secure auth with JWT tokens
3. **Row Level Security**: Users can only access their own data
4. **Session Management**: Tokens stored securely, auto-refresh enabled
5. **Payment Security**: Handled by Dodo Payments (PCI compliant)

---

## Troubleshooting

### Login Issues
- Check SUPABASE_URL and SUPABASE_ANON_KEY in .env
- Verify email confirmation if signup doesn't work
- Check Supabase Auth logs for errors

### Recording Issues
- Ensure audio device is properly configured
- Check that BlackHole/VB-Cable is installed
- Verify microphone permissions

### Summarization Errors
- Check Edge Function logs in Supabase dashboard
- Verify GROQ_API_KEY secret is set
- Check usage limits on Groq console

### Payment Issues
- Verify DODO_API_KEY and webhook secrets
- Check webhook endpoint is accessible
- Review Dodo Payments dashboard for failed payments
