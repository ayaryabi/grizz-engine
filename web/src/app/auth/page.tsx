import { MagicLinkForm } from '@/features/auth/MagicLinkForm'; // Adjust import path based on alias setup

export default function AuthPage() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-gray-100 dark:bg-gray-950 p-4">
      <MagicLinkForm />
    </div>
  );
} 