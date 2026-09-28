# Payment Flow Testing Guide

This guide covers how to test the complete subscription payment flow from checkout to webhook handling.

## Overview

The payment flow consists of these steps:

1. User clicks "Upgrade Now" in the app
2. App calls `create-checkout` Edge Function
3. App opens browser to Dodo Payments checkout page
4. App starts polling for subscription status changes
5. User completes payment on Dodo Payments
6. Dodo Payments sends webhook to `webhook` Edge Function
7. Webhook updates user's subscription status in database
8. App detects status change through polling
9. App shows success message and refreshes UI

## Prerequisites

### 1. Supabase Setup

Ensure you have deployed all Edge Functions:

```bash
cd backend/supabase
supabase functions deploy create-checkout
supabase functions deploy webhook
supabase functions deploy summarize
```

### 2. Environment Variables

Set these in Supabase Dashboard → Project Settings → Edge Functions:

```bash
DODO_API_KEY=your_dodo_api_key
DODO_WEBHOOK_SECRET=your_webhook_secret
WEBSITE_URL=https://yourdomain.com  # Or your test URL
GROQ_API_KEY=your_groq_key
```

### 3. Dodo Payments Configuration

1. Log into Dodo Payments dashboard
2. Create a product (e.g., "Pro Plan - $10/month")
3. Note the `product_id`
4. Configure webhook URL: `https://your-project.supabase.co/functions/v1/webhook`
5. Set webhook secret and save it as `DODO_WEBHOOK_SECRET`

### 4. Website Hosting

Deploy the success/cancel pages:

**Option A: Quick Test (Local)**
```bash
cd backend/website
python3 -m http.server 8080

# Update WEBSITE_URL to http://localhost:8080
```

**Option B: Netlify (Production)**
```bash
# Install Netlify CLI
npm install -g netlify-cli

# Deploy
cd backend/website
netlify deploy --prod

# Update WEBSITE_URL to your Netlify URL
```

**Option C: Supabase Storage**
```bash
# Upload to public bucket
cd backend/website
supabase storage cp subscription-success.html supabase://public/subscription-success.html
supabase storage cp subscription-cancelled.html supabase://public/subscription-cancelled.html

# Get public URLs and update WEBSITE_URL
```

## Testing Procedure

### Test 1: Full Payment Flow (Happy Path)

1. **Start the App**
   ```bash
   python -m src.main start --title "Test Meeting"
   # Or use the GUI
   ./meeting-notes-ui.command
   ```

2. **Sign In**
   - Use a test account or create a new one
   - Verify you're on the Free plan (5 meetings/month limit)

3. **Navigate to Subscription**
   - Click the account/profile button
   - Click "View Subscription"
   - Verify you see "FREE" badge and "Upgrade to Pro" section

4. **Initiate Upgrade**
   - Click "Upgrade Now" button
   - Verify status message: "Creating checkout session..."
   - Verify status changes to: "Opening checkout in browser..."
   - Verify browser opens to Dodo Payments checkout page

5. **Check App Polling**
   - Look at app - it should say "Please complete your payment."
   - The app is now polling every 5 seconds for status changes

