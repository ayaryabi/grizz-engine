-- No extension needed if pgcrypto loaded elsewhere

-- Create the conversations table
CREATE TABLE public.conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(), -- Use pgcrypto
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    context_byte_id UUID NULL REFERENCES public.bytes(id) ON DELETE SET NULL, -- Optional link to a byte
    title TEXT, -- Optional title, could be auto-generated from first message
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT now() NOT NULL
);

-- Add comments
COMMENT ON TABLE public.conversations IS 'Chat threads. context_byte_id links a chat to a Byte if relevant.';
COMMENT ON COLUMN public.conversations.id IS 'Unique identifier for the conversation.';
COMMENT ON COLUMN public.conversations.user_id IS 'Foreign key linking to the user who owns this conversation.';
COMMENT ON COLUMN public.conversations.context_byte_id IS 'Optional foreign key linking the chat context to a specific byte.'; -- Added comment
COMMENT ON COLUMN public.conversations.title IS 'Optional user-defined or generated title for the conversation.';
COMMENT ON COLUMN public.conversations.created_at IS 'Timestamp of when the conversation was created.';
COMMENT ON COLUMN public.conversations.updated_at IS 'Timestamp of when the conversation was last updated (e.g., new message).';

-- Add index for user's recent conversations
CREATE INDEX convo_user_idx ON public.conversations(user_id, updated_at DESC);
COMMENT ON INDEX public.convo_user_idx IS 'Index to efficiently fetch conversations for a user, ordered by most recent.';

-- Remove old index
-- CREATE INDEX idx_conversations_user_id ON public.conversations(user_id);

-- Remove specific update function
-- CREATE OR REPLACE FUNCTION public.handle_conversation_update()
-- RETURNS TRIGGER AS $$
-- BEGIN
--   NEW.updated_at = CURRENT_TIMESTAMP;
--   RETURN NEW;
-- END;
-- $$ LANGUAGE plpgsql SECURITY DEFINER;

-- Trigger for updated_at (uses global function)
CREATE TRIGGER on_conversation_update -- Renamed trigger slightly for consistency
BEFORE UPDATE ON public.conversations
FOR EACH ROW
EXECUTE FUNCTION public.handle_updated_at(); -- Use global function

-- Enable Row Level Security (RLS)
ALTER TABLE public.conversations ENABLE ROW LEVEL SECURITY;

-- Policy: Users can manage their own conversations
CREATE POLICY "Users can manage their own conversations" ON public.conversations -- Kept original name
FOR ALL
USING (auth.uid() = user_id)
WITH CHECK (auth.uid() = user_id);

-- Old index definition removed:
-- CREATE INDEX idx_conversations_user_id ON public.conversations(user_id); 