import { NextResponse } from 'next/server';
import { getStripeServer, STRIPE_PRICE_ID } from '@/lib/stripe/config';
import { createClient } from '@supabase/supabase-js';

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

    let stripeCustomerId: string;

    if (allCustomers.data.length > 0) {
      // Sort by creation date ascending (oldest first) and use the first one
      const oldestCustomer = allCustomers.data.sort((a, b) => a.created - b.created)[0];
      stripeCustomerId = oldestCustomer.id;

      // If there are duplicates, let's clean them up
      if (allCustomers.data.length > 1) {
        console.log(`Found ${allCustomers.data.length} duplicate customers for ${user.email}, cleaning up...`);
        // Delete all but the oldest customer
        for (const customer of allCustomers.data.slice(1)) {
          try {
            await stripe.customers.del(customer.id);
            console.log(`Deleted duplicate customer: ${customer.id}`);
          } catch (err) {
            console.error(`Failed to delete duplicate customer ${customer.id}:`, err);
          }
        }
      }
    } else {
      // Create new customer with idempotency key to prevent duplicates
      const newCustomer = await stripe.customers.create({
        email: user.email,
        metadata: {
          userId: user.id,
        }
      }, {
        idempotencyKey: `customer_${user.id}_${user.email}` // This prevents duplicate customer creation
      });
      stripeCustomerId = newCustomer.id;
    }

    // Check for any active subscriptions
    const subscriptions = await stripe.subscriptions.list({
      customer: stripeCustomerId,
      status: 'all',
      limit: 100,
    });

    // If there's any active subscription, redirect to portal
    const activeSubscription = subscriptions.data.find(sub => 
      ['active', 'trialing', 'past_due', 'unpaid', 'paused', 'incomplete'].includes(sub.status)
    );

    if (activeSubscription) {
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
              success_url: `${req.headers.get('origin')}/chat?session_id={CHECKOUT_SESSION_ID}`,
      cancel_url: `${req.headers.get('origin')}/pricing`,
      client_reference_id: user.id, // Add this to ensure we have user ID in webhooks
      metadata: {
        userId: user.id,
      },
    }, {
      idempotencyKey: `checkout_${user.id}_${Date.now()}` // Prevent duplicate checkouts
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