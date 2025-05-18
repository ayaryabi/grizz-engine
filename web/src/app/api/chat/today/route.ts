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
    console.log('Received request to /api/chat/today');
    
    // Extract the authorization header from the incoming request
    const authHeader = request.headers.get('authorization');
    if (!authHeader || !authHeader.startsWith('Bearer ')) {
      console.log('Missing or invalid authorization header');
      return NextResponse.json({ error: 'Authorization header required' }, { status: 401 });
    }

    // Extract the token
    const token = authHeader.substring(7); // Remove 'Bearer ' prefix
    console.log('Got auth token');

    // Extract timezone from request body
    let requestBody;
    try {
      requestBody = await request.json();
      console.log('Request body:', requestBody);
      console.log('Timezone sent to backend:', requestBody.timezone);
    } catch (e) {
      console.error('Failed to parse request body:', e);
      return NextResponse.json({ error: 'Invalid request body' }, { status: 400 });
    }

    const { timezone } = requestBody;
    if (!timezone) {
      console.log('Missing timezone in request body');
      return NextResponse.json({ error: 'Timezone is required' }, { status: 400 });
    }
    console.log('Using timezone:', timezone);

    // Get user from token
    console.log('Getting user info from Supabase with token');
    const { data: userData, error: userError } = await supabase.auth.getUser(token);
    if (userError) {
      console.error('Supabase auth error:', userError);
      return NextResponse.json({ error: 'Unauthorized: Invalid token', details: userError.message }, { status: 401 });
    }
    
    if (!userData || !userData.user) {
      console.error('No user data returned from Supabase');
      return NextResponse.json({ error: 'Unauthorized: No user found' }, { status: 401 });
    }

    const userId = userData.user.id;
    console.log('User authenticated, ID:', userId);

    // Construct the URL for the GET request to FastAPI
    // Use the correct endpoint path from main.py - conversation_router is mounted at /api
    const url = new URL(`${FASTAPI_BACKEND_URL}/api/conversations/today`);
    url.searchParams.append('user_id', userId);
    url.searchParams.append('tz', timezone);
    
    console.log(`Calling FastAPI at: ${url.toString()}`);

    // Call FastAPI backend
    let fastApiResponse;
    try {
      fastApiResponse = await fetch(url.toString(), {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });
      console.log('FastAPI response status:', fastApiResponse.status);
    } catch (e: any) {
      console.error('Error making request to FastAPI:', e);
      return NextResponse.json({ 
        error: 'Failed to connect to backend service', 
        details: e.message 
      }, { status: 502 });
    }

    if (!fastApiResponse.ok) {
      let errorBody = 'Unknown error';
      try {
        errorBody = await fastApiResponse.text();
        console.error('FastAPI error response body:', errorBody);
      } catch (e) {
        console.error('Could not read FastAPI error response body:', e);
      }
      console.error(`FastAPI error: ${fastApiResponse.status}`, errorBody);
      return NextResponse.json({ 
        error: `Failed to get conversation: ${fastApiResponse.statusText}`, 
        details: errorBody 
      }, { status: fastApiResponse.status });
    }

    let conversationData;
    try {
      conversationData = await fastApiResponse.json();
      console.log('FastAPI conversation data:', conversationData);
    } catch (e: any) {
      console.error('Error parsing FastAPI response:', e);
      return NextResponse.json({ 
        error: 'Invalid response from backend', 
        details: e.message 
      }, { status: 500 });
    }
    
    return NextResponse.json(conversationData);

  } catch (error: any) {
    console.error('Unhandled error in /api/chat/today:', error);
    return NextResponse.json({ 
      error: 'Internal Server Error', 
      details: error.message,
      stack: process.env.NODE_ENV === 'development' ? error.stack : undefined
    }, { status: 500 });
  }
} 