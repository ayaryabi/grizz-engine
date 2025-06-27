-- Update the handle_new_user function to set display_name from user metadata
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO public.profiles (user_id, display_name)
  VALUES (NEW.id, (NEW.raw_user_meta_data->>'first_name'));
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER; 