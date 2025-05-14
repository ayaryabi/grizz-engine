"use client"; // Mark this component as a Client Component

import React from 'react';
// import { ThemeToggle } from '@/components/ui/ThemeToggle'; // Removed ThemeToggle import
import { UserNav } from '@/components/navigation/UserNav';
import { Brain } from 'lucide-react';

export default function Navbar() {
  return (
    <nav className="flex items-center justify-between h-16 px-4 border-b sm:px-6 lg:px-8 bg-background border-border">
      <div className="flex items-center">
        {/* <Link href="/"> Optional: Make Grizz logo a link to home */}
        <span className="font-semibold text-lg text-foreground">Grizz</span>
        {/* </Link> */}
        {/* Brain icon moved to the right */}
      </div>
      <div className="flex items-center gap-x-3 sm:gap-x-4"> {/* Adjusted gap slightly if needed */}
        <button 
          onClick={() => console.log('Brain icon clicked - navigate to Bytes page later')}
          className="p-1.5 rounded-md hover:bg-muted focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 cursor-pointer"
          aria-label="Go to Bytes"
        >
          <Brain className="h-5 w-5 text-foreground" />
        </button>
        {/* <ThemeToggle /> ThemeToggle is now part of UserNav */}
        <UserNav />
      </div>
    </nav>
  );
} 