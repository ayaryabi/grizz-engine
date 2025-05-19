import { createServerClient, type CookieOptions } from '@supabase/ssr'
import { cookies } from 'next/headers'
import { ReadonlyRequestCookies } from 'next/dist/server/web/spec-extension/adapters/request-cookies'; // Might need adjustment

// Helper function to create server client, adaptable for different contexts
export function createSupabaseServerClient(cookieStore: ReadonlyRequestCookies) {
  return createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        get(name: string) {
          return cookieStore.get(name)?.value
        },
        set(name: string, value: string, options: CookieOptions) {
          // Server Components might try to set cookies, which triggers an error
          // We can often ignore this if middleware handles session refresh
          try {
             cookieStore.set({ name, value, ...options })
          } catch { }
        },
        remove(name: string, options: CookieOptions) {
           // Server Components might try to remove cookies, which triggers an error
           // We can often ignore this if middleware handles session refresh
          try {
             cookieStore.set({ name, value: '', ...options })
          } catch { }
        },
      },
    }
  );
}

// Specific function for use in Server Components/Route Handlers where `cookies()` is available
export async function createServerComponentClient() {
  const cookieStore = await cookies(); // Await the promise
  return createSupabaseServerClient(cookieStore);
}

// Note: For middleware, we'll create the client slightly differently using Request/Response 