import { createRouteHandlerClient } from '@supabase/auth-helpers-nextjs';
import { cookies } from 'next/headers';
import Stripe from 'stripe';
import { getStripeServer } from '@/lib/stripe/config';

// Initialize Stripe
const stripeTemp = getStripeServer();
if (!stripeTemp) {
  throw new Error('Failed to initialize Stripe');
}
const stripe = stripeTemp;

// This is your Stripe webhook secret for testing your endpoint locally.
const webhookSecret = process.env.STRIPE_WEBHOOK_SECRET!;

// Export config
export const dynamic = 'force-dynamic';

// Remove unused type definition

// Handle OPTIONS request for CORS
export async function OPTIONS() {
  return new Response(null, {
    status: 204,
    headers: {
      'Allow': 'POST',
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'POST',
      'Access-Control-Allow-Headers': 'Content-Type, stripe-signature',
      'Access-Control-Max-Age': '86400',
    },
  });
}

export async function POST(req: Request) {
  try {
    // Get the raw body and signature
    const body = await req.text();
    const signature = req.headers.get('stripe-signature');
    
    console.log('Webhook received:');
    console.log('- Secret:', webhookSecret);
    console.log('- Signature:', signature);
    console.log('- Body length:', body.length);
    
    if (!signature) {
      console.log('No signature found in headers');
      return new Response('No signature found', { status: 400 });
    }

    // Verify webhook signature
    let event: Stripe.Event;
    try {
      event = await stripe.webhooks.constructEventAsync(
        body,
        signature,
        webhookSecret
      );
      console.log('✅ Webhook signature verified for event:', event.type);
    } catch (err) {
      console.error('❌ Webhook signature verification failed:', err);
      return new Response('Invalid signature', { status: 400 });
    }

    // Handle the event
    const cookieStore = cookies();
    const supabase = createRouteHandlerClient({ cookies: () => cookieStore });

    switch (event.type) {
      case 'checkout.session.completed': {
        const session = event.data.object as Stripe.Checkout.Session;
        
        // Only handle subscription checkouts
        if (session.mode !== 'subscription') {
          return new Response(JSON.stringify({ received: true }), {
            status: 200,
            headers: {
              'Content-Type': 'application/json',
            },
          });
        }

        console.log('Processing checkout session:', {
          session_id: session.id,
          subscription_id: session.subscription,
          client_reference_id: session.client_reference_id,
          metadata: session.metadata
        });

        // Get user ID from metadata if client_reference_id is null
        const userId = session.client_reference_id || session.metadata?.userId;
        
        if (!userId) {
          console.error('No user ID found in session');
          return new Response(JSON.stringify({
            error: 'Missing user ID',
            message: 'Neither client_reference_id nor metadata.userId found'
          }), { status: 400 });
        }

        // Get subscription details
        const subscriptionData = await stripe.subscriptions.retrieve(session.subscription as string);
        
        console.log('Retrieved subscription:', {
          id: subscriptionData.id,
          status: subscriptionData.status,
          current_period_start: 'timestamp_available',
          current_period_end: 'timestamp_available'
        });

        // Create dates with proper error handling
        let startDate: Date, endDate: Date;
        
        try {
          // Check if the timestamps exist and are valid numbers
          const subscription = subscriptionData as unknown as { current_period_start: number; current_period_end: number };
          const startTimestamp = subscription.current_period_start;
          const endTimestamp = subscription.current_period_end;
          
          if (!startTimestamp || !endTimestamp || startTimestamp === 0 || endTimestamp === 0) {
            // If timestamps are missing, use current time and add 30 days
            console.log('Using fallback dates as subscription timestamps are missing');
            startDate = new Date();
            endDate = new Date(Date.now() + (30 * 24 * 60 * 60 * 1000)); // 30 days from now
          } else {
            startDate = new Date(startTimestamp * 1000);
            endDate = new Date(endTimestamp * 1000);
            
            // Validate the dates
            if (isNaN(startDate.getTime()) || isNaN(endDate.getTime())) {
              throw new Error(`Invalid timestamps: start=${startTimestamp}, end=${endTimestamp}`);
            }
          }
          
          console.log('Using dates:', {
            start: startDate.toISOString(),
            end: endDate.toISOString()
          });
          
        } catch (dateError) {
          console.error('Date conversion error:', dateError);
          return new Response(JSON.stringify({
            error: 'Date conversion failed',
            message: dateError instanceof Error ? dateError.message : 'Unknown date error',
            subscription_id: subscriptionData.id
          }), { status: 500 });
        }

        // No need to check if user exists - the foreign key constraint will handle it
        // If user doesn't exist in auth.users, the insert will fail gracefully

        // Check if subscription already exists
        const { data: existingSubscription } = await supabase
          .from('subscriptions')
          .select('id')
          .eq('stripe_subscription_id', subscriptionData.id)
          .single();

        if (existingSubscription) {
          console.log(`Subscription ${subscriptionData.id} already exists, updating instead`);
          
          const { error: updateError } = await supabase
            .from('subscriptions')
            .update({
              status: subscriptionData.status,
              current_period_start: startDate.toISOString(),
              current_period_end: endDate.toISOString(),
            })
            .eq('stripe_subscription_id', subscriptionData.id);

          if (updateError) {
            console.error('Error updating subscription:', updateError);
            return new Response(JSON.stringify({ error: 'Database update error' }), { status: 500 });
          }
          
          console.log('✅ Subscription updated successfully');
        } else {
          // Create new subscription record
          const { error } = await supabase
            .from('subscriptions')
            .insert({
              user_id: userId,
              status: subscriptionData.status,
              stripe_customer_id: session.customer,
              stripe_subscription_id: subscriptionData.id,
              current_period_start: startDate.toISOString(),
              current_period_end: endDate.toISOString(),
            });

          if (error) {
            console.error('Error inserting subscription:', error);
            
            // If it's a foreign key constraint error (user doesn't exist), return 200 to stop retries
            if (error.code === '23503') {
              console.log(`User ${userId} not found in auth.users, skipping webhook`);
              return new Response(JSON.stringify({ 
                received: true, 
                message: 'User not found in auth system, webhook skipped' 
              }), { status: 200 });
            }
            
            return new Response(JSON.stringify({ error: 'Database error' }), { status: 500 });
          }
          
          console.log('✅ Subscription record created successfully');
        }

        console.log('✅ Subscription record created successfully');
        break;
      }

      case 'customer.subscription.updated': {
        const subscription = event.data.object as Stripe.Subscription;
        
        // Only process if status changed
        const previousAttributes = event.data.previous_attributes as Partial<Stripe.Subscription>;
        if (!previousAttributes.status) {
          console.log('Ignoring subscription update - no status change');
          return new Response(JSON.stringify({ received: true }), {
            status: 200,
            headers: {
              'Content-Type': 'application/json',
            },
          });
        }

        console.log(`Subscription status changed from ${previousAttributes.status} to ${subscription.status}`);
        
        // Get subscription details for period updates (in case plan changed too)
        const subscriptionWithPeriod = subscription as unknown as { current_period_start: number; current_period_end: number };
        const startDate = new Date(subscriptionWithPeriod.current_period_start * 1000);
        const endDate = new Date(subscriptionWithPeriod.current_period_end * 1000);

        // Update subscription with new status and period info
        const { error } = await supabase
          .from('subscriptions')
          .update({
            status: subscription.status,
            current_period_start: startDate.toISOString(),
            current_period_end: endDate.toISOString(),
          })
          .eq('stripe_subscription_id', subscription.id);

        if (error) {
          console.error('Error updating subscription:', error);
          return new Response(JSON.stringify({ error: 'Database error' }), { status: 500 });
        }
        break;
      }

      case 'customer.subscription.deleted': {
        const subscription = event.data.object as Stripe.Subscription;
        
        // Update subscription status to canceled
        const { error } = await supabase
          .from('subscriptions')
          .update({
            status: subscription.status,
          })
          .eq('stripe_subscription_id', subscription.id);

        if (error) {
          console.error('Error updating subscription:', error);
          return new Response(JSON.stringify({ error: 'Database error' }), { status: 500 });
        }
        break;
      }

      case 'invoice.paid': {
        const invoice = event.data.object as Stripe.Invoice;
        const invoiceWithSub = invoice as unknown as { subscription: string };
        const subscriptionId = invoiceWithSub.subscription;
        
        if (!subscriptionId) {
          return new Response(JSON.stringify({ received: true }), {
            status: 200,
            headers: {
              'Content-Type': 'application/json',
            },
          });
        }

        // Get the subscription to update the period
        const subscription = await stripe.subscriptions.retrieve(subscriptionId);
        
        // Update subscription period
        const subWithPeriod = subscription as unknown as { current_period_start: number; current_period_end: number };
        const startDate = new Date(subWithPeriod.current_period_start * 1000);
        const endDate = new Date(subWithPeriod.current_period_end * 1000);

        const { error } = await supabase
          .from('subscriptions')
          .update({
            current_period_start: startDate.toISOString(),
            current_period_end: endDate.toISOString(),
          })
          .eq('stripe_subscription_id', subscriptionId);

        if (error) {
          console.error('Error updating subscription period:', error);
          return new Response(JSON.stringify({ error: 'Database error' }), { status: 500 });
        }
        break;
      }

      case 'invoice.payment_failed': {
        const invoice = event.data.object as Stripe.Invoice;
        const invoiceWithSub = invoice as unknown as { subscription: string };
        const subscriptionId = invoiceWithSub.subscription;
        
        if (!subscriptionId) {
          return new Response(JSON.stringify({ received: true }), {
            status: 200,
            headers: {
              'Content-Type': 'application/json',
            },
          });
        }

        // Log the failure - the subscription.updated webhook will handle the status change
        console.log(`Payment failed for subscription ${subscriptionId}`);
        break;
      }
    }

    return new Response(JSON.stringify({ received: true }), {
      status: 200,
      headers: {
        'Content-Type': 'application/json',
      },
    });

  } catch (err) {
    console.error('Error processing webhook:', err);
    const errorMessage = err instanceof Error ? err.message : 'Unknown error';
    console.error('Detailed error:', errorMessage);
    
    return new Response(
      JSON.stringify({ 
        error: 'Webhook Error', 
        message: errorMessage,
        timestamp: new Date().toISOString()
      }), 
      { 
        status: 500,
        headers: {
          'Content-Type': 'application/json'
        }
      }
    );
  }
} 