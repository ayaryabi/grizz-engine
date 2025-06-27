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
import Link from 'next/link';

export default function SignupPage() {
  const [firstName, setFirstName] = useState('');
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');
  const router = useRouter();

  const handleSignup = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setLoading(true);
    setErrorMsg('');

    try {
      // Store first name in localStorage for later
      localStorage.setItem('signup_first_name', firstName);

      // Try to sign in WITHOUT creating a new user
      const { error: checkError } = await supabase.auth.signInWithOtp({
        email,
        options: { shouldCreateUser: false }
      });

      // If sign in succeeds, user exists
      if (!checkError) {
        setErrorMsg('An account with this email already exists. Please sign in instead.');
        setLoading(false);
        return;
      }

      // If we get here, user doesn't exist, so create new account
      const { error } = await supabase.auth.signInWithOtp({
        email,
        options: {
          shouldCreateUser: true,
          data: {
            first_name: firstName,
          },
        },
      });
      
      if (error) throw error;

      // Get plan from URL if it exists
      const searchParams = new URLSearchParams(window.location.search);
      const plan = searchParams.get('plan');
      
      // Redirect to verification page, passing along plan if it exists
      const verifyUrl = `/verify?email=${encodeURIComponent(email)}${plan ? `&plan=${plan}` : ''}`;
      
      // Important: Don't reset loading state before redirect
      router.push(verifyUrl);
    } catch (err) {
      setErrorMsg(err instanceof Error ? err.message : 'Unable to send verification email');
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center p-4">
      <Card className="w-full max-w-sm">
        <CardHeader className="text-center">
          <CardTitle className="text-2xl font-semibold">Create Account</CardTitle>
          <CardDescription>Start your 7-day free trial today</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSignup} className="space-y-4">
            <div className="space-y-1.5">
              <Label htmlFor="firstName">First Name</Label>
              <Input
                id="firstName"
                type="text"
                required
                placeholder="John"
                value={firstName}
                onChange={(e) => setFirstName(e.target.value)}
                disabled={loading}
              />
            </div>

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
              {loading ? 'Creating Account…' : 'Continue'}
            </Button>

            <p className="text-sm text-center text-muted-foreground">
              Already have an account?{' '}
              <Link href="/signin" className="font-medium underline underline-offset-4 hover:text-primary">
                Sign in
              </Link>
            </p>
          </form>
        </CardContent>
      </Card>
    </div>
  );
} 