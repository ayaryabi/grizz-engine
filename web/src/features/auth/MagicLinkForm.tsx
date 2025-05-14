'use client';

import React, { useState } from 'react';
import { supabase } from '@/lib/supabase/supabase'; // Adjust import path based on your alias setup
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

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
    <Card className="w-full max-w-sm">
      <CardHeader className="text-center">
        <CardTitle className="text-2xl font-semibold">Sign In / Sign Up</CardTitle>
        <CardDescription className="text-sm">Enter your email below to receive a magic link.</CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleLogin} className="space-y-4">
          <div className="space-y-1.5">
            <Label htmlFor="email">Email</Label>
            <Input
              id="email"
              type="email"
              placeholder="your@email.com"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              disabled={loading}
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
              <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-current" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
            ) : null}
            {loading ? 'Sending...' : 'Send Magic Link'}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
} 