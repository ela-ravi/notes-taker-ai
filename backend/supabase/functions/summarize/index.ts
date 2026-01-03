// Supabase Edge Function: Groq API Proxy with Authentication
// Handles LLM requests, checks subscription status, and tracks usage

import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from "https://esm.sh/@supabase/supabase-js@2"

const GROQ_API_KEY = Deno.env.get('GROQ_API_KEY')
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

    // Create Supabase client with service role for admin operations
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

    // Check subscription and increment meeting count
    const { data: usageResult, error: usageError } = await supabase
      .rpc('increment_meeting_count', { user_uuid: user.id })

    if (usageError) {
      console.error('Usage check error:', usageError)
      return new Response(
        JSON.stringify({ error: 'Failed to check usage' }),
        { status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      )
    }

    if (usageResult.error === 'limit_reached') {
      return new Response(
        JSON.stringify({
          error: 'Free tier limit reached',
          code: 'LIMIT_REACHED',
          current: usageResult.current,
          limit: usageResult.limit,
          tier: usageResult.tier,
          message: 'You have reached your free tier limit of 3 meetings per month. Upgrade to Pro for unlimited meetings.'
        }),
        { status: 402, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      )
    }

    // Parse request body
    const body = await req.json()
    const { meeting_title, ...groqPayload } = body

    // Proxy request to Groq
    const groqResponse = await fetch('https://api.groq.com/openai/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${GROQ_API_KEY}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(groqPayload),
    })

    const groqData = await groqResponse.json()

    // Log usage (fire and forget)
    supabase.from('usage_logs').insert({
      user_id: user.id,
      meeting_title: meeting_title || 'Untitled Meeting',
      tokens_used: groqData.usage?.total_tokens || 0,
      model_used: groqPayload.model || 'unknown',
    }).then(() => {}).catch(console.error)

    // Return Groq response with usage info
    return new Response(
      JSON.stringify({
        ...groqData,
        _usage_info: {
          meetings_used: usageResult.meetings_used,
          meetings_limit: usageResult.meetings_limit,
          tier: usageResult.tier,
        }
      }),
      {
        status: groqResponse.status,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      }
    )

  } catch (error) {
    console.error('Summarize function error:', error)
    return new Response(
      JSON.stringify({ error: 'Internal server error', details: error.message }),
      { status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    )
  }
})
