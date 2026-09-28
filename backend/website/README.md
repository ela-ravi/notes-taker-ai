# Meeting Notes Taker - Website Files

This directory contains static HTML pages for the payment flow.

## Pages

### `subscription-success.html`
Success page shown after a user completes payment. Features:
- Animated checkmark confirmation
- Pro plan details
- Auto-closes after 5 seconds
- Redirects user back to the app

**URL**: `https://yourdomain.com/subscription-success?user_id={user_id}`

### `subscription-cancelled.html`
Cancellation page shown when a user cancels the checkout. Features:
- Clear messaging that no charges were made
- Option to retry upgrade
- Free plan reminder
- Auto-closes after 10 seconds

**URL**: `https://yourdomain.com/subscription-cancelled`

## Deployment

These pages need to be hosted on a web server or static hosting service:

### Option 1: Netlify/Vercel (Recommended)
1. Create a new site on Netlify or Vercel
2. Point it to this `backend/website` directory
3. Deploy
4. Update `WEBSITE_URL` environment variable in Supabase Edge Functions

### Option 2: Supabase Storage (Simple)
1. Upload files to Supabase Storage bucket with public access
2. Use the public URLs in the create-checkout Edge Function

### Option 3: Custom Domain
1. Host on your own web server (nginx, Apache, etc.)
2. Configure HTTPS with Let's Encrypt
3. Update DNS records

## Environment Variables

Update these in your Supabase Edge Functions:

```bash
# In backend/supabase/.env or Supabase Dashboard → Project Settings → Edge Functions
WEBSITE_URL=https://yourdomain.com
```

## Customization

Feel free to customize the HTML/CSS to match your brand:
- Update colors in the `<style>` sections
- Change messaging and copy
- Add your logo
- Modify auto-close timers

## Testing

Test locally:
```bash
# Serve with Python
cd backend/website
python3 -m http.server 8080

# Or with Node.js
npx serve .
```

Then visit:
- http://localhost:8080/subscription-success.html
- http://localhost:8080/subscription-cancelled.html
