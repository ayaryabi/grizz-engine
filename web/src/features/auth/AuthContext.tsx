'use client';

import React, { createContext, useState, useEffect, useContext, ReactNode, useCallback, useRef } from 'react';
import { useRouter, usePathname } from 'next/navigation'; // Import usePathname
import { supabase } from '@/lib/supabase/supabase'; // Adjust path if needed
import type { Session, User } from '@supabase/supabase-js';

// Define the shape of our Profile data (can be expanded later)
type Profile = {
  user_id: string;
  display_name: string | null;
  avatar_url: string | null;
  // Add other profile fields here as needed
};

// Define the shape of the context value
interface AuthContextType {
  session: Session | null;
  user: User | null;
  profile: Profile | null;
  loading: boolean; // True if initial auth check is not done OR if profile is being fetched
  signOut: () => Promise<void>;
}

// Create the context with a default value
const AuthContext = createContext<AuthContextType | undefined>(undefined);

// Define the props for the provider
interface AuthProviderProps {
  children: ReactNode;
}

// Create the AuthProvider component
export function AuthProvider({ children }: AuthProviderProps) {
  const [session, setSession] = useState<Session | null>(null);
  const [user, setUser] = useState<User | null>(null);
  const [profile, setProfile] = useState<Profile | null>(null);
  const [isLoadingProfile, setIsLoadingProfile] = useState(false);
  const [isAuthReady, setIsAuthReady] = useState(false); // Tracks if initial session/auth check is complete
  const router = useRouter();
  const pathname = usePathname(); // Get current path
  
  // Ref to prevent concurrent profile fetches (fixes triple fetch bug)
  const fetchingUserRef = useRef<string | null>(null);

  const fetchProfileData = useCallback(async (userId: string | undefined) => {
    if (!userId) {
      setProfile(null);
      setIsLoadingProfile(false);
      return;
    }
    
    // Synchronous protection against concurrent fetches (fixes triple fetch bug)
    if ((profile?.user_id === userId && !isLoadingProfile) || 
        fetchingUserRef.current === userId) {
      // console.log(`AuthContext: Profile for user ${userId} already loaded or being fetched. Skipping.`);
      return;
    }
    
    // Immediately lock this user ID to prevent concurrent fetches
    fetchingUserRef.current = userId;
    console.log(`AuthContext: Fetching profile for user: ${userId}`);
    setIsLoadingProfile(true);
    
    try {
      const { data, error, status } = await supabase
        .from('profiles')
        .select('user_id, display_name, avatar_url')
        .eq('user_id', userId)
        .single();

      if (error && status !== 406) {
        console.error('AuthContext: Error fetching profile:', error);
        setProfile(null);
      } else if (data) {
        // console.log('AuthContext: Profile data fetched:', data);
        setProfile(data as Profile);
      } else {
        // console.log('AuthContext: No profile found for user.');
        setProfile(null);
      }
    } catch (e) {
      console.error('AuthContext: Exception in fetchProfileData:', e);
      setProfile(null);
    } finally {
      // Release the lock and loading state
      fetchingUserRef.current = null;
      setIsLoadingProfile(false);
    }
  }, [profile?.user_id, isLoadingProfile]); // Added isLoadingProfile to dependencies

  // Effect for initial session check and setting up auth listener
  useEffect(() => {
    let isMounted = true;
    setIsAuthReady(false);

    supabase.auth.getSession().then(async ({ data: { session: initialSession } }) => {
      if (!isMounted) return;
      const initialUser = initialSession?.user ?? null;
      setSession(initialSession);
      setUser(initialUser);
      
      // Start profile fetch in parallel, don't wait for it to complete
      if (initialUser?.id) {
        fetchProfileData(initialUser.id); // Don't await - parallel execution
      }
      
      setIsAuthReady(true); // Set ready immediately after session, don't wait for profile
    });

    const { data: authListener } = supabase.auth.onAuthStateChange(
      async (_event, currentSession) => {
        if (!isMounted) return;
        // console.log('AuthContext: Auth state changed:', _event);
        const newSession = currentSession;
        const newUser = newSession?.user ?? null;
        
        setSession(newSession);
        setUser(newUser); // This will trigger profile fetch via the other useEffect if user changes
        if (!newUser) {
            setProfile(null); // Clear profile if user is logged out
        }
      }
    );
    return () => {
      isMounted = false;
      authListener?.subscription.unsubscribe();
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // fetchProfileData is memoized, so it's stable here

  // Effect to fetch profile when user object changes and is not null
  useEffect(() => {
    if (user && user.id !== profile?.user_id) {
        fetchProfileData(user.id);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user]); // Depends on user object and memoized fetchProfileData

  // Effect for handling re-check on tab visibility change
  useEffect(() => {
    const handleVisibilityChange = async () => {
      if (document.visibilityState === 'visible') {
        console.log("AuthContext: Tab became visible, re-checking auth state.");
        setIsAuthReady(false); // Indicate we are re-checking
        const { data: { session: currentSession } } = await supabase.auth.getSession();
        const currentUser = currentSession?.user ?? null;
        setSession(currentSession);
        setUser(currentUser);
        if (currentUser) {
          // Only fetch profile if user exists and it's different from current or not loading
          if (currentUser.id !== profile?.user_id || !profile) {
             await fetchProfileData(currentUser.id);
          }
        } else {
          setProfile(null); // No user, clear profile
        }
        setIsAuthReady(true);
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);
    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [fetchProfileData]); // Re-run if fetchProfileData changes (it shouldn't often due to useCallback)

  // Effect for handling redirection (simplified, relies on other effects to set state)
  useEffect(() => {
    // Only proceed if auth state is fully loaded and we're not loading profile
    if (!isAuthReady || isLoadingProfile) return;

    // List of protected routes that require authentication
    const protectedRoutes = ['/dashboard', '/chat', '/settings', '/document', '/bytes'];
    const isProtectedRoute = protectedRoutes.some(route => pathname?.startsWith(route));
    
    // If we're on a protected route and no user is found, redirect to auth
    if (isProtectedRoute && !user) {
      console.log('AuthContext: No user found on protected route, redirecting to /auth');
      router.push('/auth');
    }

    // Let middleware handle redirect from auth page when logged in
  }, [user, profile, isLoadingProfile, isAuthReady, router, pathname]);

  // Sign out function
  const signOut = async () => {
    setIsLoadingProfile(true); // To prevent UI flicker or race conditions during sign out
    await supabase.auth.signOut();
    // Auth listener will handle clearing session, user, and profile state
  };

  // The value provided to consuming components
  const contextValue: AuthContextType = {
    session,
    user,
    profile,
    loading: !isAuthReady, // Only block on auth readiness, let profile load in background
    signOut,
  };

  return <AuthContext.Provider value={contextValue}>{children}</AuthContext.Provider>;
}

// Custom hook to use the AuthContext
export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
} 