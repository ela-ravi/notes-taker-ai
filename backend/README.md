# Meeting Notes Taker - Backend

Supabase backend for authentication, subscription management, and LLM API proxy.

## Structure

```
backend/
├── supabase/
│   ├── functions/
│   │   ├── summarize/       # Groq API proxy with auth check
│   │   ├── create-checkout/ # Dodo Payments checkout session
│   │   └── webhook/         # Payment webhook handler
│   └── migrations/
│       └── 001_initial_schema.sql
└── README.md
```

## Setup

### 1. Install Supabase CLI

```bash
npm install -g supabase
```

### 2. Login and Link Project

```bash
supabase login
supabase link --project-ref YOUR_PROJECT_REF
```

Get your project ref from: https://supabase.com/dashboard/project/_/settings/general

### 3. Run Database Migrations

Copy the SQL from `migrations/001_initial_schema.sql` and run it in the Supabase SQL Editor:
https://supabase.com/dashboard/project/_/sql

### 4. Set Environment Secrets

```bash
supabase secrets set GROQ_API_KEY=gsk_your_key_here
supabase secrets set DODO_API_KEY=your_dodo_api_key
supabase secrets set DODO_WEBHOOK_SECRET=your_webhook_secret
```

### 5. Deploy Edge Functions

```bash
cd backend
supabase functions deploy summarize
supabase functions deploy create-checkout
supabase functions deploy webhook
```

## Environment Variables

### Edge Function Secrets (set via `supabase secrets set`)

| Variable | Description |
|----------|-------------|
| `GROQ_API_KEY` | Groq API key for LLM |
| `DODO_API_KEY` | Dodo Payments API key |
| `DODO_WEBHOOK_SECRET` | Webhook signing secret |

### Desktop App (.env)

```env
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_ANON_KEY=eyJhbGc...
```

## API Endpoints

### POST /functions/v1/summarize
Proxy to Groq API with authentication and usage tracking.

**Headers:**
- `Authorization: Bearer <supabase_access_token>`

**Body:**
```json
{
  "model": "llama-3.1-8b-instant",
  "messages": [...],
  "meeting_title": "Optional title"
}
```

### POST /functions/v1/create-checkout
Create a Dodo Payments checkout session.

**Headers:**
- `Authorization: Bearer <supabase_access_token>`

**Body:**
```json
{
  "product_id": "your_dodo_product_id"
}
```

### POST /functions/v1/webhook
Handle Dodo Payments webhooks.

## Subscription Tiers

| Tier | Price | Meetings/Month | Features |
|------|-------|----------------|----------|
| Free | $0 | 3 | Basic summarization |
| Pro | $10/month | Unlimited | All features |
