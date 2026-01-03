// Supabase Edge Function: Dodo Payments Webhook Handler
// Handles subscription events from Dodo Payments

import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from "https://esm.sh/@supabase/supabase-js@2"

const DODO_WEBHOOK_SECRET = Deno.env.get('DODO_WEBHOOK_SECRET')
const SUPABASE_URL = Deno.env.get('SUPABASE_URL')
const SUPABASE_SERVICE_KEY = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')

serve(async (req) => {
  try {
    // Verify webhook signature (adjust based on Dodo's signature method)
    const signature = req.headers.get('x-dodo-signature') || req.headers.get('x-webhook-signature')
    const body = await req.text()

    // TODO: Implement proper signature verification based on Dodo Payments docs
    // For now, we'll use a simple secret header check
    if (DODO_WEBHOOK_SECRET && signature !== DODO_WEBHOOK_SECRET) {
      console.warn('Invalid webhook signature')
      // In production, uncomment this:
      // return new Response('Invalid signature', { status: 401 })
    }

    const event = JSON.parse(body)
    console.log('Received webhook event:', event.type)

    // Create Supabase client
    const supabase = createClient(SUPABASE_URL!, SUPABASE_SERVICE_KEY!)

    // Handle different event types
    switch (event.type) {
      case 'checkout.completed':
      case 'subscription.created':
      case 'subscription.activated': {
        // User subscribed successfully
        const userId = event.data?.metadata?.user_id || event.data?.metadata?.supabase_user_id
        const customerId = event.data?.customer_id
        const subscriptionId = event.data?.subscription_id || event.data?.id

        if (userId) {
          const { error } = await supabase
            .from('profiles')
            .update({
              subscription_tier: 'pro',
              subscription_status: 'active',
              dodo_customer_id: customerId,
              dodo_subscription_id: subscriptionId,
              updated_at: new Date().toISOString(),
            })
            .eq('id', userId)

          if (error) {
            console.error('Failed to update profile:', error)
            return new Response(JSON.stringify({ error: 'Failed to update profile' }), { status: 500 })
          }

          console.log(`User ${userId} upgraded to pro`)
        }
        break
      }

      case 'subscription.canceled':
      case 'subscription.expired': {
        // User canceled or subscription expired
        const userId = event.data?.metadata?.user_id || event.data?.metadata?.supabase_user_id
        const customerId = event.data?.customer_id

        // Try to find user by customer ID if user_id not in metadata
        let targetUserId = userId
        if (!targetUserId && customerId) {
          const { data: profile } = await supabase
            .from('profiles')
            .select('id')
            .eq('dodo_customer_id', customerId)
            .single()
          targetUserId = profile?.id
        }

        if (targetUserId) {
          const { error } = await supabase
            .from('profiles')
            .update({
              subscription_tier: 'free',
              subscription_status: event.type === 'subscription.canceled' ? 'canceled' : 'expired',
              updated_at: new Date().toISOString(),
            })
            .eq('id', targetUserId)

          if (error) {
            console.error('Failed to update profile:', error)
            return new Response(JSON.stringify({ error: 'Failed to update profile' }), { status: 500 })
          }

          console.log(`User ${targetUserId} subscription ended`)
        }
        break
      }

      case 'subscription.payment_failed':
      case 'payment.failed': {
        // Payment failed
        const userId = event.data?.metadata?.user_id || event.data?.metadata?.supabase_user_id
        const customerId = event.data?.customer_id

        let targetUserId = userId
        if (!targetUserId && customerId) {
          const { data: profile } = await supabase
            .from('profiles')
            .select('id')
            .eq('dodo_customer_id', customerId)
            .single()
          targetUserId = profile?.id
        }

        if (targetUserId) {
          await supabase
            .from('profiles')
            .update({
              subscription_status: 'past_due',
              updated_at: new Date().toISOString(),
            })
            .eq('id', targetUserId)

          console.log(`User ${targetUserId} payment failed - marked as past_due`)
        }
        break
      }

      case 'subscription.renewed':
      case 'payment.succeeded': {
        // Successful renewal payment
        const userId = event.data?.metadata?.user_id || event.data?.metadata?.supabase_user_id
        const customerId = event.data?.customer_id

        let targetUserId = userId
        if (!targetUserId && customerId) {
          const { data: profile } = await supabase
            .from('profiles')
            .select('id')
            .eq('dodo_customer_id', customerId)
            .single()
          targetUserId = profile?.id
        }

        if (targetUserId) {
          await supabase
            .from('profiles')
            .update({
              subscription_status: 'active',
              updated_at: new Date().toISOString(),
            })
            .eq('id', targetUserId)

          console.log(`User ${targetUserId} subscription renewed`)
        }
        break
      }

      default:
        console.log(`Unhandled event type: ${event.type}`)
    }

    return new Response(JSON.stringify({ received: true }), {
      headers: { 'Content-Type': 'application/json' },
    })

  } catch (error) {
    console.error('Webhook error:', error)
    return new Response(
      JSON.stringify({ error: 'Webhook processing failed', details: error.message }),
      { status: 500, headers: { 'Content-Type': 'application/json' } }
    )
  }
})
