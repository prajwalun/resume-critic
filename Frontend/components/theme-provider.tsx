"use client"
import { ThemeProvider as NextThemesProvider } from "next-themes"
import type { ThemeProviderProps } from "next-themes"
import { useEffect, useState } from 'react';

export function ThemeProvider({ children, ...props }: ThemeProviderProps) {
  const [theme, setTheme] = useState('light');

  useEffect(() => {
    if (typeof window !== 'undefined') {
      const stored = localStorage.getItem('theme');
      if (stored) setTheme(stored);
      document.documentElement.classList.toggle('dark', stored === 'dark');
    }
  }, []);

  const toggleTheme = () => {
    const newTheme = theme === 'dark' ? 'light' : 'dark';
    setTheme(newTheme);
    localStorage.setItem('theme', newTheme);
    document.documentElement.classList.toggle('dark', newTheme === 'dark');
  };

  return (
    <>
      <button
        aria-label="Toggle dark mode"
        onClick={toggleTheme}
        className="absolute right-8 top-4 bg-emerald-600 hover:bg-emerald-700 text-white rounded-full font-semibold px-4 py-2 text-sm shadow-lg transition-all duration-200"
      >
        {theme === 'dark' ? '🌙 Dark' : '☀️ Light'}
      </button>
      <NextThemesProvider {...props}>{children}</NextThemesProvider>
    </>
  );
}
