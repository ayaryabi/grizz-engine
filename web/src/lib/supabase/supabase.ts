import { createClient } from '@supabase/supabase-js'

// Read environment variables
const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY

// Validate environment variables
if (!supabaseUrl) {
  throw new Error("Missing environment variable: NEXT_PUBLIC_SUPABASE_URL")
}
if (!supabaseAnonKey) {
  throw new Error("Missing environment variable: NEXT_PUBLIC_SUPABASE_ANON_KEY")
}

// Initialize the Supabase client
// The generic type is optional, but helpful for RLS policies and type safety
// We can add the generated DB types later if needed
export const supabase = createClient(supabaseUrl, supabaseAnonKey)

// Note: We might enhance this later with server-side clients or specific configurations
// if needed for server components or API routes, but this covers the basic client-side setup. 