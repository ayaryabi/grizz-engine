-- No extension needed if pgcrypto loaded elsewhere

-- Create ENUM type for link_type
CREATE TYPE public.byte_link_type AS ENUM ('panel_reference','inline_reference','ai_suggested');

-- Create the byte_links table
CREATE TABLE public.byte_links (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(), -- Use pgcrypto
    source_byte_id UUID REFERENCES public.bytes(id) ON DELETE CASCADE NOT NULL,
    target_byte_id UUID REFERENCES public.bytes(id) ON DELETE CASCADE NOT NULL,
    user_id UUID NOT NULL, -- Set by trigger (assuming same pattern as byte_entity_links)
    link_type public.byte_link_type NOT NULL, -- Use ENUM type
    position INTEGER, -- For ordered references, like panels
    properties JSONB, -- For extra metadata if needed
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT now() NOT NULL -- In case link properties are updated
);

-- Add uniqueness constraint (prevent identical links of same type)
CREATE UNIQUE INDEX uniq_byte_link ON public.byte_links (source_byte_id, target_byte_id, link_type);
COMMENT ON INDEX public.uniq_byte_link IS 'Ensures a specific link type only exists once between two bytes.';

-- Add comments
COMMENT ON TABLE public.byte_links IS 'Links bytes to other bytes (e.g., for references, panels).';
COMMENT ON COLUMN public.byte_links.id IS 'Unique identifier for the link.';
COMMENT ON COLUMN public.byte_links.source_byte_id IS 'Foreign key referencing the source byte.';
COMMENT ON COLUMN public.byte_links.target_byte_id IS 'Foreign key referencing the target byte.';
COMMENT ON COLUMN public.byte_links.user_id IS 'Owner user ID, copied from the source byte via trigger.'; -- Needs trigger!
COMMENT ON COLUMN public.byte_links.link_type IS 'Type of link (panel, inline, ai).'; -- Updated
COMMENT ON COLUMN public.byte_links.position IS 'Order for links, relevant for types like panel_reference.';
COMMENT ON COLUMN public.byte_links.properties IS 'Optional JSONB field for additional link context.';
COMMENT ON COLUMN public.byte_links.created_at IS 'Timestamp of when the link was created.';
COMMENT ON COLUMN public.byte_links.updated_at IS 'Timestamp of when the link was last updated.';

-- Add indexes
CREATE INDEX idx_byte_links_source_byte_id ON public.byte_links(source_byte_id);
CREATE INDEX idx_byte_links_target_byte_id ON public.byte_links(target_byte_id);
-- CREATE INDEX idx_byte_links_user_id ON public.byte_links(user_id); -- Removed

-- Trigger function to auto-set user_id from the SOURCE byte
-- IMPORTANT: Need to add this trigger logic similar to byte_entity_links
CREATE OR REPLACE FUNCTION public.set_byte_link_user()
RETURNS TRIGGER AS $$
BEGIN
  -- Copy the user_id from the referenced SOURCE byte.
  NEW.user_id := (SELECT user_id FROM public.bytes WHERE id = NEW.source_byte_id);
  IF NEW.user_id IS NULL THEN
     RAISE EXCEPTION 'Source Byte % not found or has NULL user_id', NEW.source_byte_id;
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Trigger to call the function before insert
CREATE TRIGGER trigger_set_byte_link_user
BEFORE INSERT ON public.byte_links
FOR EACH ROW
EXECUTE FUNCTION public.set_byte_link_user();

-- Trigger for updated_at (uses global function)
CREATE TRIGGER on_byte_link_update
BEFORE UPDATE ON public.byte_links
FOR EACH ROW
EXECUTE FUNCTION public.handle_updated_at(); -- Use global function

-- Enable Row Level Security (RLS)
ALTER TABLE public.byte_links ENABLE ROW LEVEL SECURITY;

-- Policy: Users can manage links owned by them (derived from source byte ownership)
CREATE POLICY "Users can manage their own byte links" ON public.byte_links
FOR ALL
USING (auth.uid() = user_id) -- Check against trigger-set user_id
WITH CHECK (auth.uid() = user_id);

-- Constraint to prevent linking a byte to itself (optional, but good practice)
ALTER TABLE public.byte_links ADD CONSTRAINT check_source_target_different CHECK (source_byte_id <> target_byte_id);
