// Example usage of the subscription context
'use client';

import { useSubscription } from './useSubscription';

export function ExampleSubscriptionComponent() {
  const { 
    subscription, 
    isActive, 
    status, 
    loading, 
    error, 
    openPortal 
  } = useSubscription();

  if (loading) {
    return <div>Loading subscription...</div>;
  }

  if (error) {
    return <div>Error loading subscription: {error.message}</div>;
  }

  if (!subscription) {
    return (
      <div>
        <p>No subscription found</p>
        <button onClick={openPortal}>
          Subscribe Now
        </button>
      </div>
    );
  }

  return (
    <div>
      <h2>Subscription Status</h2>
      <p>Status: {status}</p>
      <p>Active: {isActive ? 'Yes' : 'No'}</p>
      <p>Current Period: {subscription.current_period_start} to {subscription.current_period_end}</p>
      
      {!isActive && (
        <div>
          <p>⚠️ Your subscription is not active</p>
          <button onClick={openPortal}>
            Manage Subscription
          </button>
        </div>
      )}
      
      {isActive && (
        <button onClick={openPortal}>
          Manage Subscription
        </button>
      )}
    </div>
  );
} 