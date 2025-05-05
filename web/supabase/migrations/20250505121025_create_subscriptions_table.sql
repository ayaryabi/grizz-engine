-- No extension needed if pgcrypto loaded elsewhere

-- Create subscription plan type
CREATE TYPE public.subscription_plan AS ENUM ('free', 'pro', 'enterprise');

-- Create subscription status type
CREATE TYPE public.subscription_status AS ENUM ('active', 'inactive', 'trialing', 'past_due', 'canceled');

-- Create the subscriptions table
CREATE TABLE public.subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(), -- Use pgcrypto
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL UNIQUE, -- Keep UNIQUE for v0.1
    plan public.subscription_plan NOT NULL DEFAULT 'free',
    status public.subscription_status NOT NULL DEFAULT 'active',
    stripe_customer_id TEXT, -- Removed UNIQUE constraint here
    stripe_subscription_id TEXT, -- Removed UNIQUE constraint here
    current_period_start TIMESTAMPTZ,
    current_period_end TIMESTAMPTZ,
    trial_start TIMESTAMPTZ,
    trial_end TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT now() NOT NULL
);

-- Add comments
COMMENT ON TABLE public.subscriptions IS 'Stores user subscription status and details.';
COMMENT ON COLUMN public.subscriptions.id IS 'Unique identifier for the subscription record.';
COMMENT ON COLUMN public.subscriptions.user_id IS 'Foreign key linking to the user. UNIQUE constraint ensures one record per user.';
COMMENT ON COLUMN public.subscriptions.plan IS 'The subscription plan the user is on.';
COMMENT ON COLUMN public.subscriptions.status IS 'The current status of the subscription.';
COMMENT ON COLUMN public.subscriptions.stripe_customer_id IS 'Associated Stripe Customer ID, if applicable.';
COMMENT ON COLUMN public.subscriptions.stripe_subscription_id IS 'Associated Stripe Subscription ID, if applicable.';
COMMENT ON COLUMN public.subscriptions.current_period_start IS 'Start date of the current billing period.';
COMMENT ON COLUMN public.subscriptions.current_period_end IS 'End date of the current billing period.';
COMMENT ON COLUMN public.subscriptions.trial_start IS 'Start date of the free trial, if applicable.';
COMMENT ON COLUMN public.subscriptions.trial_end IS 'End date of the free trial, if applicable.';
COMMENT ON COLUMN public.subscriptions.created_at IS 'Timestamp of when the subscription record was created.';
COMMENT ON COLUMN public.subscriptions.updated_at IS 'Timestamp of when the subscription record was last updated.';

-- Add index on user_id (already unique, but good for lookups)
CREATE INDEX idx_subscriptions_user_id ON public.subscriptions(user_id);

-- Add partial unique indexes for Stripe IDs (ignore NULLs)
CREATE UNIQUE INDEX idx_unique_stripe_customer_id ON public.subscriptions(stripe_customer_id)
  WHERE stripe_customer_id IS NOT NULL;
CREATE UNIQUE INDEX idx_unique_stripe_subscription_id ON public.subscriptions(stripe_subscription_id)
  WHERE stripe_subscription_id IS NOT NULL;
COMMENT ON INDEX public.idx_unique_stripe_customer_id IS 'Ensures stripe_customer_id is unique among non-null values.';
COMMENT ON INDEX public.idx_unique_stripe_subscription_id IS 'Ensures stripe_subscription_id is unique among non-null values.';

-- Remove old simple indexes for Stripe IDs
-- CREATE INDEX idx_subscriptions_stripe_customer_id ON public.subscriptions(stripe_customer_id);
-- CREATE INDEX idx_subscriptions_stripe_subscription_id ON public.subscriptions(stripe_subscription_id);

-- Remove specific update function
-- CREATE OR REPLACE FUNCTION public.handle_subscription_update()
-- RETURNS TRIGGER AS $$
-- BEGIN
--   NEW.updated_at = CURRENT_TIMESTAMP;
--   RETURN NEW;
-- END;
-- $$ LANGUAGE plpgsql SECURITY DEFINER;

-- Trigger for updated_at (uses global function)
CREATE TRIGGER on_subscription_update
BEFORE UPDATE ON public.subscriptions
FOR EACH ROW
EXECUTE FUNCTION public.handle_updated_at(); -- Use global function

-- Enable Row Level Security (RLS)
ALTER TABLE public.subscriptions ENABLE ROW LEVEL SECURITY;

-- Policy: Users can view their own subscription details
CREATE POLICY "Users can view own subscription" ON public.subscriptions
FOR SELECT
USING (auth.uid() = user_id);

-- Policy: Allow service_role (for webhook updates) to bypass RLS
CREATE POLICY "Allow service_role to manage subscriptions" ON public.subscriptions
  FOR ALL
  USING (true) -- Allows access based on role, not user_id match
  WITH CHECK (true);

-- Note: Need to restrict this policy to ONLY the service_role if possible
-- Using Supabase roles, this policy might need refinement, but allows backend full access.
-- Consider separate INSERT/UPDATE policies if more granularity needed.

-- Policy: Prevent users from modifying their own subscription directly
-- Updates should happen via backend processes (e.g., Stripe webhooks) using service role key.
-- We will handle inserts via a trigger modification in a later migration. 