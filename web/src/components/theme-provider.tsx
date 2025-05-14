"use client";

import * as React from "react";
import { ThemeProvider as NextThemesProvider } from "next-themes";
// Use React.ComponentProps for more robust type inference for the provider's props
// import type { ThemeProviderProps } from "next-themes/dist/types"; 

export function ThemeProvider({
  children,
  ...props
}: React.ComponentProps<typeof NextThemesProvider>) { // Use React.ComponentProps
  return <NextThemesProvider {...props}>{children}</NextThemesProvider>;
} 