'use client';

import React, { useState, useEffect } from 'react';
import { supabase } from '@/lib/supabase/supabase';
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
import { useRouter, useSearchParams } from 'next/navigation';

export function MagicLinkForm() {
  const [email, setEmail] = useState('');
  const [code, setCode] = useState('');
  const [loading, setLoading] = useState(false);
  const [infoMsg, setInfoMsg] = useState('');
  const [errorMsg, setErrorMsg] = useState('');
  const router = useRouter();
  const searchParams = useSearchParams();

  useEffect(() => {
    // Get email from URL params
    const emailParam = searchParams.get('email');
    if (emailParam) {
      setEmail(emailParam);
    }
  }, [searchParams]);

  const verifyCode = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setLoading(true);
    setErrorMsg('');

    try {
      const { error } = await supabase.auth.verifyOtp({
        email,
        token: code,
        type: 'email',
      });
      if (error) throw error;

      // Get stored first name and check for plan parameter
      const firstName = localStorage.getItem('signup_first_name');
      const searchParams = new URLSearchParams(window.location.search);
      const plan = searchParams.get('plan');
      
      if (firstName) {
        // This was a signup
        localStorage.removeItem('signup_first_name');
        
        if (plan === 'pro') {
          // User came from pricing - redirect to checkout
          setInfoMsg('Account created! Setting up your plan...');
          router.replace('/checkout');
        } else {
          // Normal signup - redirect to chat
          setInfoMsg('Account created! Redirecting...');
          router.replace('/chat');
        }
      } else {
        // This was a signin - redirect to chat
        setInfoMsg('Welcome back! Redirecting...');
        router.replace('/chat');
      }
    } catch (err) {
      setErrorMsg(err instanceof Error ? err.message : 'Invalid code');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card className="w-full max-w-sm">
      <CardHeader className="text-center">
        <CardTitle className="text-2xl font-semibold">Enter the Code</CardTitle>
        <CardDescription className="text-sm">
          Check your e-mail (<span className="font-medium">{email}</span>)
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={verifyCode} className="space-y-4">
          <div className="space-y-1.5">
            <Label htmlFor="code">6-digit Code</Label>
            <Input
              id="code"
              type="text"
              pattern="[0-9]{6}"
              maxLength={6}
              required
              inputMode="numeric"
              value={code}
              onChange={(e) => setCode(e.target.value)}
              disabled={loading}
            />
          </div>

          {infoMsg && <p className="text-sm text-green-600">{infoMsg}</p>}
          {errorMsg && <p className="text-sm text-red-600">{errorMsg}</p>}

          <Button type="submit" disabled={loading} className="w-full">
            {loading ? 'Verifying…' : 'Verify & Continue'}
          </Button>
          <p className="text-xs text-center text-muted-foreground">
            Didn&apos;t get it?{' '}
            <button
              type="button"
              className="underline"
              onClick={() => {
                // Go back to appropriate page
                const firstName = localStorage.getItem('signup_first_name');
                router.push(firstName ? '/signup' : '/signin');
              }}
            >
              Try Again
            </button>
          </p>
        </form>
      </CardContent>
    </Card>
  );
} 