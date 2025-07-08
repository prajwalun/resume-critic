"use client"
import { ThemeProvider as NextThemesProvider } from "next-themes"
import type { ThemeProviderProps } from "next-themes"
import { useEffect, useState } from 'react';
import { Moon, Sun } from 'lucide-react';

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
        className="btn-ghost p-2 rounded-xl hover:bg-slate-100 dark:hover:bg-slate-800 transition-all duration-200"
      >
        {theme === 'dark' ? (
          <Sun className="w-5 h-5 text-amber-500" />
        ) : (
          <Moon className="w-5 h-5 text-slate-600" />
        )}
      </button>
      <NextThemesProvider {...props}>{children}</NextThemesProvider>
    </>
  );
}
