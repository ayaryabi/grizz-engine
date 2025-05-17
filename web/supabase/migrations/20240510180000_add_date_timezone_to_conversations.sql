-- Add date and timezone columns to conversations
ALTER TABLE public.conversations ADD COLUMN date DATE NOT NULL DEFAULT (CURRENT_DATE);
ALTER TABLE public.conversations ADD COLUMN timezone TEXT;

-- Add unique index to ensure only one conversation per user per day
CREATE UNIQUE INDEX uniq_user_date ON public.conversations(user_id, date);

-- Add comments
COMMENT ON COLUMN public.conversations.date IS 'The day (in user''s timezone) this conversation belongs to.';
COMMENT ON COLUMN public.conversations.timezone IS 'The user''s timezone for this conversation.';

-- Drop unneeded tables for MVP simplicity
DROP TABLE IF EXISTS public.byte_links CASCADE;
DROP TABLE IF EXISTS public.byte_entity_links CASCADE;
DROP TABLE IF EXISTS public.entities CASCADE;
DROP TABLE IF EXISTS public.entity_entity_links CASCADE; 