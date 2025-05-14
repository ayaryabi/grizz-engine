'use client';

import React, { useState } from 'react';
import { supabase } from '@/lib/supabase/supabase'; // Adjust import path based on your alias setup
import { Button } from "@/components/ui/button";

export function MagicLinkForm() {
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [errorMsg, setErrorMsg] = useState('');

  const handleLogin = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setLoading(true);
    setMessage('');
    setErrorMsg('');

    try {
      const { error } = await supabase.auth.signInWithOtp({
        email: email,
        options: {
          // set this to localhost for testing or your main URL for production
          emailRedirectTo: window.location.origin, 
        },
      });

      if (error) throw error;

      setMessage('Check your email for the magic link!');
      setEmail(''); // Clear input on success

    } catch (error: any) {
      console.error("Error sending magic link:", error);
      setErrorMsg(error.error_description || error.message || 'An unexpected error occurred.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="w-full max-w-sm p-6 bg-white rounded-lg shadow-md dark:bg-gray-800">
      <h2 className="text-2xl font-semibold text-center text-gray-900 dark:text-white mb-2">Sign In / Sign Up</h2>
      <p className="text-sm text-center text-gray-600 dark:text-gray-400 mb-6">Enter your email below to receive a magic link.</p>
      <form onSubmit={handleLogin} className="space-y-4">
        <div>
          <label htmlFor="email" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
            Email
          </label>
          <input
            id="email"
            type="email"
            placeholder="your@email.com"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            disabled={loading}
            className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm dark:bg-gray-700 dark:border-gray-600 dark:text-white disabled:opacity-50"
          />
        </div>

        {message && <p className="text-sm text-green-600">{message}</p>}
        {errorMsg && <p className="text-sm text-red-600">Error: {errorMsg}</p>}

        <Button
          type="submit"
          disabled={loading}
          className="w-full"
        >
          {loading ? (
            <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
          ) : null}
          {loading ? 'Sending...' : 'Send Magic Link'}
        </Button>
      </form>
    </div>
  );
} 