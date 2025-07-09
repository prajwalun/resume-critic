import type React from "react"
import type { Metadata } from "next"
import { Inter } from "next/font/google"
import "./globals.css"

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
})

export const metadata: Metadata = {
  title: "ResumeWise - AI Resume Analysis",
  description: "Transform your resume with AI-powered analysis and optimization",
    generator: 'v0.dev'
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className="dark">
      <body
        className={`${inter.variable} font-sans antialiased`}
        style={{ backgroundColor: "#121212", color: "#EAEAEA" }}
      >
        {children}
      </body>
    </html>
  )
}
