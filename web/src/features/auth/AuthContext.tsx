'use client';

import React, { createContext, useState, useEffect, useContext, ReactNode } from 'react';
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

  // Function to fetch user profile
  const fetchProfileData = async (userId: string) => {
    // Avoid fetching if profile for this user is already loaded and matches
    if (profile?.user_id === userId) {
      console.log(`AuthContext: Profile for user ${userId} already loaded. Skipping fetch.`);
      return;
    }
    
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
        console.log('AuthContext: Profile data fetched:', data);
        setProfile(data as Profile);
      } else {
        console.log('AuthContext: No profile found for user (might be first login).');
        setProfile(null);
      }
    } catch (e) {
      console.error('AuthContext: Exception in fetchProfileData:', e);
      setProfile(null);
    } finally {
      setIsLoadingProfile(false);
    }
  };

  // Effect for initial session check and setting up auth listener
  useEffect(() => {
    let isMounted = true;
    setIsAuthReady(false); // Mark auth as not ready until initial check is done

    // 1. Check for initial session
    supabase.auth.getSession().then(async ({ data: { session: initialSession } }) => {
      if (!isMounted) return;

      const initialUser = initialSession?.user ?? null;
      setSession(initialSession);
      setUser(initialUser);

      if (initialUser) {
        await fetchProfileData(initialUser.id);
      } else {
        setProfile(null); // No user, so no profile
      }
      setIsAuthReady(true); // Initial session check complete
    });

    // 2. Set up auth state change listener
    const { data: authListener } = supabase.auth.onAuthStateChange(
      async (_event, currentSession) => {
        if (!isMounted) return;
        
        console.log('AuthContext: Auth state changed:', _event, currentSession);
        const newSession = currentSession;
        const newUser = newSession?.user ?? null;
        const oldUserId = user?.id; // Get user ID from previous state (closure)

        setSession(newSession);
        setUser(newUser);

        if (newUser) {
          // Fetch profile if user ID has changed, or if it's a new user and profile wasn't for them
          if (newUser.id !== oldUserId || profile?.user_id !== newUser.id) {
            await fetchProfileData(newUser.id);
          }
        } else {
          setProfile(null); // Clear profile on logout
        }
      }
    );

    return () => {
      isMounted = false;
      authListener?.subscription.unsubscribe();
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // Empty dependency array: runs only on mount and unmount

  // Effect for handling redirection
  useEffect(() => {
    if (!isAuthReady || isLoadingProfile) {
      // Don't redirect if initial auth isn't ready or profile is still loading
      return;
    }

    if (user) {
      if (profile && profile.user_id === user.id) {
        if (pathname === '/auth') { 
          console.log(`AuthContext: User ${user.id} logged in with profile, on /auth. Redirecting to /.`);
          router.push('/');
        }
      } else if (!profile) {
        console.log(`AuthContext: User ${user.id} logged in, but no profile. Current path: ${pathname}. No automatic redirect.`);
      }
    } else { 
      // No user (logged out)
      // If not on /auth page, you might want to redirect to /auth
      // if (pathname !== '/auth') {
      //   console.log(`AuthContext: User logged out, not on /auth. Redirecting to /auth.`);
      //   router.push('/auth');
      // }
    }
  }, [user, profile, isLoadingProfile, isAuthReady, router, pathname]);

  // Sign out function
  const signOut = async () => {
    // Setting isLoadingProfile true here can prevent premature redirects during signout. 
    // onAuthStateChange will eventually lead to isLoadingProfile becoming false after profile is nullified.
    setIsLoadingProfile(true); 
    await supabase.auth.signOut();
    // onAuthStateChange will handle setting user, session, profile to null.
  };

  // The value provided to consuming components
  const contextValue: AuthContextType = {
    session,
    user,
    profile,
    loading: !isAuthReady || isLoadingProfile,
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