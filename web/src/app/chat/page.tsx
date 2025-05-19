'use client';

import { useAuth } from '@/features/auth/AuthContext';
import { useEffect } from 'react';

export default function ChatPage() {
  const { user, profile, loading } = useAuth();
  
  // Debug logging
  useEffect(() => {
    console.log('Chat Page Mounted');
    console.log('Auth State:', { 
      isLoggedIn: !!user, 
      userId: user?.id,
      hasProfile: !!profile,
      isLoading: loading 
    });
  }, [user, profile, loading]);

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-4">Chat Page</h1>
      
      {loading ? (
        <p>Loading authentication state...</p>
      ) : user ? (
        <div>
          <p className="mb-2">Welcome, {profile?.display_name || user.email}</p>
          <p className="text-sm text-gray-500">User ID: {user.id}</p>
          <p className="mt-4">Chat interface will go here...</p>
        </div>
      ) : (
        <p>You should not see this message - if you do, there&apos;s an auth problem.</p>
      )}
    </div>
  );
} 