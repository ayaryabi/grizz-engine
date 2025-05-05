-- No extension needed if pgcrypto loaded elsewhere

-- Create the messages table
CREATE TABLE public.messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(), -- Use pgcrypto
    conversation_id UUID NOT NULL REFERENCES public.conversations(id) ON DELETE CASCADE,
    user_id UUID NULL REFERENCES auth.users(id) ON DELETE SET NULL, -- User who sent the message (null for AI/system/tool)
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system', 'tool')), -- Added 'tool'
    content TEXT NOT NULL CHECK (length(content) > 0), -- Added non-empty check
    metadata JSONB, -- Optional metadata (e.g., referenced byte IDs, tool calls)
    created_at TIMESTAMPTZ DEFAULT now() NOT NULL
    -- No updated_at needed for messages typically
);

-- Add comments
COMMENT ON TABLE public.messages IS 'Chat messages (user & AI).'; -- Simplified comment
COMMENT ON COLUMN public.messages.id IS 'Unique identifier for the message.';
COMMENT ON COLUMN public.messages.conversation_id IS 'Foreign key linking to the conversation this message belongs to.';
COMMENT ON COLUMN public.messages.user_id IS 'Foreign key linking to the user who sent the message (null if system/AI/tool).'; -- Updated comment
COMMENT ON COLUMN public.messages.role IS 'Indicates whether the message is from the user, AI assistant, system, or a tool.'; -- Updated comment
COMMENT ON COLUMN public.messages.content IS 'The actual text content of the message.';
COMMENT ON COLUMN public.messages.metadata IS 'Optional JSONB field for additional message context.';
COMMENT ON COLUMN public.messages.created_at IS 'Timestamp of when the message was created.';

-- Add optimized index for fetching messages by conversation
CREATE INDEX msg_conv_ts_idx ON public.messages (conversation_id, created_at DESC);
COMMENT ON INDEX public.msg_conv_ts_idx IS 'Index to efficiently fetch messages for a conversation, ordered by time.';

-- Enable Row Level Security (RLS)
ALTER TABLE public.messages ENABLE ROW LEVEL SECURITY;

-- Policy: Users can manage messages in conversations they own
CREATE POLICY msg_owner ON public.messages
FOR ALL
USING (auth.uid() = (SELECT user_id FROM public.conversations WHERE id = conversation_id))
WITH CHECK (auth.uid() = (SELECT user_id FROM public.conversations WHERE id = conversation_id));

-- Policy: Allow service role (e.g., for assistant messages) or authenticated users (if functions insert)
-- to insert messages without the ownership check.
CREATE POLICY msg_service_insert ON public.messages
  FOR INSERT TO authenticated, service_role
  WITH CHECK (true);

-- Function to update conversation's updated_at (Keep this, it's correct)
CREATE OR REPLACE FUNCTION public.handle_new_message()
RETURNS TRIGGER AS $$
BEGIN
  UPDATE public.conversations
  SET updated_at = CURRENT_TIMESTAMP
  WHERE id = NEW.conversation_id;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Trigger to update conversation timestamp after a new message is inserted
CREATE TRIGGER touch_conv_after_msg -- Renamed trigger slightly
AFTER INSERT ON public.messages
FOR EACH ROW
EXECUTE FUNCTION public.handle_new_message(); 