-- No extension needed here if pgcrypto loaded elsewhere

-- Create the byte_entity_links table (join table)
CREATE TABLE public.byte_entity_links (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(), -- Added surrogate PK
    byte_id UUID REFERENCES public.bytes(id) ON DELETE CASCADE NOT NULL,
    entity_id UUID REFERENCES public.entities(id) ON DELETE CASCADE NOT NULL,
    user_id UUID NOT NULL, -- Removed FK to auth.users, will be set by trigger
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    -- PRIMARY KEY (byte_id, entity_id) -- Replaced by surrogate key
    UNIQUE (byte_id, entity_id) -- Ensure pair uniqueness
);

-- Add comments
COMMENT ON TABLE public.byte_entity_links IS 'Links bytes to the entities mentioned or related to them.';
COMMENT ON COLUMN public.byte_entity_links.id IS 'Unique identifier for the link itself.'; -- New comment
COMMENT ON COLUMN public.byte_entity_links.byte_id IS 'Foreign key referencing the byte.';
COMMENT ON COLUMN public.byte_entity_links.entity_id IS 'Foreign key referencing the entity.';
COMMENT ON COLUMN public.byte_entity_links.user_id IS 'Owner user ID, copied from the associated byte via trigger.'; -- Updated comment
COMMENT ON COLUMN public.byte_entity_links.created_at IS 'Timestamp of when the link was created.';

-- Trigger function to auto-set user_id from the byte
CREATE OR REPLACE FUNCTION public.set_byte_entity_link_user()
RETURNS TRIGGER AS $$
BEGIN
  -- Assume the user creating the link owns the byte.
  -- Copy the user_id from the referenced byte.
  NEW.user_id := (SELECT user_id FROM public.bytes WHERE id = NEW.byte_id);
  -- If byte doesn't exist or user_id is somehow null, this might fail or set null.
  -- Consider adding error handling if needed, though FK constraint should prevent orphan byte_id.
  IF NEW.user_id IS NULL THEN
     RAISE EXCEPTION 'Byte % not found or has NULL user_id', NEW.byte_id;
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Trigger to call the function before insert
CREATE TRIGGER trigger_set_byte_entity_link_user
BEFORE INSERT ON public.byte_entity_links
FOR EACH ROW
EXECUTE FUNCTION public.set_byte_entity_link_user();


-- Add indexes for faster lookups
CREATE INDEX idx_bel_byte_id ON public.byte_entity_links(byte_id); -- Renamed
CREATE INDEX idx_bel_entity_id ON public.byte_entity_links(entity_id); -- Renamed
-- CREATE INDEX idx_byte_entity_links_user_id ON public.byte_entity_links(user_id); -- Removed as less critical


-- Enable Row Level Security (RLS)
ALTER TABLE public.byte_entity_links ENABLE ROW LEVEL SECURITY;

-- Policy: Users can manage links owned by them (derived from byte ownership)
CREATE POLICY "Users can manage their own byte-entity links" ON public.byte_entity_links
FOR ALL
USING (auth.uid() = user_id) -- Check against the trigger-set user_id
WITH CHECK (auth.uid() = user_id); -- Enforce on insert/update (redundant with trigger? safer)

-- Removed the commented out alternative policies 