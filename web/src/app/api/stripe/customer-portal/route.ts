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

    // Get customer ID from Stripe - look for all customers
    const customers = await stripe.customers.list({
      email: user.email,
      limit: 100, // Increased to catch all duplicates
    });

    if (customers.data.length === 0) {
      return NextResponse.json(
        { error: 'No Stripe customer found' },
        { status: 404 }
      );
    }

    // If multiple customers found, use the oldest one
    const oldestCustomer = customers.data.sort((a, b) => a.created - b.created)[0];

    // Create a portal session
    const session = await stripe.billingPortal.sessions.create({
      customer: oldestCustomer.id,
      return_url: `${req.headers.get('origin')}/account`,
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