6. **Complete Payment** (Use Dodo's test mode)
   - Enter test credit card: `4242 4242 4242 4242`
   - Any future expiry date
   - Any CVV
   - Complete the checkout

7. **Verify Redirect**
   - Browser should redirect to your `subscription-success.html` page
   - Page should show checkmark animation and "Welcome to Pro!"
   - Page auto-closes after 5 seconds

8. **Verify Webhook**
   - Check Supabase logs: Functions → webhook → Logs
   - You should see: "User {user_id} upgraded to pro"
   - Check database:
     ```sql
     SELECT id, email, subscription_tier, subscription_status, dodo_customer_id
     FROM profiles
     WHERE email = 'your-test-email@example.com';
     ```
   - Verify `subscription_tier` = 'pro' and `subscription_status` = 'active'

9. **Verify App Updates**
   - After 5-10 seconds, app should detect the change
   - Status message: "🎉 Subscription activated! Refreshing..."
   - UI refreshes to show "PRO" badge
   - "Upgrade to Pro" section disappears
   - Usage shows "X / Unlimited meetings this month"

**Expected Result**: ✅ Full upgrade flow works end-to-end

---

### Test 2: Cancelled Payment

1. Follow steps 1-5 from Test 1
2. On Dodo checkout page, click "Cancel" or close the window
3. Verify browser redirects to `subscription-cancelled.html`
4. Verify message: "Subscription Cancelled"
5. Verify app stops polling after detecting no change (5 minutes timeout)
6. User remains on Free plan

**Expected Result**: ✅ Cancellation handled gracefully

---

### Test 3: Webhook Signature Verification

1. Send a fake webhook request without proper signature:
   ```bash
   curl -X POST https://your-project.supabase.co/functions/v1/webhook \
     -H "Content-Type: application/json" \
     -H "x-dodo-signature: fake-signature" \
     -d '{"type":"subscription.created","data":{"metadata":{"user_id":"test"}}}'
   ```

2. Check Supabase logs
3. Verify response: `401 Unauthorized` with "Invalid signature"

**Expected Result**: ✅ Webhook rejects unauthorized requests

---

### Test 4: Webhook Events

Test different webhook events by simulating them:

**Subscription Cancelled**
```bash
# Manually update database to simulate cancellation
UPDATE profiles 
SET subscription_tier = 'free', subscription_status = 'canceled'
WHERE id = 'your-user-id';
```

Verify app refreshes and shows Free plan again.

**Payment Failed**
```bash
UPDATE profiles 
SET subscription_status = 'past_due'
WHERE id = 'your-user-id';
```

**Subscription Renewed**
```bash
UPDATE profiles 
SET subscription_status = 'active'
WHERE id = 'your-user-id';
```

---

### Test 5: Polling Timeout

1. Start upgrade flow
2. **Do not complete payment**
3. Wait 5 minutes
4. Verify app shows: "Polling timed out. Please refresh to check status."
5. Verify polling thread stops (check CPU usage)

**Expected Result**: ✅ Polling gracefully times out

---

### Test 6: Error Scenarios

**Scenario A: Invalid Product ID**
- Modify app to use invalid `product_id`
- Attempt upgrade
- Verify error: "Failed to create checkout session"

**Scenario B: Expired Session**
- Sign in, then manually delete session token
- Attempt upgrade
- Verify error: "Please sign in again."

**Scenario C: Network Error**
- Disconnect internet
- Attempt upgrade
- Verify graceful error handling

---

## Debugging

### Check Edge Function Logs

```bash
# Via CLI
supabase functions logs webhook --tail
supabase functions logs create-checkout --tail

# Or in Dashboard
Supabase → Functions → Select function → Logs
```

### Check Database State

```sql
-- View all user profiles
SELECT * FROM profiles;

-- View usage logs
SELECT * FROM usage_logs ORDER BY created_at DESC LIMIT 10;

-- Check specific user
SELECT * FROM profiles WHERE email = 'test@example.com';
```

### Test Webhook Locally

```bash
# Install ngrok for local testing
ngrok http 54321

# Update Dodo webhook URL to ngrok URL
https://abc123.ngrok.io/functions/v1/webhook

# Test locally
supabase functions serve webhook
```

### Debug App Polling

Add print statements to `src/ui/login_screen.py`:

```python
def _poll_subscription_status(self) -> None:
    print(f"Starting polling, initial tier: {initial_tier}")
    while self._polling_active and poll_count < max_polls:
        print(f"Poll {poll_count}/{max_polls}")
        # ... rest of code
```

---

## Production Checklist

Before going live:

- [ ] Deploy website pages to production hosting
- [ ] Update `WEBSITE_URL` to production domain
- [ ] Configure Dodo Payments production mode
- [ ] Set production API keys
- [ ] Enable webhook signature verification (ensure it's not commented out)
- [ ] Test with real payment (small amount)
- [ ] Set up monitoring alerts
- [ ] Document support procedures for failed payments

---

## Common Issues

### Issue: Webhook never received

**Cause**: Incorrect webhook URL or firewall blocking

**Solution**:
1. Verify webhook URL in Dodo dashboard
2. Check Supabase Edge Function is deployed
3. Test webhook endpoint manually:
   ```bash
   curl https://your-project.supabase.co/functions/v1/webhook
   ```

### Issue: Polling doesn't detect change

**Cause**: Database not updated or polling stopped

**Solution**:
1. Check webhook logs for errors
2. Manually verify database was updated
3. Ensure polling thread is still running
4. Check for any exceptions in app logs

### Issue: "Invalid signature" errors

**Cause**: Webhook secret mismatch

**Solution**:
1. Verify `DODO_WEBHOOK_SECRET` matches Dodo dashboard
2. Check signature header name (`x-dodo-signature` vs `x-webhook-signature`)
3. Review signature verification algorithm

---

## Support

For issues:
1. Check Supabase logs
2. Check Dodo Payments dashboard for payment status
3. Verify database state
4. Review this testing guide
5. Contact support with log excerpts
