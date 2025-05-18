import { NextResponse } from 'next/server';
import { createClient } from '@supabase/supabase-js';

// Ensure this points to your FastAPI backend
const FASTAPI_BACKEND_URL = process.env.NEXT_PUBLIC_FASTAPI_BACKEND_URL || 'http://localhost:8000';

// Create a Supabase client using direct server-side auth
const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL ?? '',
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY ?? ''
);

export async function POST(request: Request) {
  try {
    // Extract the authorization header from the incoming request
    const authHeader = request.headers.get('authorization');
    if (!authHeader || !authHeader.startsWith('Bearer ')) {
      return NextResponse.json({ error: 'Authorization header required' }, { status: 401 });
    }

    // Extract the token
    const token = authHeader.substring(7); // Remove 'Bearer ' prefix

    // Extract timezone from request body
    const { timezone } = await request.json();
    if (!timezone) {
      return NextResponse.json({ error: 'Timezone is required' }, { status: 400 });
    }

    // Get user from token
    const { data: userData, error: userError } = await supabase.auth.getUser(token);
    if (userError || !userData.user) {
      console.error('Error getting user or no active user:', userError);
      return NextResponse.json({ error: 'Unauthorized: Invalid token' }, { status: 401 });
    }

    const userId = userData.user.id;

    // Construct the URL for the GET request to FastAPI
    const url = new URL(`${FASTAPI_BACKEND_URL}/conversations/today`);
    url.searchParams.append('user_id', userId);
    url.searchParams.append('timezone', timezone);

    // Call FastAPI backend
    const fastApiResponse = await fetch(url.toString(), {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!fastApiResponse.ok) {
      let errorBody = 'Unknown error';
      try {
        errorBody = await fastApiResponse.text();
      } catch (e) {
        // ignore if can't parse error body
      }
      console.error(`FastAPI error: ${fastApiResponse.status}`, errorBody);
      return NextResponse.json({ error: `Failed to get conversation: ${fastApiResponse.statusText}`, details: errorBody }, { status: fastApiResponse.status });
    }

    const conversationData = await fastApiResponse.json();
    return NextResponse.json(conversationData);

  } catch (error: any) {
    console.error('Error in /api/chat/today:', error);
    return NextResponse.json({ error: 'Internal Server Error', details: error.message }, { status: 500 });
  }
} 