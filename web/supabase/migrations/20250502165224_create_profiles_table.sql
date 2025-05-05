-- Create the profiles table
CREATE TABLE public.profiles (
  user_id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
  display_name TEXT,
  avatar_url TEXT,
  monthly_token_quota INTEGER, -- Max tokens allowed per month (nullable, depends on plan)
  token_usage_this_month INTEGER DEFAULT 0 NOT NULL, -- Tokens used this billing cycle
  timezone TEXT NOT NULL DEFAULT 'UTC', -- User's IANA timezone
  created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
  updated_at TIMESTAMPTZ DEFAULT now() NOT NULL
);

-- Add comments to the table and columns
COMMENT ON TABLE public.profiles IS 'Stores public profile information for users.';
COMMENT ON COLUMN public.profiles.user_id IS 'References the user in auth.users.';
COMMENT ON COLUMN public.profiles.display_name IS 'Public display name chosen by the user.';
COMMENT ON COLUMN public.profiles.avatar_url IS 'URL of the user's avatar image.';
COMMENT ON COLUMN public.profiles.monthly_token_quota IS 'Maximum number of tokens the user can consume per month.';
COMMENT ON COLUMN public.profiles.token_usage_this_month IS 'Number of tokens consumed in the current billing period.';
COMMENT ON COLUMN public.profiles.timezone IS 'User's preferred IANA timezone string for display purposes.';

-- Enable Row Level Security (RLS)
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;

-- Create RLS policies
-- 1. Allow users to read their own profile
CREATE POLICY "Allow individual user read access" ON public.profiles
  FOR SELECT USING (auth.uid() = user_id);

-- 2. Allow users to update their own profile
CREATE POLICY "Allow individual user update access" ON public.profiles
  FOR UPDATE USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);

-- Note: INSERT is handled by the trigger function below, which runs with security definer privileges.
-- DELETE is implicitly disallowed for users by default RLS unless a specific policy grants it.

-- Function to handle automatic updated_at timestamp
CREATE OR REPLACE FUNCTION public.handle_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to automatically update updated_at on row modification
CREATE TRIGGER on_profiles_updated
  BEFORE UPDATE ON public.profiles
  FOR EACH ROW
  EXECUTE FUNCTION public.handle_updated_at();

-- Function to automatically create a profile when a new user signs up
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO public.profiles (user_id)
  VALUES (NEW.id);
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER; -- SECURITY DEFINER allows this function to bypass RLS

-- Trigger to call handle_new_user after a new user is created in auth.users
CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW
  EXECUTE FUNCTION public.handle_new_user();
