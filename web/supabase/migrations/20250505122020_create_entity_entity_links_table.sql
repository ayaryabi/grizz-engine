-- No extension needed if pgcrypto loaded elsewhere

-- Define the canonical edge vocabulary type (based on mvp_v0.1.md)
CREATE TYPE public.entity_relationship_type AS ENUM (
    'WORKS_AT', 'WORKS_ON', 'FOUNDED_BY', 'OWNED_BY',
    'LOCATED_IN', 'PART_OF', 'EVENT_OF', 'ATTENDED',
    'ABOUT', 'RELATED_TO', 'NEXT_STEP', 'USES_TOOL'
);

-- Create the entity_entity_links table
CREATE TABLE public.entity_entity_links (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(), -- Use pgcrypto
    source_entity_id UUID REFERENCES public.entities(id) ON DELETE CASCADE NOT NULL,
    target_entity_id UUID REFERENCES public.entities(id) ON DELETE CASCADE NOT NULL,
    user_id UUID NOT NULL, -- Set by trigger (assuming ownership follows source entity)
    relationship_type public.entity_relationship_type NOT NULL DEFAULT 'RELATED_TO',
    properties JSONB, -- For relationship details (role, since, confidence, etc.)
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT now() NOT NULL
);

-- Add uniqueness constraint
CREATE UNIQUE INDEX uniq_entity_edge ON public.entity_entity_links (source_entity_id, target_entity_id, relationship_type);
COMMENT ON INDEX public.uniq_entity_edge IS 'Ensures a specific relationship type only exists once between two entities.';

-- Add comments
COMMENT ON TABLE public.entity_entity_links IS 'Stores relationships (edges) between entities.';
COMMENT ON COLUMN public.entity_entity_links.id IS 'Unique identifier for the relationship link.';
COMMENT ON COLUMN public.entity_entity_links.source_entity_id IS 'Foreign key referencing the source entity of the relationship.';
COMMENT ON COLUMN public.entity_entity_links.target_entity_id IS 'Foreign key referencing the target entity of the relationship.';
COMMENT ON COLUMN public.entity_entity_links.user_id IS 'Owner user ID, copied from the source entity via trigger.'; -- Needs trigger!
COMMENT ON COLUMN public.entity_entity_links.relationship_type IS 'The type of relationship between the entities (e.g., WORKS_AT).';
COMMENT ON COLUMN public.entity_entity_links.properties IS 'Optional JSONB field for additional relationship context.';
COMMENT ON COLUMN public.entity_entity_links.created_at IS 'Timestamp of when the link was created.';
COMMENT ON COLUMN public.entity_entity_links.updated_at IS 'Timestamp of when the link was last updated.';

-- Add indexes
CREATE INDEX idx_entity_links_source_id ON public.entity_entity_links(source_entity_id);
CREATE INDEX idx_entity_links_target_id ON public.entity_entity_links(target_entity_id);
CREATE INDEX idx_entity_links_user_id ON public.entity_entity_links(user_id);
CREATE INDEX idx_entity_links_rel_type ON public.entity_entity_links(relationship_type);

-- Trigger function to auto-set user_id from the SOURCE entity
-- IMPORTANT: Need to add this trigger logic similar to other link tables
CREATE OR REPLACE FUNCTION public.set_entity_link_user()
RETURNS TRIGGER AS $$
BEGIN
  -- Copy the user_id from the referenced SOURCE entity.
  NEW.user_id := (SELECT user_id FROM public.entities WHERE id = NEW.source_entity_id);
  IF NEW.user_id IS NULL THEN
     RAISE EXCEPTION 'Source Entity % not found or has NULL user_id', NEW.source_entity_id;
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Trigger to call the function before insert
CREATE TRIGGER trigger_set_entity_link_user
BEFORE INSERT ON public.entity_entity_links
FOR EACH ROW
EXECUTE FUNCTION public.set_entity_link_user();

-- Trigger for updated_at (uses global function)
CREATE TRIGGER on_entity_link_update
BEFORE UPDATE ON public.entity_entity_links
FOR EACH ROW
EXECUTE FUNCTION public.handle_updated_at(); -- Use global function

-- Enable Row Level Security (RLS)
ALTER TABLE public.entity_entity_links ENABLE ROW LEVEL SECURITY;

-- Policy: Users can manage links owned by them (derived from source entity ownership)
CREATE POLICY "Users can manage their own entity links" ON public.entity_entity_links
FOR ALL
USING (auth.uid() = user_id) -- Check against trigger-set user_id
WITH CHECK (auth.uid() = user_id);

-- Constraint to prevent linking an entity to itself (optional, but good practice)
ALTER TABLE public.entity_entity_links ADD CONSTRAINT check_entity_source_target_different CHECK (source_entity_id <> target_entity_id);
