import { createServerClient, type CookieOptions } from '@supabase/ssr'
import { NextResponse, type NextRequest } from 'next/server'

export async function middleware(request: NextRequest) {
  let response = NextResponse.next({
    request: {
      headers: request.headers,
    },
  })

  // Create a Supabase client specific to this middleware request
  const supabase = createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        get(name: string) {
          return request.cookies.get(name)?.value
        },
        set(name: string, value: string, options: CookieOptions) {
          // If the cookie is updated, update the request cookies and response cookies
          request.cookies.set({
            name,
            value,
            ...options,
          })
          response = NextResponse.next({
            request: {
              headers: request.headers,
            },
          })
          response.cookies.set({
            name,
            value,
            ...options,
          })
        },
        remove(name: string, options: CookieOptions) {
          // If the cookie is removed, update the request cookies and response cookies
          request.cookies.set({
            name,
            value: '',
            ...options,
          })
          response = NextResponse.next({
            request: {
              headers: request.headers,
            },
          })
          response.cookies.set({
            name,
            value: '',
            ...options,
          })
        },
      },
    }
  )

  // Refresh session if expired - required for Server Components
  // https://supabase.com/docs/guides/auth/auth-helpers/nextjs#managing-session-with-middleware
  const { data: { user } } = await supabase.auth.getUser()

  const { pathname } = request.nextUrl;

  // Define protected routes (adjust as needed)
  const protectedRoutes = ['/dashboard', '/chat', '/settings', '/document', '/bytes']; 
  // Define auth route
  const authRoute = '/auth';

  const isProtectedRoute = protectedRoutes.some(route => pathname.startsWith(route));

  // Redirect to login if trying to access protected route without session
  if (isProtectedRoute && !user) {
    console.log('Middleware: No user, redirecting to auth from', pathname);
    return NextResponse.redirect(new URL(authRoute, request.url))
  }

  // Redirect to homepage if trying to access auth route with session
  // Re-enabling this block and setting redirect to root
  if (pathname === authRoute && user) {
    // Default redirect path set to homepage '/' for now
    const redirectPath = '/'; 
    console.log('Middleware: User found, redirecting to homepage from', pathname);
    return NextResponse.redirect(new URL(redirectPath, request.url))
  }

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
     * Feel free to modify this pattern to include more paths.
     */
    '/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)',
    // Add specific routes if needed, but the above pattern is generally good
    // '/dashboard/:path*',
    // '/chat/:path*',
    // '/auth',
  ],
} 