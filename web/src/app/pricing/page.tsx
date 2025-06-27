'use client';

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { useRouter } from 'next/navigation';

export default function PricingPage() {
  const router = useRouter();

  const handleStartTrial = () => {
    // Redirect to signup with pro plan parameter
    router.push('/signup?plan=pro');
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <Card className="w-full max-w-sm">
        <CardHeader>
          <CardTitle className="text-2xl font-bold text-center">Grizz Pro</CardTitle>
          <CardDescription className="text-center">
            7-day free trial, then $10/month
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="text-center text-3xl font-bold">
            $10
            <span className="text-sm font-normal text-muted-foreground">/month</span>
          </div>
          <ul className="space-y-2 text-sm">
            <li className="flex items-center">
              <svg
                className="mr-2 h-4 w-4"
                fill="none"
                stroke="currentColor"
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth="2"
                viewBox="0 0 24 24"
              >
                <path d="M20 6L9 17l-5-5" />
              </svg>
              Unlimited conversations
            </li>
            <li className="flex items-center">
              <svg
                className="mr-2 h-4 w-4"
                fill="none"
                stroke="currentColor"
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth="2"
                viewBox="0 0 24 24"
              >
                <path d="M20 6L9 17l-5-5" />
              </svg>
              Advanced AI features
            </li>
            <li className="flex items-center">
              <svg
                className="mr-2 h-4 w-4"
                fill="none"
                stroke="currentColor"
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth="2"
                viewBox="0 0 24 24"
              >
                <path d="M20 6L9 17l-5-5" />
              </svg>
              Priority support
            </li>
          </ul>
        </CardContent>
        <CardFooter>
          <Button 
            className="w-full" 
            size="lg"
            onClick={handleStartTrial}
          >
            Start 7-Day Free Trial
          </Button>
        </CardFooter>
      </Card>
    </div>
  );
} 