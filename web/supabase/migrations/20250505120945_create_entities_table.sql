-- Enable the required extension
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Create the entities table
CREATE TABLE public.entities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    entity_type TEXT NOT NULL CHECK (entity_type IN ('person', 'place', 'organization', 'concept', 'other')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Add comments to the table and columns
COMMENT ON TABLE public.entities IS 'Stores structured entities extracted or defined by users.';
COMMENT ON COLUMN public.entities.id IS 'Unique identifier for the entity.';
COMMENT ON COLUMN public.entities.user_id IS 'Foreign key linking to the user who owns this entity.';
COMMENT ON COLUMN public.entities.name IS 'The name of the entity.';
COMMENT ON COLUMN public.entities.description IS 'A brief description of the entity.';
COMMENT ON COLUMN public.entities.entity_type IS 'Categorization of the entity type.';
COMMENT ON COLUMN public.entities.created_at IS 'Timestamp of when the entity was created.';
COMMENT ON COLUMN public.entities.updated_at IS 'Timestamp of when the entity was last updated.';

-- Add index on user_id for faster lookups
CREATE INDEX idx_entities_user_id ON public.entities(user_id);

-- Add unique index for user, name (case-insensitive), and type
CREATE UNIQUE INDEX ent_unique_per_user
  ON public.entities (user_id, lower(name), entity_type);
COMMENT ON INDEX public.ent_unique_per_user IS 'Ensures entity names are unique per user and type (case-insensitive).';

-- Trigger for updated_at (now uses the global function)
CREATE TRIGGER on_entities_updated
BEFORE UPDATE ON public.entities
FOR EACH ROW
EXECUTE FUNCTION public.handle_updated_at();

-- Enable Row Level Security (RLS)
ALTER TABLE public.entities ENABLE ROW LEVEL SECURITY;

-- Policy: Users can manage their own entities
CREATE POLICY "Users can manage their own entities" ON public.entities
FOR ALL
USING (auth.uid() = user_id)
WITH CHECK (auth.uid() = user_id); 