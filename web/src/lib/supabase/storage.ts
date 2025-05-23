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
  
  console.log('Upload attempt:', {
    providedUserId: userId,
    authUserId: user.id,
    userIdMatch: userId === user.id
  });

  const timestamp = Date.now();
  const fileName = `${timestamp}_${file.name.replace(/[^a-zA-Z0-9.-]/g, '_')}`;
  const filePath = `${userId}/${fileName}`;
  
  console.log('Upload path:', filePath);

  const { data, error } = await supabase.storage
    .from('chat-files')
    .upload(filePath, file, {
      cacheControl: '3600',
      upsert: false
    });

  if (error) {
    throw new Error(`Upload failed: ${error.message}`);
  }

  const { data: urlData } = supabase.storage
    .from('chat-files')
    .getPublicUrl(filePath);

  return urlData.publicUrl;
}
