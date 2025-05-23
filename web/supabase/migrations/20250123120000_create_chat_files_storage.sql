-- Create chat-files storage bucket for file uploads
INSERT INTO storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
VALUES (
  'chat-files',
  'chat-files', 
  false,
  52428800, -- 50MB in bytes
  ARRAY[
    'image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp',
    'application/pdf', 
    'text/plain', 'text/markdown',
    'audio/mpeg', 'audio/wav', 'audio/mp4',
    'video/mp4', 'video/quicktime'
  ]
)
ON CONFLICT (id) DO NOTHING;

-- Enable RLS on storage.objects (should already be enabled)
ALTER TABLE storage.objects ENABLE ROW LEVEL SECURITY;

-- Policy: Allow authenticated users to upload files to their own folder
CREATE POLICY "Users can upload to own folder" 
ON storage.objects 
FOR INSERT 
TO authenticated 
WITH CHECK (
  bucket_id = 'chat-files' 
  AND (storage.foldername(name))[1] = auth.uid()::text
);

-- Policy: Allow authenticated users to view their own files
CREATE POLICY "Users can view own files" 
ON storage.objects 
FOR SELECT 
TO authenticated 
USING (
  bucket_id = 'chat-files' 
  AND (storage.foldername(name))[1] = auth.uid()::text
);

-- Policy: Allow authenticated users to delete their own files
CREATE POLICY "Users can delete own files" 
ON storage.objects 
FOR DELETE 
TO authenticated 
USING (
  bucket_id = 'chat-files' 
  AND (storage.foldername(name))[1] = auth.uid()::text
);

-- Add comments
COMMENT ON POLICY "Users can upload to own folder" ON storage.objects IS 'Users can only upload files to folders matching their user ID';
COMMENT ON POLICY "Users can view own files" ON storage.objects IS 'Users can only view files in their own folder';
COMMENT ON POLICY "Users can delete own files" ON storage.objects IS 'Users can only delete files in their own folder'; 