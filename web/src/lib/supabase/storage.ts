import { supabase } from './supabase';

export async function uploadToSupabase(file: File, userId: string): Promise<string> {
  const maxSize = 50 * 1024 * 1024;
  if (file.size > maxSize) {
    throw new Error('File size must be less than 50MB');
  }

  // Debug: Check if user is authenticated
  const { data: { user }, error: authError } = await supabase.auth.getUser();
  if (authError || !user) {
    throw new Error('User not authenticated for file upload');
  }
  
  const timestamp = Date.now();
  const fileName = `${timestamp}_${file.name.replace(/[^a-zA-Z0-9.-]/g, '_')}`;
  const filePath = `${userId}/${fileName}`;

  const { error } = await supabase.storage
    .from('chat-files')
    .upload(filePath, file, {
      cacheControl: '3600',
      upsert: false
    });

  if (error) {
    throw new Error(`Upload failed: ${error.message}`);
  }

  // Since our bucket is private, we need to create a signed URL
  const { data: urlData, error: urlError } = await supabase.storage
    .from('chat-files')
    .createSignedUrl(filePath, 60 * 60 * 24 * 365); // 1 year expiry

  if (urlError) {
    throw new Error(`Failed to create signed URL: ${urlError.message}`);
  }

  return urlData.signedUrl;
}
