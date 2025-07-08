import type React from "react"
import type { Metadata } from "next"
import { Inter } from "next/font/google"
import "./globals.css"
import { ThemeProvider } from "@/components/theme-provider"
import '../app/globals.css';

const inter = Inter({ subsets: ["latin"] })

export const metadata: Metadata = {
  title: "ResumeWise - AI Resume Critic",
  description: "Get professional feedback on your resume with AI-powered analysis",
    generator: 'v0.dev'
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={`${inter.className} min-h-screen bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100`}>
        <ThemeProvider attribute="class" defaultTheme="system" enableSystem disableTransitionOnChange>
          <div className="sticky-topbar w-full flex items-center justify-between px-8 py-4 relative">
            <span className="text-2xl font-bold tracking-tight text-emerald-600 dark:text-emerald-400">ResumeWise</span>
            {/* Dark mode toggle is now inside ThemeProvider and appears on the right */}
          </div>
          <main className="flex flex-col items-center justify-center min-h-[calc(100vh-64px)] px-4">
            <div className="resume-card w-full max-w-3xl">
              {children}
            </div>
          </main>
        </ThemeProvider>
      </body>
    </html>
  )
}
