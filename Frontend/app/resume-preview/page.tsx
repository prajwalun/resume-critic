"use client"

import React from "react"
import { useRouter } from "next/navigation"
import { Download, ArrowLeft, FileText, CheckCircle, Sparkles, Target, Shield, Loader2 } from "lucide-react"
import { Button } from "@/components/ui/button"
import type { JSX } from "react"

// Utility to decode base64 to string
function decodeBase64(str: string) {
  try {
    return decodeURIComponent(escape(window.atob(str)))
  } catch {
    return ""
  }
}

// Utility to trigger TXT download
function downloadTxt(filename: string, text: string) {
  const element = document.createElement("a")
  const file = new Blob([text], { type: "text/plain" })
  element.href = URL.createObjectURL(file)
  element.download = filename
  document.body.appendChild(element)
  element.click()
  document.body.removeChild(element)
}

// Utility to clean up markdown: remove duplicate headings, fix structure, and convert bullets
export function cleanResumeMarkdown(md: string) {
  // Remove any subheading (###) that immediately follows a section heading (##) with the same text
  md = md.replace(/(##+ .+)\n(### .+)\n/g, (match, h2, h3) => {
    if (h2.replace(/#+ /, "") === h3.replace(/#+ /, "")) return h2 + "\n"
    return match
  })
  // Remove all but the first occurrence of each section heading (e.g., '## Technical Skills')
  const seen = new Set<string>()
  md = md
    .split("\n")
    .filter((line) => {
      const headingMatch = line.match(/^(#+) (.+)$/)
      if (headingMatch) {
        const key = headingMatch[2].trim().toLowerCase()
        if (seen.has(key)) return false
        seen.add(key)
      }
      return true
    })
    .join("\n")
  // Group lines starting with '-' or '*' into proper Markdown lists, ensuring blank lines before/after
  md = md.replace(/((?:^[-*] .+(?:\n|$))+)/gm, (block) => {
    // Ensure blank line before and after
    return "\n" + block.trim() + "\n"
  })
  // Add extra blank lines before section headings for spacing
  md = md.replace(/(#+ .+)/g, "\n$1")
  // Remove extra blank lines at the start
  md = md.replace(/^\s+/, "")
  return md
}

// Add a new utility to further clean and format resume markdown for display
function formatResumeMarkdown(md: string) {
  // Remove duplicate subheadings within a section
  md = md.replace(/(Relevant Coursework:)([\s\S]*?)(?=Relevant Coursework:|$)/g, (block: string) => {
    // Only keep the first 'Relevant Coursework:' per section
    const lines = block.split("\n")
    const seen = new Set()
    return lines
      .filter((line: string) => {
        if (/^Relevant Coursework:/i.test(line)) {
          if (seen.has("rc")) return false
          seen.add("rc")
        }
        return true
      })
      .join("\n")
  })
  // Bulletize comma-separated lists
  md = md.replace(
    /(Relevant Coursework:|Skills:|Technologies:|Tools:|Languages:|Achievements:|Responsibilities:)[ \t]*\n?([^-\n][^\n]*)/gi,
    (match: string, heading: string, items: string) => {
      if (!items) return match
      const bullets = items
        .split(/,|•|\u2022/)
        .map((s: string) => s.trim())
        .filter(Boolean)
      if (bullets.length > 1) {
        return `${heading}\n` + bullets.map((b: string) => `- ${b}`).join("\n")
      }
      return match
    },
  )
  // Bulletize any line with multiple comma-separated items (not already a list)
  md = md.replace(/^(?![-*] )([^\n]+,[^\n]+)$/gm, (line: string) => {
    const items = line
      .split(/,|•|\u2022/)
      .map((s: string) => s.trim())
      .filter(Boolean)
    if (items.length > 1) {
      return items.map((b: string) => `- ${b}`).join("\n")
    }
    return line
  })
  // Remove extra blank lines
  md = md.replace(/\n{3,}/g, "\n\n")
  return md
}

function parseSection(section: string) {
  const lines = section.trim().split(/\n+/)
  const heading = lines[0]?.replace(/^#+\s*/, "").trim()
  const content = lines.slice(1).join("\n").trim()
  return { heading, content }
}

// Add a new formatter for section-aware resume rendering
export function formatResumeSections(sections: string[]): JSX.Element[] {
  return sections
    .map((section, i) => {
      const { heading, content } = parseSection(section)
      if (!heading) return null
      // Skills: comma-separated
      if (/skills|technologies|tools|languages|certifications/i.test(heading)) {
        const items = content
          .split(/[,•\-\n]+/)
          .map((s) => s.trim())
          .filter(Boolean)
        return (
          <section key={i} className="resume-section mb-10">
            <h2 className="resume-heading text-2xl font-bold mb-4 tracking-tight" style={{ color: "#F8FAFC" }}>
              {heading}
            </h2>
            <div className="leading-relaxed font-normal" style={{ color: "#94A3B8" }}>
              {items.join(", ")}
            </div>
          </section>
        )
      }
      // Projects: Title, tech/tools, bullets
      if (/projects?/i.test(heading)) {
        // Split by double newlines or project markers
        const entries = content
          .split(/\n{2,}|(?=^[A-Z][^\n]+\|[^\n]+|\*\*.+\*\*)/gm)
          .map((e) => e.trim())
          .filter(Boolean)
        return (
          <section key={i} className="resume-section mb-10">
            <h2 className="resume-heading text-2xl font-bold mb-4 tracking-tight" style={{ color: "#F8FAFC" }}>
              {heading}
            </h2>
            <div className="space-y-8">
              {entries.map((entry, idx) => {
                // Try to split title/tools/details
                const [firstLine, ...rest] = entry.split("\n")
                let title = firstLine,
                  tech = "",
                  details = rest.join("\n").trim()
                // If firstLine contains |, treat as Title | Tech
                if (/\|/.test(firstLine)) {
                  const parts = firstLine.split("|").map((s) => s.trim())
                  title = parts[0]
                  tech = parts.slice(1).join(" | ")
                }
                // Bulletize details
                let bullets = details
                  .split(/\n|(?<!\d), /)
                  .map((s) => s.trim())
                  .filter(Boolean)
                // Remove bullets that are just tech/tools
                bullets = bullets.filter((b) => b && b !== tech && b !== title)
                return (
                  <div key={idx} className="mb-4">
                    <div className="font-bold text-lg mb-1" style={{ color: "#F8FAFC" }}>
                      {title}
                    </div>
                    {tech && (
                      <div className="text-sm mb-1 italic" style={{ color: "#64748B" }}>
                        {tech}
                      </div>
                    )}
                    {bullets.length > 0 && (
                      <ul className="list-disc ml-6 space-y-1">
                        {bullets.map((b, j) => (
                          <li key={j} className="leading-relaxed font-normal" style={{ color: "#94A3B8" }}>
                            {b}
                          </li>
                        ))}
                      </ul>
                    )}
                  </div>
                )
              })}
            </div>
          </section>
        )
      }
      // Experience: Job Title | Company | Date, bullets
      if (/experience/i.test(heading)) {
        const entries = content
          .split(/\n{2,}|(?=^[A-Z][^\n]+\|[^\n]+|\*\*.+\*\*)/gm)
          .map((e) => e.trim())
          .filter(Boolean)
        return (
          <section key={i} className="resume-section mb-10">
            <h2 className="resume-heading text-2xl font-bold mb-4 tracking-tight" style={{ color: "#F8FAFC" }}>
              {heading}
            </h2>
            <div className="space-y-8">
              {entries.map((entry, idx) => {
                const [firstLine, ...rest] = entry.split("\n")
                let title = firstLine,
                  meta = "",
                  details = rest.join("\n").trim()
                // Try to extract Job Title | Company | Date
                if (/\|/.test(firstLine)) {
                  const parts = firstLine.split("|").map((s) => s.trim())
                  title = parts.slice(0, -1).join(" | ")
                  meta = parts[parts.length - 1]
                }
                // Bulletize details
                let bullets = details
                  .split(/\n|(?<!\d), /)
                  .map((s) => s.trim())
                  .filter(Boolean)
                bullets = bullets.filter((b) => b && b !== meta && b !== title)
                return (
                  <div key={idx} className="mb-4">
                    <div className="font-bold text-lg mb-1" style={{ color: "#F8FAFC" }}>
                      {title}
                    </div>
                    {meta && (
                      <div className="text-sm mb-1" style={{ color: "#64748B" }}>
                        {meta}
                      </div>
                    )}
                    {bullets.length > 0 && (
                      <ul className="list-disc ml-6 space-y-1">
                        {bullets.map((b, j) => (
                          <li key={j} className="leading-relaxed font-normal" style={{ color: "#94A3B8" }}>
                            {b}
                          </li>
                        ))}
                      </ul>
                    )}
                  </div>
                )
              })}
            </div>
          </section>
        )
      }
      // Education: Degree | Institution | Date, optional GPA/honors
      if (/education/i.test(heading)) {
        const entries = content
          .split(/\n{2,}|(?=^[A-Z][^\n]+\|[^\n]+|\*\*.+\*\*)/gm)
          .map((e) => e.trim())
          .filter(Boolean)
        return (
          <section key={i} className="resume-section mb-10">
            <h2 className="resume-heading text-2xl font-bold mb-4 tracking-tight" style={{ color: "#F8FAFC" }}>
              {heading}
            </h2>
            <div className="space-y-8">
              {entries.map((entry, idx) => {
                const [firstLine, ...rest] = entry.split("\n")
                let degree = firstLine,
                  meta = "",
                  details = rest.join("\n").trim()
                // Try to extract Degree | Institution | Date
                if (/\|/.test(firstLine)) {
                  const parts = firstLine.split("|").map((s) => s.trim())
                  degree = parts.slice(0, -1).join(" | ")
                  meta = parts[parts.length - 1]
                }
                // GPA/honors
                let extras = details
                  .split(/\n|, /)
                  .map((s) => s.trim())
                  .filter(Boolean)
                extras = extras.filter((e) => e && e !== meta && e !== degree)
                return (
                  <div key={idx} className="mb-4">
                    <div className="font-bold text-lg mb-1" style={{ color: "#F8FAFC" }}>
                      {degree}
                    </div>
                    {meta && (
                      <div className="text-sm mb-1" style={{ color: "#64748B" }}>
                        {meta}
                      </div>
                    )}
                    {extras.length > 0 && (
                      <div className="text-sm mt-1" style={{ color: "#94A3B8" }}>
                        {extras.join(" | ")}
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
          </section>
        )
      }
      // Default: paragraph
      return (
        <section key={i} className="resume-section mb-10">
          <h2 className="resume-heading text-2xl font-bold mb-4 tracking-tight" style={{ color: "#F8FAFC" }}>
            {heading}
          </h2>
          <div className="leading-relaxed font-normal whitespace-pre-line" style={{ color: "#94A3B8" }}>
            {content}
          </div>
        </section>
      )
    })
    .filter(Boolean) as JSX.Element[]
}

// Utility to fetch the final resume from the backend
async function fetchFinalResume(analysisId: string): Promise<string> {
  // Try the new backend endpoint
  const res = await fetch(`/api/final-resume/${encodeURIComponent(analysisId)}`)
  if (!res.ok) throw new Error("Failed to fetch final resume")
  const data = await res.json()
  return data.final_resume || data.data?.final_resume || ""
}

export default function ResumePreview() {
  const router = useRouter()
  const [sessionData, setSessionData] = React.useState<any>(null)
  const [loading, setLoading] = React.useState(true)
  const [error, setError] = React.useState<string | null>(null)

  React.useEffect(() => {
    try {
      // Get structured session data from storage
      const storedData = window.sessionStorage.getItem("analysis_session_data")
      if (storedData) {
        const parsed = JSON.parse(storedData)
        setSessionData(parsed)
      } else {
        // Fallback to legacy data
        const legacyResume = window.sessionStorage.getItem("last_final_resume")
        if (legacyResume) {
          setSessionData({ finalResume: legacyResume, sections: {}, sectionAnalyses: {} })
        } else {
          setError("No analysis data found. Please run an analysis first.")
        }
      }
    } catch (e) {
      console.error("Error loading session data:", e)
      setError("Failed to load analysis data.")
    } finally {
      setLoading(false)
    }
  }, [])

  const renderSectionContent = (sectionType: string, section: any, analysis: any, isAccepted: boolean) => {
    // Determine what content to show
    let content = ""
    let isImproved = false

    if (isAccepted && analysis?.improved_content) {
      // Show improved content if changes were accepted
      content = analysis.improved_content
      isImproved = true
    } else if (analysis?.original_content) {
      // Show original content from analysis
      content = analysis.original_content
    } else if (section?.content) {
      // Fallback to section content
      content = section.content
    } else {
      // No content available
      return null
    }

    // Section-specific formatting
    if (sectionType === 'skills') {
      const skills = content.split(/[,\n•\-]+/).map(s => s.trim()).filter(Boolean)
      return (
        <div className="space-y-2">
          <p className="text-slate-300 leading-relaxed">
            {skills.join(" • ")}
          </p>
          {isImproved && (
            <div className="inline-flex items-center gap-1 px-2 py-1 bg-emerald-500/20 text-emerald-300 text-xs rounded-full">
              <CheckCircle className="w-3 h-3" />
              AI Enhanced
            </div>
          )}
        </div>
      )
    }
    
    if (sectionType === 'projects') {
      const projects = content.split(/\n\s*\n/).filter(p => p.trim())
      return (
        <div className="space-y-6">
          {projects.map((project, idx) => {
            const lines = project.trim().split('\n')
            const titleLine = lines[0]
            const details = lines.slice(1).join('\n')
            
            // Extract title and tech from first line if formatted as "Title | Tech"
            let title = titleLine
            let tech = ""
            if (titleLine.includes('|')) {
              const parts = titleLine.split('|').map(p => p.trim())
              title = parts[0]
              tech = parts.slice(1).join(' | ')
            }
            
            return (
              <div key={idx} className="border-l-2 border-blue-400/30 pl-4">
                <h4 className="text-lg font-semibold text-white mb-1">{title}</h4>
                {tech && (
                  <p className="text-blue-300 text-sm mb-2 font-medium">{tech}</p>
                )}
                <div className="text-slate-300 leading-relaxed space-y-1">
                  {details.split('\n').map((line, i) => {
                    const cleanLine = line.trim().replace(/^[•\-\*]\s*/, '')
                    return cleanLine ? (
                      <div key={i} className="flex items-start gap-2">
                        <div className="w-1 h-1 bg-slate-400 rounded-full mt-2 flex-shrink-0" />
                        <span>{cleanLine}</span>
                      </div>
                    ) : null
                  })}
                </div>
              </div>
            )
          })}
          {isImproved && (
            <div className="inline-flex items-center gap-1 px-2 py-1 bg-emerald-500/20 text-emerald-300 text-xs rounded-full">
              <CheckCircle className="w-3 h-3" />
              AI Enhanced
            </div>
          )}
        </div>
      )
    }
    
    if (sectionType === 'experience') {
      const experiences = content.split(/\n\s*\n/).filter(e => e.trim())
      return (
        <div className="space-y-6">
          {experiences.map((exp, idx) => {
            const lines = exp.trim().split('\n')
            const titleLine = lines[0]
            const details = lines.slice(1).join('\n')
            
            return (
              <div key={idx} className="border-l-2 border-purple-400/30 pl-4">
                <h4 className="text-lg font-semibold text-white mb-2">{titleLine}</h4>
                <div className="text-slate-300 leading-relaxed space-y-1">
                  {details.split('\n').map((line, i) => {
                    const cleanLine = line.trim().replace(/^[•\-\*]\s*/, '')
                    return cleanLine ? (
                      <div key={i} className="flex items-start gap-2">
                        <div className="w-1 h-1 bg-slate-400 rounded-full mt-2 flex-shrink-0" />
                        <span>{cleanLine}</span>
                      </div>
                    ) : null
                  })}
                </div>
              </div>
            )
          })}
          {isImproved && (
            <div className="inline-flex items-center gap-1 px-2 py-1 bg-emerald-500/20 text-emerald-300 text-xs rounded-full">
              <CheckCircle className="w-3 h-3" />
              AI Enhanced
            </div>
          )}
        </div>
      )
    }
    
    // Default formatting for other sections
    return (
      <div className="space-y-2">
        <div className="text-slate-300 leading-relaxed whitespace-pre-line">
          {content}
        </div>
        {isImproved && (
          <div className="inline-flex items-center gap-1 px-2 py-1 bg-emerald-500/20 text-emerald-300 text-xs rounded-full">
            <CheckCircle className="w-3 h-3" />
            AI Enhanced
          </div>
        )}
      </div>
    )
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 to-slate-800 flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="w-8 h-8 mx-auto mb-4 animate-spin text-blue-400" />
          <p className="text-white/70">Loading your resume...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 to-slate-800">
        <div className="flex items-center justify-center min-h-[60vh]">
          <div className="text-center max-w-md mx-auto px-6">
            <div className="w-16 h-16 rounded-2xl flex items-center justify-center mx-auto mb-6 bg-gradient-to-r from-red-500 to-red-600">
              <FileText className="w-8 h-8 text-white" />
            </div>
            <h2 className="text-2xl font-semibold mb-4 text-white">Resume Not Found</h2>
            <p className="mb-8 text-slate-400">{error}</p>
            <Button
              onClick={() => router.push("/")}
              className="px-8 py-3 rounded-xl font-semibold bg-gradient-to-r from-blue-500 to-blue-600 text-white border-none"
            >
              <ArrowLeft className="w-4 h-4 mr-2" />
              Start New Analysis
            </Button>
          </div>
        </div>
      </div>
    )
  }

  const { sections, sectionAnalyses, acceptedChanges, analysisOrder } = sessionData

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 to-slate-800">
      {/* Header */}
      <div className="border-b border-white/10 bg-black/20 backdrop-blur-xl">
        <div className="max-w-4xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-gradient-to-r from-blue-500 to-purple-600 rounded-xl flex items-center justify-center">
                <span className="text-white font-bold text-lg">RW</span>
              </div>
              <div>
                <h1 className="text-xl font-bold text-white">Resume Preview</h1>
                <p className="text-white/60 text-sm">Professional optimization complete</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <Button
                onClick={() => {
                  const resumeText = sessionData.finalResume || "Resume content not available"
                  downloadTxt("resume.txt", resumeText)
                }}
                className="bg-emerald-600 hover:bg-emerald-700 text-white"
              >
                <Download className="w-4 h-4 mr-2" />
                Download Resume
              </Button>
              <Button
                onClick={() => router.push("/")}
                variant="outline"
                className="border-white/20 text-white/80 hover:bg-white/10"
              >
                <ArrowLeft className="w-4 h-4 mr-2" />
                New Analysis
              </Button>
            </div>
          </div>
        </div>
      </div>

      {/* Resume Content */}
      <div className="max-w-4xl mx-auto px-6 py-12">
        <div className="bg-white/5 backdrop-blur-xl rounded-3xl border border-white/10 shadow-2xl overflow-hidden">
          <div className="p-12">
            {/* Section-by-Section Rendering */}
            <div className="space-y-12">
              {analysisOrder && analysisOrder.length > 0 ? (
                analysisOrder.map((sectionType: string) => {
                  const section = sections?.[sectionType]
                  const analysis = sectionAnalyses?.[sectionType]
                  const isAccepted = acceptedChanges?.[sectionType]
                  
                  const sectionContent = renderSectionContent(sectionType, section, analysis, isAccepted)
                  
                  if (!sectionContent) return null
                  
                  return (
                    <section key={sectionType} className="resume-section">
                      <h2 className="text-2xl font-bold text-white mb-6 pb-2 border-b border-white/20">
                        {sectionType.charAt(0).toUpperCase() + sectionType.slice(1).replace('_', ' ')}
                      </h2>
                      {sectionContent}
                    </section>
                  )
                })
              ) : (
                // Fallback to raw resume text if no structured data
                <div className="space-y-6">
                  <h2 className="text-2xl font-bold text-white mb-6">Professional Resume</h2>
                  <div className="text-slate-300 leading-relaxed whitespace-pre-line">
                    {sessionData.finalResume || "Resume content not available"}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
} 