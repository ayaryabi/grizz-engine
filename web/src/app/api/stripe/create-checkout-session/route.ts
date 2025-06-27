import { NextResponse } from 'next/server';
import { getStripeServer, STRIPE_PRICE_ID } from '@/lib/stripe/config';
import { createClient } from '@supabase/supabase-js';
import type { Stripe } from 'stripe';

export async function POST(req: Request) {
  try {
    const stripe = getStripeServer();
    if (!stripe) {
      throw new Error('Failed to initialize Stripe');
    }

    // Get the session token from the request
    const authHeader = req.headers.get('authorization');
    if (!authHeader) {
      return NextResponse.json(
        { error: 'No authorization header' },
        { status: 401 }
      );
    }

    // Initialize Supabase client
    const supabase = createClient(
      process.env.NEXT_PUBLIC_SUPABASE_URL!,
      process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
      {
        auth: {
          autoRefreshToken: false,
          persistSession: false
        }
      }
    );

    // Get user data using the session token
    const { data: { user }, error: userError } = await supabase.auth.getUser(authHeader.replace('Bearer ', ''));
    
    if (userError || !user?.email) {
      return NextResponse.json(
        { error: 'User not authenticated' },
        { status: 401 }
      );
    }

    // First, search for ALL customers with this email (in case of duplicates)
    const allCustomers = await stripe.customers.list({
      email: user.email,
      limit: 100, // Increased limit to catch all possible duplicates
    });

    // If multiple customers found, we'll use the oldest one
    let stripeCustomerId: string;
    let existingCustomer: Stripe.Customer | null = null;

    if (allCustomers.data.length > 0) {
      // Sort by creation date ascending (oldest first)
      const sortedCustomers = allCustomers.data.sort((a, b) => a.created - b.created);
      existingCustomer = sortedCustomers[0];
      stripeCustomerId = existingCustomer.id;

      // Check ALL subscription statuses that could indicate an active subscription
      const allSubscriptions = await stripe.subscriptions.list({
        customer: stripeCustomerId,
        status: 'all', // Get all subscriptions to check their status
        limit: 100,
      });

      // Check for any subscription that's not canceled or incomplete_expired
      const activeOrPendingSubscription = allSubscriptions.data.find(sub => 
        ['active', 'trialing', 'past_due', 'unpaid', 'paused', 'incomplete'].includes(sub.status)
      );

      if (activeOrPendingSubscription) {
        // Create portal session for any existing subscription
        const portalSession = await stripe.billingPortal.sessions.create({
          customer: stripeCustomerId,
          return_url: `${req.headers.get('origin')}/account`,
        });

        return NextResponse.json({ 
          type: 'portal',
          url: portalSession.url 
        });
      }

      // If we get here, the customer exists but has no active subscriptions
    } else {
      // Create new customer
      const newCustomer = await stripe.customers.create({
        email: user.email,
        metadata: {
          userId: user.id,
        },
      });
      stripeCustomerId = newCustomer.id;
    }

    // Double-check for any subscriptions one last time before creating checkout
    // This helps prevent race conditions
    const finalCheck = await stripe.subscriptions.list({
      customer: stripeCustomerId,
      limit: 1,
    });

    if (finalCheck.data.length > 0) {
      const portalSession = await stripe.billingPortal.sessions.create({
        customer: stripeCustomerId,
        return_url: `${req.headers.get('origin')}/account`,
      });

      return NextResponse.json({ 
        type: 'portal',
        url: portalSession.url 
      });
    }

    // Create a checkout session with trial period
    const checkoutSession = await stripe.checkout.sessions.create({
      mode: 'subscription',
      payment_method_types: ['card'],
      customer: stripeCustomerId,
      line_items: [
        {
          price: STRIPE_PRICE_ID,
          quantity: 1,
        },
      ],
      subscription_data: {
        trial_period_days: 7,
        metadata: {
          userId: user.id,
        },
      },
      success_url: `${req.headers.get('origin')}/?session_id={CHECKOUT_SESSION_ID}`,
      cancel_url: `${req.headers.get('origin')}/pricing`,
      metadata: {
        userId: user.id,
      },
    });

    return NextResponse.json({ 
      type: 'checkout',
      sessionId: checkoutSession.id 
    });
  } catch (error) {
    console.error('Error creating checkout session:', error);
    return NextResponse.json(
      { error: 'Failed to create checkout session' },
      { status: 500 }
    );
  }
} 