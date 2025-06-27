'use client';

import React from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { CreditCard, X } from 'lucide-react';

interface SubscriptionOverlayProps {
  onUpgrade: () => Promise<void>;
  onClose?: () => void;
  loading?: boolean;
}

export function SubscriptionOverlay({ onUpgrade, onClose, loading = false }: SubscriptionOverlayProps) {
  const handleUpgrade = async () => {
    try {
      await onUpgrade();
    } catch (error) {
      console.error('Failed to open subscription portal:', error);
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-background/20 backdrop-blur-sm flex items-center justify-center p-4 animate-in fade-in duration-300">
      <Card className="w-[380px] shadow-lg animate-in zoom-in-90 duration-300 relative">
        {onClose && (
          <button
            onClick={onClose}
            className="absolute top-4 right-4 text-muted-foreground hover:text-foreground transition-colors"
            aria-label="Close"
          >
            <X className="h-4 w-4" />
          </button>
        )}
        <CardHeader className="space-y-1">
          <div className="flex items-center gap-2">
            <CreditCard className="w-5 h-5 text-muted-foreground" />
            <CardTitle className="text-xl">Subscription Required</CardTitle>
          </div>
          <CardDescription>
            Your subscription has expired. Please update to continue.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Button 
            onClick={handleUpgrade}
            disabled={loading}
            className="w-full"
          >
            {loading ? (
              <div className="flex items-center gap-2">
                <div className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin" />
                <span>Opening Portal...</span>
              </div>
            ) : (
              'Update Subscription'
            )}
          </Button>
        </CardContent>
      </Card>
    </div>
  );
} 