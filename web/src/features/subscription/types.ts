export interface Subscription {
  id: string;
  user_id: string;
  stripe_customer_id: string;
  stripe_subscription_id: string;
  status: 'active' | 'trialing' | 'canceled' | 'past_due' | 'unpaid' | 'incomplete' | 'incomplete_expired' | 'paused';
  current_period_start: string;
  current_period_end: string;
  trial_start?: string | null;
  trial_end?: string | null;
  created_at: string;
  updated_at: string;
}

export interface SubscriptionContextType {
  subscription: Subscription | null;
  isActive: boolean;  // true if status is 'active' or 'trialing'
  status: Subscription['status'] | null;
  loading: boolean;
  error: Error | null;
  openPortal: () => Promise<void>;
  refetch: () => Promise<void>;
}

export interface SubscriptionProviderProps {
  children: React.ReactNode;
} 