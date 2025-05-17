'use client';

import { useAuth } from '@/features/auth/AuthContext';
import { useEffect, useState } from 'react';
import { supabase } from '@/lib/supabase/supabase';

export default function AuthDebugPage() {
  const { user, profile, loading, session } = useAuth();
  const [cookies, setCookies] = useState<string>('Loading...');
  
  useEffect(() => {
    // Log auth state on mount
    console.log('Auth Debug Page Mounted');
    console.log('Auth State from Context:', { 
      hasUser: !!user, 
      userId: user?.id,
      hasProfile: !!profile,
      isLoading: loading,
      hasSession: !!session
    });
    
    // Check direct with Supabase
    const checkSupabaseDirectly = async () => {
      const { data, error } = await supabase.auth.getSession();
      console.log('Direct Supabase Session Check:', {
        hasSession: !!data.session,
        userId: data.session?.user?.id,
        error: error?.message
      });
    };
    
    checkSupabaseDirectly();
    
    // Get cookies for debugging
    const cookieString = document.cookie;
    setCookies(cookieString);
  }, [user, profile, loading, session]);

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold mb-6">Authentication Debug Page</h1>
      
      <div className="grid gap-6">
        <div className="border p-4 rounded-lg">
          <h2 className="text-lg font-semibold mb-2">Auth Context State</h2>
          <div className="grid grid-cols-2 gap-2 text-sm">
            <div className="font-medium">Loading:</div>
            <div>{loading ? 'Yes' : 'No'}</div>
            
            <div className="font-medium">Logged In:</div>
            <div>{user ? 'Yes' : 'No'}</div>
            
            <div className="font-medium">User ID:</div>
            <div>{user?.id || 'None'}</div>
            
            <div className="font-medium">Email:</div>
            <div>{user?.email || 'None'}</div>
            
            <div className="font-medium">Profile:</div>
            <div>{profile ? 'Loaded' : 'Not Loaded'}</div>
            
            <div className="font-medium">Display Name:</div>
            <div>{profile?.display_name || 'None'}</div>
          </div>
        </div>
        
        <div className="border p-4 rounded-lg">
          <h2 className="text-lg font-semibold mb-2">Session Information</h2>
          <div className="grid grid-cols-2 gap-2 text-sm">
            <div className="font-medium">Has Session:</div>
            <div>{session ? 'Yes' : 'No'}</div>
            
            <div className="font-medium">Expires At:</div>
            <div>{session?.expires_at ? new Date(session.expires_at * 1000).toLocaleString() : 'N/A'}</div>
          </div>
        </div>
        
        <div className="border p-4 rounded-lg">
          <h2 className="text-lg font-semibold mb-2">Browser Cookies</h2>
          <pre className="text-xs bg-gray-100 p-3 rounded overflow-x-auto">{cookies}</pre>
        </div>
      </div>
      
      <div className="mt-6">
        <p className="text-sm text-gray-500">
          Check the browser console for additional debugging information.
        </p>
      </div>
    </div>
  );
} 