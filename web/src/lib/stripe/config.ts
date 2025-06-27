import { Stripe as StripeClient, loadStripe } from '@stripe/stripe-js';

// Client-side Stripe instance (safe to use in browser)
let stripePromise: Promise<StripeClient | null>;
export const getStripe = () => {
  if (!stripePromise) {
    stripePromise = loadStripe(process.env.NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY!);
  }
  return stripePromise;
};

// Constants (safe to use in browser)
export const STRIPE_PRICE_ID = process.env.STRIPE_PRICE_ID!;

// Server-side only imports and config
// This code will be eliminated from client bundles
import Stripe from 'stripe';

let stripeServerInstance: Stripe | null = null;

export const getStripeServer = () => {
  if (!stripeServerInstance && process.env.STRIPE_SECRET_KEY) {
    stripeServerInstance = new Stripe(process.env.STRIPE_SECRET_KEY, {
      apiVersion: '2025-05-28.basil',
      typescript: true,
    });
  }
  return stripeServerInstance;
};

// Constants
export const STRIPE_WEBHOOK_SECRET = process.env.STRIPE_WEBHOOK_SECRET!; 