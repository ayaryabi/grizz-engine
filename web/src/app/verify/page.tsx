import { Suspense } from 'react';
import { MagicLinkForm } from '@/features/auth/MagicLinkForm';

export default function VerifyPage() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-gray-100 dark:bg-gray-950 p-4">
      <Suspense fallback={<div>Loading...</div>}>
        <MagicLinkForm />
      </Suspense>
    </div>
  );
} 