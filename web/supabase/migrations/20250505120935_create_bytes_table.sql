-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS vector WITH SCHEMA extensions;
CREATE EXTENSION IF NOT EXISTS pgcrypto; -- Needed for gen_random_uuid()

-- Create ENUM types needed for bytes table
CREATE TYPE public.visibility_status AS ENUM ('private', 'shared', 'public');
CREATE TYPE public.moderation_status AS ENUM ('pending', 'approved', 'rejected', 'flagged');

-- Create the bytes table
CREATE TABLE public.bytes (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  item_type TEXT NOT NULL DEFAULT 'note', -- e.g., 'note', 'document', 'recipe', 'paystub', 'image', 'video', 'audio'
  title TEXT,
  content JSONB, -- TipTap JSON or potentially plain MD
  properties JSONB DEFAULT '{}'::jsonb, -- Other metadata (dimensions, duration, etc.)
  embedding extensions.vector(1536), -- pgvector embedding (size from mvp_v0.1.md)
  file_url TEXT, -- Direct URL to the file in storage (hot path)
  mime_type TEXT, -- Mime type of the stored file (hot path)
  is_deleted BOOLEAN DEFAULT false NOT NULL, -- For soft deletes
  visibility public.visibility_status DEFAULT 'private' NOT NULL, -- visibility ENUM
  moderation_status public.moderation_status DEFAULT 'pending' NOT NULL, -- moderation ENUM
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Add constraint to enforce file_url and mime_type for binary types
ALTER TABLE public.bytes
ADD CONSTRAINT file_url_mime_type_required_for_binary_types
CHECK (
  -- If item_type IS a file type, then file_url AND mime_type MUST be NOT NULL
  (item_type IN ('image', 'video', 'document', 'audio', 'paystub') AND file_url IS NOT NULL AND mime_type IS NOT NULL)
  OR
  -- Otherwise (if item_type is NOT a file type), this constraint doesn't apply
  (item_type NOT IN ('image', 'video', 'document', 'audio', 'paystub'))
);

-- Add comments
COMMENT ON TABLE public.bytes IS 'Core table for storing knowledge items (notes, docs, files, etc.).';
COMMENT ON COLUMN public.bytes.item_type IS 'Type of the knowledge item.';
COMMENT ON COLUMN public.bytes.content IS 'Main content, likely TipTap JSON or Markdown.';
COMMENT ON COLUMN public.bytes.properties IS 'Structured metadata specific to the item_type.';
COMMENT ON COLUMN public.bytes.embedding IS 'Vector embedding for semantic search.';
COMMENT ON COLUMN public.bytes.file_url IS 'Direct URL to the associated file in object storage.';
COMMENT ON COLUMN public.bytes.mime_type IS 'MIME type of the associated file.';
COMMENT ON COLUMN public.bytes.is_deleted IS 'Flag for soft deletion.';
COMMENT ON COLUMN public.bytes.visibility IS 'Visibility status of the byte (private, shared, public).';
COMMENT ON COLUMN public.bytes.moderation_status IS 'Content moderation status.';

-- Add pgvector index using ivfflat and cosine distance
CREATE INDEX bytes_embedding_cos_idx ON public.bytes USING ivfflat (embedding extensions.vector_cosine_ops) WITH (lists = 100);
COMMENT ON INDEX public.bytes_embedding_cos_idx IS 'IVFFlat index on the embedding column for cosine similarity search.';

-- Add trigger for updated_at (reuse function from profiles migration)
CREATE TRIGGER on_bytes_updated
  BEFORE UPDATE ON public.bytes
  FOR EACH ROW
  EXECUTE FUNCTION public.handle_updated_at(); 

-- Enable RLS
ALTER TABLE public.bytes ENABLE ROW LEVEL SECURITY;

-- Create Policy with WITH CHECK
CREATE POLICY "Allow individual user CRUD access on bytes" ON public.bytes
  FOR ALL 
  USING (auth.uid() = user_id) -- Checks ownership for SELECT, UPDATE, DELETE
  WITH CHECK (auth.uid() = user_id); -- Enforces ownership for INSERT, UPDATE
