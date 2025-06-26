'use client';

import React, { useState } from 'react';
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
import { useRouter } from 'next/navigation';

export function MagicLinkForm() {
  const [stage, setStage] = useState<'email' | 'code'>('email');
  const [email, setEmail] = useState('');
  const [code, setCode] = useState('');
  const [loading, setLoading] = useState(false);
  const [infoMsg, setInfoMsg] = useState('');
  const [errorMsg, setErrorMsg] = useState('');
  const router = useRouter();

  const sendCode = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setLoading(true);
    setErrorMsg('');

    try {
      const { error } = await supabase.auth.signInWithOtp({
        email,
        options: {
          shouldCreateUser: true, // sign-up if new
        },
      });
      if (error) throw error;

      setStage('code');
      setInfoMsg('We just emailed you a 6-digit code. Enter it below.');
    } catch (err) {
      setErrorMsg(err instanceof Error ? err.message : 'Unable to send code');
    } finally {
      setLoading(false);
    }
  };

  const verifyCode = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setLoading(true);
    setErrorMsg('');

    try {
      const { error } = await supabase.auth.verifyOtp({
        email,
        token: code,
        type: 'email', // verify sign-in / sign-up email OTP
      });
      if (error) throw error;

      // Supabase returned a session; AuthContext listener will redirect.
      setInfoMsg('Logged in! Redirecting…');
      // Small delay to show the message
      setTimeout(() => {
        router.replace('/');
      }, 500);
    } catch (err) {
      setErrorMsg(err instanceof Error ? err.message : 'Invalid code');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card className="w-full max-w-sm">
      <CardHeader className="text-center">
        <CardTitle className="text-2xl font-semibold">
          {stage === 'email' ? 'Sign In / Sign Up' : 'Enter the Code'}
        </CardTitle>
        {stage === 'email' ? (
          <CardDescription className="text-sm">We'll send a 6-digit code to your inbox.</CardDescription>
        ) : (
          <CardDescription className="text-sm">Check your e-mail (<span className="font-medium">{email}</span>)</CardDescription>
        )}
      </CardHeader>
      <CardContent>
        {stage === 'email' ? (
          <form onSubmit={sendCode} className="space-y-4">
            <div className="space-y-1.5">
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                required
                placeholder="you@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                disabled={loading}
              />
            </div>

            {errorMsg && <p className="text-sm text-red-600">{errorMsg}</p>}

            <Button type="submit" disabled={loading} className="w-full">
              {loading ? 'Sending…' : 'Send Code'}
            </Button>
          </form>
        ) : (
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
              Didn't get it?{' '}
              <button
                type="button"
                className="underline"
                onClick={() => {
                  // resend code
                  setStage('email');
                  setCode('');
                  setInfoMsg('');
                }}
              >
                Resend
              </button>
            </p>
          </form>
        )}
      </CardContent>
    </Card>
  );
} 