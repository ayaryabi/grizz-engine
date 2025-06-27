'use client';

import React, { createContext, useContext, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useAuth } from '@/features/auth/AuthContext';
import { supabase } from '@/lib/supabase/supabase';
import { Subscription, SubscriptionContextType, SubscriptionProviderProps } from './types';

// Create the context
const SubscriptionContext = createContext<SubscriptionContextType | undefined>(undefined);

// Fetch subscription data from Supabase
async function fetchSubscription(userId: string): Promise<Subscription | null> {
  const { data, error } = await supabase
    .from('subscriptions')
    .select('*')
    .eq('user_id', userId)
    .single();

  if (error) {
    if (error.code === 'PGRST116') {
      // No subscription found - this is normal for new users
      return null;
    }
    throw error;
  }

  return data as Subscription;
}

// Open customer portal
async function openCustomerPortal(): Promise<void> {
  // Get the current session token
  const { data: { session } } = await supabase.auth.getSession();
  
  if (!session?.access_token) {
    throw new Error('Not authenticated');
  }

  const response = await fetch('/api/stripe/customer-portal', {
    method: 'POST',
    headers: { 
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${session.access_token}`,
    },
  });

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.error || 'Failed to open customer portal');
  }

  const { url } = await response.json();
  window.location.href = url;
}

// Provider component
export function SubscriptionProvider({ children }: SubscriptionProviderProps) {
  const { user, loading: authLoading } = useAuth();

  // Only fetch subscription if user is authenticated
  const {
    data: subscription,
    isLoading: subscriptionLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: ['subscription', user?.id],
    queryFn: () => fetchSubscription(user!.id),
    enabled: !!user?.id, // Only run query when user exists
    staleTime: 5 * 60 * 1000, // 5 minutes
    refetchOnWindowFocus: true,
    refetchOnMount: true,
  });

  // Calculate derived state
  const isActive = useMemo(() => {
    if (!subscription) return false;
    return ['active', 'trialing'].includes(subscription.status);
  }, [subscription]);

  const status = subscription?.status || null;
  const loading = authLoading || subscriptionLoading;

  // Portal function with error handling
  const openPortal = async () => {
    try {
      await openCustomerPortal();
    } catch (err) {
      console.error('Failed to open customer portal:', err);
      // You could add toast notification here
    }
  };

  // Refetch function
  const handleRefetch = async () => {
    await refetch();
  };

  const contextValue: SubscriptionContextType = {
    subscription: subscription || null,
    isActive,
    status,
    loading,
    error: error as Error | null,
    openPortal,
    refetch: handleRefetch,
  };

  return (
    <SubscriptionContext.Provider value={contextValue}>
      {children}
    </SubscriptionContext.Provider>
  );
}

// Hook to use subscription context
export function useSubscription(): SubscriptionContextType {
  const context = useContext(SubscriptionContext);
  if (context === undefined) {
    throw new Error('useSubscription must be used within a SubscriptionProvider');
  }
  return context;
} 