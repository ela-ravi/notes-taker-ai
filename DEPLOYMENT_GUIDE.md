# 🚀 Deployment Guide - Step by Step

This guide will walk you through deploying the payment flow to production.

**Estimated Time**: 2-3 hours for first-time setup

---

## Prerequisites Check

Before starting, ensure you have:

- [x] Supabase CLI installed (`/opt/homebrew/bin/supabase` ✓)
- [ ] Supabase account created at https://supabase.com
- [ ] Dodo Payments account created at https://dodopayments.com
- [ ] Domain or hosting for payment pages (Netlify/Vercel/etc)

---

## Phase 1: Supabase Setup (30 minutes)

### Step 1.1: Create/Access Supabase Project

1. Go to https://supabase.com/dashboard
2. Either use existing project or click "New Project"
3. Note your:
   - Project URL: `https://xxxxx.supabase.co`
   - Anon Key: `eyJhbGc...`
   - Service Role Key: `eyJhbGc...` (from Settings → API)
   - Project Reference ID: From Settings → General

### Step 1.2: Link Your Local Project

```bash
cd /Volumes/Development/zoom-notes-taker/backend/supabase

# Login to Supabase
supabase login

# Link to your project
supabase link --project-ref YOUR_PROJECT_REF
```

Replace `YOUR_PROJECT_REF` with your actual project reference.

### Step 1.3: Run Database Migration

**Option A: Via SQL Editor (Recommended)**

1. Open https://supabase.com/dashboard/project/_/sql
2. Copy contents of `backend/supabase/migrations/001_initial_schema.sql`
3. Paste into SQL Editor
4. Click "Run"
5. Verify tables created: `profiles`, `usage_logs`

**Option B: Via CLI**

```bash
cd /Volumes/Development/zoom-notes-taker/backend/supabase
supabase db push
```

### Step 1.4: Verify Database Setup

Run this query in SQL Editor to verify:

```sql
-- Check tables exist
SELECT tablename FROM pg_tables WHERE schemaname = 'public';

-- Should see: profiles, usage_logs

-- Check RLS policies
SELECT tablename, policyname FROM pg_policies WHERE schemaname = 'public';
```

---

## Phase 2: Dodo Payments Setup (20 minutes)

### Step 2.1: Create Dodo Account

1. Sign up at https://dodopayments.com (if you haven't already)
2. Complete account verification
3. Switch to **Test Mode** for initial testing

### Step 2.2: Create Product

1. Go to Products → Create Product
2. Set up your Pro plan:
   - **Name**: Meeting Notes Pro
   - **Price**: $10.00
   - **Billing Interval**: Monthly
   - **Description**: Unlimited meetings, priority support
3. Click "Create"
4. **Copy the Product ID** - you'll need this

### Step 2.3: Get API Keys

1. Go to Settings → API Keys
2. Copy:
   - **Test API Key** (starts with `test_`)
   - **Live API Key** (starts with `live_`) - save for later
3. Keep these secure!

### Step 2.4: Set Up Webhook

1. Go to Settings → Webhooks
2. Click "Add Endpoint"
3. Enter: `https://YOUR_PROJECT_REF.supabase.co/functions/v1/webhook`
   - Replace `YOUR_PROJECT_REF` with your actual Supabase project reference
4. Select events to listen for:
   - `checkout.completed`
   - `subscription.created`
   - `subscription.activated`
   - `subscription.canceled`
   - `subscription.expired`
   - `payment.succeeded`
   - `payment.failed`
5. Click "Create"
6. **Copy the Webhook Secret** - you'll need this

---

## Phase 3: Deploy Website Pages (30 minutes)

Choose ONE option:

### Option A: Netlify (Recommended - Easiest)

```bash
# Install Netlify CLI
npm install -g netlify-cli

# Deploy
cd /Volumes/Development/zoom-notes-taker/backend/website
netlify deploy --prod

# Follow prompts:
# - Create new site or link existing
# - Deploy path: . (current directory)
# - Copy the URL provided (e.g., https://your-site.netlify.app)
```

### Option B: Vercel

```bash
# Install Vercel CLI
npm install -g vercel

# Deploy
cd /Volumes/Development/zoom-notes-taker/backend/website
vercel --prod

# Follow prompts and copy the URL
```

### Option C: Supabase Storage (Quick Test)

```bash
cd /Volumes/Development/zoom-notes-taker/backend/supabase

# Create public bucket
supabase storage create --public payment-pages

# Upload files
supabase storage cp ../website/subscription-success.html supabase://payment-pages/subscription-success.html
supabase storage cp ../website/subscription-cancelled.html supabase://payment-pages/subscription-cancelled.html

# Get URLs:
# https://YOUR_PROJECT_REF.supabase.co/storage/v1/object/public/payment-pages/subscription-success.html
# https://YOUR_PROJECT_REF.supabase.co/storage/v1/object/public/payment-pages/subscription-cancelled.html
```

**Save your website URL** - you'll need it for environment variables.

---

## Phase 4: Set Environment Variables (10 minutes)

### Step 4.1: Set Supabase Secrets

```bash
cd /Volumes/Development/zoom-notes-taker/backend/supabase

# Dodo Payments API Key (use TEST key for now)
supabase secrets set DODO_API_KEY=test_your_key_here

# Dodo Webhook Secret
supabase secrets set DODO_WEBHOOK_SECRET=your_webhook_secret_here

# Website URL (from Phase 3)
supabase secrets set WEBSITE_URL=https://your-site.netlify.app

# Groq API Key (if you have one)
supabase secrets set GROQ_API_KEY=gsk_your_groq_key_here

# Verify secrets were set
supabase secrets list
```

### Step 4.2: Update Desktop App Config

