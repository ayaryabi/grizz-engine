import { createServerClient, type CookieOptions } from '@supabase/ssr'
import { NextResponse, type NextRequest } from 'next/server'

export async function middleware(request: NextRequest) {
  // Create an initial response object
  const response = NextResponse.next({
    request: {
      headers: request.headers,
    },
  })

  // Create the Supabase client
  const supabase = createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        get(name: string) {
          return request.cookies.get(name)?.value
        },
        set(name: string, value: string, options: CookieOptions) {
          // CRITICAL: Don't create a new response - modify the existing one
          response.cookies.set({
            name,
            value,
            ...options,
          })
        },
        remove(name: string, options: CookieOptions) {
          // CRITICAL: Don't create a new response - modify the existing one
          response.cookies.set({
            name,
            value: '',
            ...options,
          })
        },
      },
    }
  )

  // CRITICAL: First get the session, which will refresh tokens if needed
  const { data: { session } } = await supabase.auth.getSession()
  
  // For debugging - log if we have a session
  console.log(`Middleware running for path: ${request.nextUrl.pathname}`)
  console.log(`Session exists: ${!!session}`)
  if (session) console.log(`User ID: ${session.user.id}`)

  const { pathname } = request.nextUrl;
  const authRoute = '/auth';

  // NEW APPROACH: Only redirect from auth page when we know user is logged in
  // For protected routes, we'll let client-side auth handle the redirect to login
  // This avoids the race condition between middleware and client auth state

  // Case: Auth route with session
  if (pathname === authRoute && session) {
    console.log('Session found on auth page, redirecting to home')
    return NextResponse.redirect(new URL('/', request.url))
  }

  // All other cases: Return the response with refreshed cookies
  // Let client-side authentication handle protected routes access
  return response
}

// Define which paths middleware should run on
export const config = {
  matcher: [
    /*
     * Match all request paths except for the ones starting with:
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     */
    '/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)',
  ],
} 