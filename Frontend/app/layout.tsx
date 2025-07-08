import type { Metadata } from "next"
import { Inter } from "next/font/google"
import "./globals.css"

const inter = Inter({ 
  subsets: ["latin"],
  variable: "--font-inter",
})

export const metadata: Metadata = {
  title: "ResumeWise - AI Resume Critic",
  description: "Get professional feedback on your resume with AI-powered analysis",
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className={`${inter.variable} min-h-screen bg-[var(--background)] text-[var(--foreground)] antialiased`}>
        {/* Modern sticky header */}
        <header className="sticky-header">
          <div className="container-modern">
            <div className="flex items-center justify-between h-16">
              <div className="flex items-center space-x-3">
                <div className="w-8 h-8 bg-gradient-to-br from-blue-600 to-emerald-500 rounded-lg flex items-center justify-center">
                  <span className="text-white font-bold text-sm">R</span>
                </div>
                <h1 className="text-xl font-bold text-gradient">ResumeWise</h1>
              </div>
              <div className="flex items-center space-x-4">
                <span className="text-sm text-slate-600">
                  AI-Powered Resume Analysis
                </span>
              </div>
            </div>
          </div>
        </header>

        {/* Main content with modern spacing */}
        <main className="min-h-[calc(100vh-4rem)] flex flex-col">
          <div className="flex-1 container-modern section-spacing">
            {children}
          </div>
        </main>

        {/* Modern footer */}
        <footer className="bg-white border-t border-[var(--border)]">
          <div className="container-modern py-8">
            <div className="flex flex-col sm:flex-row items-center justify-between space-y-4 sm:space-y-0">
              <div className="flex items-center space-x-2">
                <div className="w-6 h-6 bg-gradient-to-br from-blue-600 to-emerald-500 rounded-md flex items-center justify-center">
                  <span className="text-white font-bold text-xs">R</span>
                </div>
              </div>
              <div className="flex items-center space-x-6 text-sm text-slate-400 select-none">
                <span>Privacy</span>
                <span>Terms</span>
                <span>Support</span>
              </div>
            </div>
          </div>
        </footer>
      </body>
    </html>
  )
}
