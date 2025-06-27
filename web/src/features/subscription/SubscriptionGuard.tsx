'use client';

import React from 'react';
import { useAuth } from '@/features/auth/AuthContext';
import { useSubscription } from './useSubscription';
import { SubscriptionOverlay } from './SubscriptionOverlay';

interface SubscriptionGuardProps {
  children: React.ReactNode;
}

export function SubscriptionGuard({ children }: SubscriptionGuardProps) {
  const { user } = useAuth();
  const { isActive, loading, openPortal } = useSubscription();

  // Show overlay if user is authenticated but doesn't have active subscription
  const shouldShowOverlay = user && !loading && !isActive;

  return (
    <>
      {children}
      {shouldShowOverlay && (
        <SubscriptionOverlay 
          onUpgrade={openPortal}
          loading={loading}
        />
      )}
    </>
  );
} 