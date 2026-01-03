// Supabase Edge Function: Dodo Payments Checkout Session
// Creates a checkout session for subscription upgrade

import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from "https://esm.sh/@supabase/supabase-js@2"

const DODO_API_KEY = Deno.env.get('DODO_API_KEY')
const DODO_API_URL = 'https://api.dodopayments.com/v1'
const SUPABASE_URL = Deno.env.get('SUPABASE_URL')
const SUPABASE_SERVICE_KEY = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

serve(async (req) => {
  // Handle CORS preflight
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  try {
    // Verify authorization header
    const authHeader = req.headers.get('Authorization')
    if (!authHeader) {
      return new Response(
        JSON.stringify({ error: 'Missing authorization header' }),
        { status: 401, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      )
    }

    // Create Supabase client
    const supabase = createClient(SUPABASE_URL!, SUPABASE_SERVICE_KEY!)

    // Verify user token
    const token = authHeader.replace('Bearer ', '')
    const { data: { user }, error: authError } = await supabase.auth.getUser(token)

    if (authError || !user) {
      return new Response(
        JSON.stringify({ error: 'Invalid or expired token' }),
        { status: 401, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      )
    }

    // Get user profile
    const { data: profile } = await supabase
      .from('profiles')
      .select('*')
      .eq('id', user.id)
      .single()

    // Parse request body
    const { product_id, success_url, cancel_url } = await req.json()

    if (!product_id) {
      return new Response(
        JSON.stringify({ error: 'Missing product_id' }),
        { status: 400, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      )
    }

    // Create Dodo Payments checkout session
    // Note: Adjust this based on actual Dodo Payments API
    const checkoutResponse = await fetch(`${DODO_API_URL}/checkout/sessions`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${DODO_API_KEY}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        product_id: product_id,
        customer_email: user.email,
        metadata: {
          user_id: user.id,
          supabase_user_id: user.id,
        },
        success_url: success_url || 'meetingnotes://subscription-success',
        cancel_url: cancel_url || 'meetingnotes://subscription-cancel',
      }),
    })

    if (!checkoutResponse.ok) {
      const errorData = await checkoutResponse.text()
      console.error('Dodo Payments error:', errorData)
      return new Response(
        JSON.stringify({ error: 'Failed to create checkout session' }),
        { status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      )
    }

    const checkoutData = await checkoutResponse.json()

    // Update profile with Dodo customer ID if provided
    if (checkoutData.customer_id && !profile?.dodo_customer_id) {
      await supabase
        .from('profiles')
        .update({ dodo_customer_id: checkoutData.customer_id })
        .eq('id', user.id)
    }

    return new Response(
      JSON.stringify({
        checkout_url: checkoutData.url,
        session_id: checkoutData.id,
      }),
      { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    )

  } catch (error) {
    console.error('Create checkout error:', error)
    return new Response(
      JSON.stringify({ error: 'Internal server error', details: error.message }),
      { status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    )
  }
})