Edit or create `/Volumes/Development/zoom-notes-taker/.env`:

```env
# Supabase
ZNT_SUPABASE_URL=https://YOUR_PROJECT_REF.supabase.co
ZNT_SUPABASE_ANON_KEY=your_anon_key_here

# Dodo Payments
ZNT_DODO_PRODUCT_ID=your_product_id_here

# Optional: For local LLM
ZNT_LLM_PROVIDER=cloud
ZNT_GROQ_API_KEY=gsk_your_key_here
```

---

## Phase 5: Deploy Edge Functions (15 minutes)

### Step 5.1: Deploy All Functions

```bash
cd /Volumes/Development/zoom-notes-taker/backend/supabase

# Deploy summarize function
supabase functions deploy summarize

# Deploy create-checkout function
supabase functions deploy create-checkout

# Deploy webhook function
supabase functions deploy webhook
```

You should see:
```
✓ Deployed Function summarize
✓ Deployed Function create-checkout
✓ Deployed Function webhook
```

### Step 5.2: Verify Functions Are Running

```bash
# List deployed functions
supabase functions list

# Should show:
# - summarize
# - create-checkout
# - webhook
```

### Step 5.3: Test Functions

**Test webhook endpoint:**

```bash
curl https://YOUR_PROJECT_REF.supabase.co/functions/v1/webhook \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"test":"data"}'

# Should return: {"error":"Invalid signature"} with status 401
# This is GOOD - it means security is working!
```

---

## Phase 6: Test the Payment Flow (30 minutes)

Now follow the complete testing guide:

👉 **Open `PAYMENT_TESTING_GUIDE.md`** and run **Test 1: Full Payment Flow**

Quick version:

1. **Start the app**:
   ```bash
   cd /Volumes/Development/zoom-notes-taker
   python -m src.main start --title "Test Meeting"
   ```

2. **Sign up / Sign in** with a test account

3. **Go to Subscription** → Click "Upgrade Now"

4. **Complete payment** with test card:
   - Card: `4242 4242 4242 4242`
   - Expiry: Any future date
   - CVV: Any 3 digits

5. **Verify upgrade** - Within 10-15 seconds, you should see:
   - Success page in browser
   - "🎉 Subscription activated!" in app
   - UI shows PRO badge

6. **Check logs**:
   ```bash
   # View webhook logs
   supabase functions logs webhook --tail
   
   # Check database
   supabase db query "SELECT email, subscription_tier, subscription_status FROM profiles"
   ```

---

## Phase 7: Go Live (When Ready)

### Before Going to Production:

1. **Switch Dodo to Live Mode**:
   - Dodo Dashboard → Settings → Switch to Live Mode
   - Update `DODO_API_KEY` secret with **live** key

2. **Run ALL tests** from `PAYMENT_TESTING_GUIDE.md`:
   - ✅ Test 1: Full payment flow
   - ✅ Test 2: Payment cancellation
   - ✅ Test 3: Webhook security
   - ✅ Test 4: Different webhook events
   - ✅ Test 5: Polling timeout
   - ✅ Test 6: Error scenarios

3. **Test with real payment** (use your own card, small amount)

4. **Monitor for 24 hours** - check Supabase logs regularly

5. **Set up alerts** - Configure Supabase to email you on errors

6. **Add legal docs** - Terms of Service, Privacy Policy (required!)

---

## Troubleshooting

### Issue: `supabase: command not found`

**Solution**:
```bash
# Ensure Supabase CLI is in PATH
export PATH="/opt/homebrew/bin:$PATH"

# Or install globally
npm install -g supabase
```

### Issue: "Failed to link project"

**Solution**:
```bash
# Make sure you're logged in
supabase login

# Get your project reference from:
# https://supabase.com/dashboard/project/_/settings/general
```

### Issue: "Edge Function deployment failed"

**Solution**:
```bash
# Check for syntax errors
cd backend/supabase/functions/webhook
deno check index.ts

# Redeploy with verbose logging
supabase functions deploy webhook --debug
```

### Issue: Webhook returns 401

**Good!** This means security is working. The error will only go away when Dodo sends a properly signed request.

### Issue: Payment completes but app doesn't update

**Check**:
1. Webhook was received: `supabase functions logs webhook`
2. Database was updated: Check `profiles` table
3. App is polling: Look for "Please complete your payment" message
4. Token is valid: Try refreshing or signing in again

---

## Next Steps

Once deployment is complete:

1. ✅ Deploy payment flow (you just did this!)
2. ⏳ Run comprehensive tests (`PAYMENT_TESTING_GUIDE.md`)
3. ⏳ Add legal documents (Terms, Privacy Policy)
4. ⏳ Set up email notifications
5. ⏳ Create landing page
6. ⏳ Launch! 🚀

See `LAUNCH_CHECKLIST.md` for complete roadmap.

---

## Quick Reference Commands

```bash
# Deploy all functions
cd /Volumes/Development/zoom-notes-taker/backend/supabase
supabase functions deploy summarize
supabase functions deploy create-checkout
supabase functions deploy webhook

# View logs
supabase functions logs webhook --tail

# Set secrets
supabase secrets set KEY=value

# Check database
supabase db query "SELECT * FROM profiles"

# Test locally (optional)
supabase functions serve webhook
```

---

## Support

- **Deployment Issues**: Re-read this guide, check Supabase logs
- **Payment Issues**: Check `PAYMENT_TESTING_GUIDE.md`
- **General Questions**: Check `START_HERE.md`

---

**Ready to deploy?** Let's start with Phase 1! 🚀

Run:
```bash
cd /Volumes/Development/zoom-notes-taker/backend/supabase
supabase login
```

Good luck!
