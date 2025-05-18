'use client';

import { useState } from 'react';
import { useAuth } from '@/features/auth/AuthContext';
import Link from 'next/link';
import { supabase } from '@/lib/supabase/supabase';

export default function TestConversationPage() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<any>(null);
  const { user, profile, loading: authLoading } = useAuth();

  const testGetConversation = async () => {
    if (!user) {
      setError('Not authenticated. Please log in first.');
      return;
    }

    setLoading(true);
    setError(null);
    
    try {
      // Get current timezone
      const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
      
      // Get the session to extract the access token
      const { data: { session } } = await supabase.auth.getSession();
      const accessToken = session?.access_token;
      
      if (!accessToken) {
        throw new Error("Could not get access token");
      }
      
      // Call our Next.js API route
      const response = await fetch('/api/chat/today', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${accessToken}`
        },
        body: JSON.stringify({ timezone })
      });
      
      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.error || 'Failed to get conversation');
      }
      
      setResult(data);
    } catch (err: any) {
      setError(err.message || 'Failed to get conversation');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-8 max-w-xl mx-auto">
      <h1 className="text-2xl font-bold mb-4">Test Conversation API</h1>
      
      {authLoading ? (
        <div className="mb-4 p-4 bg-gray-100 border border-gray-300 rounded">
          Checking authentication status...
        </div>
      ) : !user ? (
        <div className="mb-4 p-4 bg-yellow-100 border border-yellow-400 rounded">
          <p className="mb-2"><strong>Not logged in.</strong> Please log in first.</p>
          <Link href="/login" className="text-blue-600 underline">Go to login page</Link>
        </div>
      ) : (
        <div className="mb-4 p-4 bg-green-100 border border-green-400 rounded">
          <p><strong>Logged in as:</strong> {profile?.display_name || user.email}</p>
          <p className="text-sm mt-1">User ID: {user.id}</p>
        </div>
      )}
      
      <button 
        onClick={testGetConversation}
        disabled={loading || authLoading || !user}
        className="px-4 py-2 bg-blue-500 text-white rounded disabled:bg-gray-300 disabled:cursor-not-allowed"
      >
        {loading ? 'Testing...' : 'Test Get Conversation'}
      </button>
      
      {error && (
        <div className="mt-4 p-4 bg-red-100 border border-red-400 rounded">
          <strong>Error:</strong> {error}
        </div>
      )}
      
      {result && (
        <div className="mt-4">
          <h2 className="text-xl font-bold mb-2">Result:</h2>
          <pre className="p-4 bg-gray-100 rounded overflow-auto">
            {JSON.stringify(result, null, 2)}
          </pre>
        </div>
      )}
      
      <div className="mt-6">
        <h3 className="text-lg font-bold mb-2">Auth Debug Info:</h3>
        <pre className="p-4 bg-gray-100 rounded overflow-auto text-xs">
          {JSON.stringify({ 
            isLoggedIn: !!user, 
            userId: user?.id,
            hasProfile: !!profile,
            isLoading: authLoading 
          }, null, 2)}
        </pre>
      </div>
    </div>
  );
} 