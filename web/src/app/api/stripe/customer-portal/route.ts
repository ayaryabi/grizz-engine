import { NextResponse } from 'next/server';
import { getStripeServer } from '@/lib/stripe/config';
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

    // Get customer ID from our database first (fast!)
    const { data: subscription } = await supabase
      .from('subscriptions')
      .select('stripe_customer_id')
      .eq('user_id', user.id)
      .single();

    let stripeCustomerId: string;

    if (subscription?.stripe_customer_id) {
      // Use cached customer ID (fast path)
      stripeCustomerId = subscription.stripe_customer_id;
    } else {
      // Fallback: Look up customer in Stripe (slow, but only happens once)
      const customers = await stripe.customers.list({
        email: user.email,
        limit: 10,
      });

      if (customers.data.length === 0) {
        // Create a new customer if none exists (edge case)
        const newCustomer = await stripe.customers.create({
          email: user.email,
          metadata: {
            userId: user.id,
          }
        });
        stripeCustomerId = newCustomer.id;
      } else {
        stripeCustomerId = customers.data[0].id;
      }
    }

    // Create a portal session
    const session = await stripe.billingPortal.sessions.create({
      customer: stripeCustomerId,
      return_url: `${req.headers.get('origin')}/chat`,
    });

    return NextResponse.json({ url: session.url });
  } catch (error) {
    console.error('Error creating portal session:', error);
    return NextResponse.json(
      { error: 'Failed to create portal session' },
      { status: 500 }
    );
  }
} 