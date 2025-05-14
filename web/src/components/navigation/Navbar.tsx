import React from 'react';
import { ThemeToggle } from '@/components/ui/ThemeToggle';

export default function Navbar() {
  return (
    <nav className="flex items-center justify-between h-16 px-4 border-b sm:px-6 lg:px-8 bg-background border-border">
      <div>
        <span className="font-semibold text-lg text-foreground">Grizz</span>
        {/* Logo could go here */}
      </div>
      <div className="flex items-center gap-x-2 sm:gap-x-4">
        {/* Other nav items like Brain icon can go here */}
        <ThemeToggle />
        {/* User avatar/menu can go here */}
      </div>
    </nav>
  );
} 