import React from 'react';
import Navbar from '@/components/navigation/Navbar';

interface MainAppLayoutProps {
  children: React.ReactNode;
}

export default function MainAppLayout({ children }: MainAppLayoutProps) {
  return (
    <div className="flex flex-col h-screen bg-background text-foreground">
      <Navbar />

      <main className="flex-grow overflow-y-auto pt-16 sm:pt-20">
        {children}
      </main>
    </div>
  );
} 