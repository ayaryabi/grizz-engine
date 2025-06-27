'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { getStripe } from '@/lib/stripe/config';
import { useAuth } from '@/features/auth/AuthContext';

export default function CheckoutPage() {
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();
  const { user, session } = useAuth();

  useEffect(() => {
    const createCheckoutSession = async () => {
      try {
        if (!session?.access_token) {
          throw new Error('No session found');
        }

        // Create checkout session
        const response = await fetch('/api/stripe/create-checkout-session', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${session.access_token}`,
          },
        });

        if (!response.ok) {
          throw new Error('Failed to create checkout session');
        }

        const data = await response.json();
        
        // Check response type
        if (data.type === 'portal') {
          // Redirect to Stripe Customer Portal
          window.location.href = data.url;
          return;
        }
        
        // Otherwise, redirect to Stripe Checkout
        const stripe = await getStripe();
        if (!stripe) throw new Error('Failed to load Stripe');
        
        const { error } = await stripe.redirectToCheckout({ sessionId: data.sessionId });
        if (error) throw error;

      } catch (err) {
        console.error('Checkout error:', err);
        setError(err instanceof Error ? err.message : 'Something went wrong');
        setIsLoading(false);
      }
    };

    if (user && session) {
      createCheckoutSession();
    } else {
      // If no user, redirect to signup
      router.push('/signup');
    }
  }, [user, session, router]);

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center p-4">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-red-600 mb-4">Oops!</h1>
          <p className="text-gray-600 mb-4">{error}</p>
          <button
            className="text-blue-600 hover:underline"
            onClick={() => router.push('/')}
          >
            Return to Homepage
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <div className="text-center">
        <h1 className="text-2xl font-bold mb-4">Setting Up Your Trial</h1>
        <p className="text-gray-600">Please wait while we redirect you...</p>
      </div>
    </div>
  );
} 