'use client';

import React, { createContext, useState, useEffect, useContext, ReactNode } from 'react';
import { useRouter } from 'next/navigation'; // Import useRouter
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
  loading: boolean;
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
  const [loading, setLoading] = useState(true); // Start loading initially
  const router = useRouter(); // Initialize router

  // Function to fetch user profile
  const fetchProfile = async (userId: string) => {
    try {
      console.log('Fetching profile for user:', userId);
      const { data, error, status } = await supabase
        .from('profiles')
        .select(`user_id, display_name, avatar_url`)
        .eq('user_id', userId)
        .single();

      if (error && status !== 406) {
        // 406 status means no row found, which is expected for new users
        console.error('Error fetching profile:', error);
        throw error;
      }

      if (data) {
        console.log('Profile data fetched:', data);
        setProfile(data as Profile);
      } else {
        console.log('No profile found for user (might be first login).');
        setProfile(null); // Ensure profile is null if not found
      }
    } catch (error) {
      console.error('Exception in fetchProfile:', error);
      setProfile(null); // Reset profile on error
    } 
  };

  // Effect to handle auth state changes
  useEffect(() => {
    let isMounted = true; // Prevent state updates if unmounted
    setLoading(true);
    // Get initial session 
    supabase.auth.getSession().then(async ({ data: { session } }) => {
      if (!isMounted) return;
      setSession(session);
      setUser(session?.user ?? null);
      if (session?.user) {
        await fetchProfile(session.user.id);
      }
      setLoading(false);
    });

    // Listen for auth state changes
    const { data: authListener } = supabase.auth.onAuthStateChange(
      async (_event, session) => {
        if (!isMounted) return;
        console.log('Auth state changed:', _event, session);
        const currentUser = session?.user ?? null;
        const previousUser = user; // Capture previous user state
        
        setSession(session);
        setUser(currentUser);
        
        // Fetch profile only if user logged in and profile isn't already loaded (or if user changed)
        if (currentUser && currentUser.id !== profile?.user_id) { 
          setLoading(true);
          await fetchProfile(currentUser.id);
          setLoading(false);
        } else if (!currentUser) {
          setProfile(null); // Clear profile on logout
        }

        // *** Modify Redirect Logic ***
        // Redirect if we now have a user but didn't before
        if (currentUser && !previousUser) {
          console.log(`Redirecting to / because currentUser exists (${currentUser.id}) and previousUser was null.`);
          router.push('/'); // Redirect to homepage on login detection
        }
        // Optional: Redirect on sign out?
        // if (!currentUser && previousUser) { // Check if user just logged out
        //   console.log('Redirecting to /auth after sign out');
        //   router.push('/auth');
        // }
      }
    );

    // Cleanup listener on component unmount
    return () => {
      isMounted = false; // Set flag on unmount
      authListener?.subscription.unsubscribe();
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // Dependencies removed to ensure router isn't causing re-runs, manage manually

  // Sign out function
  const signOut = async () => {
    setLoading(true);
    const { error } = await supabase.auth.signOut();
    if (error) {
      console.error('Error signing out:', error);
    } else {
      // State updates handled by onAuthStateChange listener
      console.log('Signed out successfully');
    }
    setLoading(false);
  };

  // The value provided to consuming components
  const value = {
    session,
    user,
    profile,
    loading,
    signOut,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

// Custom hook to use the AuthContext
export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
} 