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

// Parse the backend's formatted resume sections
function parseFinalResume(finalResumeText: string): Array<{ title: string, content: string }> {
  if (!finalResumeText) return []
  
  // Split by section headers like "=== SKILLS ===" 
  const sections = finalResumeText.split(/(?=^=== .+ ===)/m).filter(s => s.trim())
  
  return sections.map(section => {
    const lines = section.trim().split('\n')
    const headerLine = lines[0]
    
    // Extract title from "=== TITLE ===" format
    const titleMatch = headerLine.match(/^=== (.+) ===$/)
    const title = titleMatch ? titleMatch[1] : 'Unknown Section'
    
    // Get content (everything after the header)
    const content = lines.slice(1).join('\n').trim()
    
    return { title, content }
  })
}

// Format individual sections for display
function formatSectionContent(title: string, content: string): JSX.Element {
  const sectionType = title.toLowerCase().replace(/\s+/g, '_')
  
  // Contact Info section - format contact details
  if (sectionType.includes('contact')) {
    const lines = content.split('\n').filter(line => line.trim())
    
    return (
      <div className="space-y-2">
        {lines.map((line, idx) => (
          <p key={idx} className="text-slate-300 text-lg leading-relaxed">
            {line.trim()}
          </p>
        ))}
      </div>
    )
  }
  
  // Summary section - format as professional paragraph
  if (sectionType.includes('summary') || sectionType.includes('objective')) {
    return (
      <div className="space-y-3">
        {content.split('\n\n').filter(para => para.trim()).map((paragraph, idx) => (
          <p key={idx} className="text-slate-300 leading-relaxed text-justify">
            {paragraph.trim()}
          </p>
        ))}
      </div>
    )
  }
  
  // Skills section - display as clean, professional list
  if (sectionType.includes('skills') || sectionType.includes('technical')) {
    const lines = content.split('\n').filter(line => line.trim())
    
    return (
      <div className="space-y-4">
        {lines.map((line, idx) => {
          // Check if line has category format (e.g., "Languages: Python, JavaScript")
          if (line.includes(':')) {
            const [category, items] = line.split(':', 2)
            const skillItems = items.split(/[,•·\|]/).map(s => s.trim()).filter(Boolean)
            
            return (
              <div key={idx} className="mb-4">
                <h4 className="text-lg font-semibold text-white mb-2">{category.trim()}</h4>
                <div className="flex flex-wrap gap-2">
                  {skillItems.map((skill, skillIdx) => (
                    <span 
                      key={skillIdx} 
                      className="px-3 py-1 bg-slate-700/50 text-slate-200 rounded-md text-sm border border-slate-600/30"
                    >
                      {skill}
                    </span>
                  ))}
                </div>
              </div>
            )
          } else {
            // Handle single line or uncategorized skills
            const skillItems = line.split(/[,•·\|]/).map(s => s.trim()).filter(Boolean)
            
            if (skillItems.length > 1) {
              return (
                <div key={idx} className="flex flex-wrap gap-2">
                  {skillItems.map((skill, skillIdx) => (
                    <span 
                      key={skillIdx} 
                      className="px-3 py-1 bg-slate-700/50 text-slate-200 rounded-md text-sm border border-slate-600/30"
                    >
                      {skill}
                    </span>
                  ))}
                </div>
              )
            } else {
              return (
                <p key={idx} className="text-slate-300 leading-relaxed">
                  {line}
                </p>
              )
            }
          }
        })}
      </div>
    )
  }
  
  // Experience section - parse job entries with enhanced formatting
  if (sectionType.includes('experience')) {
    const experiences = content.split(/\n\s*\n/).filter(e => e.trim())
    
    return (
      <div className="space-y-8">
        {experiences.map((exp, idx) => {
          const lines = exp.trim().split('\n')
          const titleLine = lines[0]
          const details = lines.slice(1).filter(line => line.trim())
          
          // Try to parse company, role, and dates from title line
          let company = titleLine
          let role = ""
          let dates = ""
          
          // Look for patterns like "Software Engineer at Google (2020-2023)"
          const companyRoleMatch = titleLine.match(/^(.+?)\s+at\s+(.+?)(\s*\(.*\))?$/)
          if (companyRoleMatch) {
            role = companyRoleMatch[1].trim()
            company = companyRoleMatch[2].trim()
            dates = companyRoleMatch[3] ? companyRoleMatch[3].replace(/[()]/g, '').trim() : ""
          } else {
            // Look for patterns like "Google - Software Engineer (2020-2023)"
            const dashMatch = titleLine.match(/^(.+?)\s*[-–]\s*(.+?)(\s*\(.*\))?$/)
            if (dashMatch) {
              company = dashMatch[1].trim()
              role = dashMatch[2].trim()
              dates = dashMatch[3] ? dashMatch[3].replace(/[()]/g, '').trim() : ""
            }
          }
          
          return (
            <div key={idx} className="border-l-3 border-purple-400/40 pl-6 relative">
              <div className="absolute -left-2 top-0 w-4 h-4 bg-purple-400/20 rounded-full border-2 border-purple-400/40"></div>
              
              <div className="mb-3">
                {role && company ? (
                  <>
                    <h4 className="text-xl font-bold text-white mb-1">{role}</h4>
                    <p className="text-purple-300 font-medium text-lg">{company}</p>
                    {dates && <p className="text-slate-400 text-sm mt-1">{dates}</p>}
                  </>
                ) : (
                  <h4 className="text-xl font-bold text-white mb-2">{titleLine}</h4>
                )}
              </div>
              
              <div className="text-slate-300 leading-relaxed space-y-2">
                {details.map((line, i) => {
                  const cleanLine = line.trim().replace(/^[•\-\*]\s*/, '')
                  return cleanLine ? (
                    <div key={i} className="flex items-start gap-3">
                      <div className="w-1.5 h-1.5 bg-purple-400/60 rounded-full mt-2 flex-shrink-0" />
                      <span className="text-sm leading-relaxed">{cleanLine}</span>
                    </div>
                  ) : null
                })}
              </div>
            </div>
          )
        })}
      </div>
    )
  }
  
  // Projects section - parse project entries with enhanced formatting
  if (sectionType.includes('projects')) {
    const projects = content.split(/\n\s*\n/).filter(p => p.trim())
    
    return (
      <div className="space-y-8">
        {projects.map((project, idx) => {
          const lines = project.trim().split('\n')
          const titleLine = lines[0]
          const details = lines.slice(1).filter(line => line.trim())
          
          // Extract title, tech, and dates from various formats
          let title = titleLine
          let tech = ""
          let dates = ""
          
          // Look for patterns like "Project Name | React, Node.js | 2023"
          if (titleLine.includes('|')) {
            const parts = titleLine.split('|').map(p => p.trim())
            title = parts[0]
            if (parts.length > 1) {
              // Check if last part looks like a date
              const lastPart = parts[parts.length - 1]
              if (/\d{4}/.test(lastPart)) {
                dates = lastPart
                tech = parts.slice(1, -1).join(', ')
              } else {
                tech = parts.slice(1).join(', ')
              }
            }
          } else {
            // Look for patterns like "Project Name (React, Node.js)"
            const techMatch = titleLine.match(/^(.+?)\s*\((.+?)\)$/)
            if (techMatch) {
              title = techMatch[1].trim()
              tech = techMatch[2].trim()
            }
          }
          
          return (
            <div key={idx} className="border-l-3 border-blue-400/40 pl-6 relative">
              <div className="absolute -left-2 top-0 w-4 h-4 bg-blue-400/20 rounded-full border-2 border-blue-400/40"></div>
              
              <div className="mb-3">
                <h4 className="text-xl font-bold text-white mb-2">{title}</h4>
                {tech && (
                  <div className="flex flex-wrap gap-2 mb-2">
                    {tech.split(/[,•·\|]/).map((t, techIdx) => (
                      <span 
                        key={techIdx} 
                        className="px-2 py-1 bg-blue-500/20 text-blue-300 rounded text-xs border border-blue-500/30"
                      >
                        {t.trim()}
                      </span>
                    ))}
                  </div>
                )}
                {dates && <p className="text-slate-400 text-sm">{dates}</p>}
              </div>
              
              <div className="text-slate-300 leading-relaxed space-y-2">
                {details.map((line, i) => {
                  const cleanLine = line.trim().replace(/^[•\-\*]\s*/, '')
                  return cleanLine ? (
                    <div key={i} className="flex items-start gap-3">
                      <div className="w-1.5 h-1.5 bg-blue-400/60 rounded-full mt-2 flex-shrink-0" />
                      <span className="text-sm leading-relaxed">{cleanLine}</span>
                    </div>
                  ) : null
                })}
              </div>
            </div>
          )
        })}
      </div>
    )
  }
  
  // Education section - parse education entries with enhanced formatting
  if (sectionType.includes('education')) {
    const educationEntries = content.split(/\n\s*\n/).filter(e => e.trim())
    
    return (
      <div className="space-y-8">
        {educationEntries.map((entry, idx) => {
          const lines = entry.trim().split('\n')
          const titleLine = lines[0]
          const details = lines.slice(1).filter(line => line.trim())
          
          // Try to parse degree, institution, and dates
          let degree = titleLine
          let institution = ""
          let dates = ""
          let gpa = ""
          
          // Look for patterns like "Bachelor of Science in Computer Science, MIT (2020-2024)"
          const degreeMatch = titleLine.match(/^(.+?),\s*(.+?)(\s*\(.*\))?$/)
          if (degreeMatch) {
            degree = degreeMatch[1].trim()
            institution = degreeMatch[2].trim()
            dates = degreeMatch[3] ? degreeMatch[3].replace(/[()]/g, '').trim() : ""
          } else {
            // Look for patterns like "MIT - Bachelor of Science (2020-2024)"
            const institutionMatch = titleLine.match(/^(.+?)\s*[-–]\s*(.+?)(\s*\(.*\))?$/)
            if (institutionMatch) {
              institution = institutionMatch[1].trim()
              degree = institutionMatch[2].trim()
              dates = institutionMatch[3] ? institutionMatch[3].replace(/[()]/g, '').trim() : ""
            }
          }
          
          // Look for GPA in details
          const gpaDetail = details.find(line => line.toLowerCase().includes('gpa'))
          if (gpaDetail) {
            const gpaMatch = gpaDetail.match(/gpa[:\s]*([0-9.]+)/i)
            if (gpaMatch) {
              gpa = gpaMatch[1]
            }
          }
          
          return (
            <div key={idx} className="border-l-3 border-green-400/40 pl-6 relative">
              <div className="absolute -left-2 top-0 w-4 h-4 bg-green-400/20 rounded-full border-2 border-green-400/40"></div>
              
              <div className="mb-3">
                {degree && institution ? (
                  <>
                    <h4 className="text-xl font-bold text-white mb-1">{degree}</h4>
                    <p className="text-green-300 font-medium text-lg">{institution}</p>
                    <div className="flex items-center gap-4 mt-1">
                      {dates && <p className="text-slate-400 text-sm">{dates}</p>}
                      {gpa && <p className="text-slate-400 text-sm">GPA: {gpa}</p>}
                    </div>
                  </>
                ) : (
                  <h4 className="text-xl font-bold text-white mb-2">{titleLine}</h4>
                )}
              </div>
              
              <div className="text-slate-300 leading-relaxed space-y-2">
                {details.filter(line => !line.toLowerCase().includes('gpa')).map((line, i) => {
                  const cleanLine = line.trim().replace(/^[•\-\*]\s*/, '')
                  return cleanLine ? (
                    <div key={i} className="flex items-start gap-3">
                      <div className="w-1.5 h-1.5 bg-green-400/60 rounded-full mt-2 flex-shrink-0" />
                      <span className="text-sm leading-relaxed">{cleanLine}</span>
                    </div>
                  ) : null
                })}
              </div>
            </div>
          )
        })}
      </div>
    )
  }
  
  // Certifications section - format certifications with badges
  if (sectionType.includes('certifications') || sectionType.includes('licenses')) {
    const certEntries = content.split(/\n\s*\n|\n/).filter(e => e.trim())
    
    return (
      <div className="space-y-6">
        {certEntries.map((cert, idx) => {
          const cleanCert = cert.trim()
          
          // Try to parse certification name, issuer, and date
          let certName = cleanCert
          let issuer = ""
          let date = ""
          
          // Look for patterns like "AWS Certified Solutions Architect - Amazon (2023)"
          const certMatch = cleanCert.match(/^(.+?)\s*[-–]\s*(.+?)(\s*\(.*\))?$/)
          if (certMatch) {
            certName = certMatch[1].trim()
            issuer = certMatch[2].trim()
            date = certMatch[3] ? certMatch[3].replace(/[()]/g, '').trim() : ""
          } else {
            // Look for date patterns at the end
            const dateMatch = cleanCert.match(/^(.+?)\s*\((.+?)\)$/)
            if (dateMatch) {
              certName = dateMatch[1].trim()
              date = dateMatch[2].trim()
            }
          }
          
          return (
            <div key={idx} className="border-l-3 border-amber-400/40 pl-6 relative">
              <div className="absolute -left-2 top-0 w-4 h-4 bg-amber-400/20 rounded-full border-2 border-amber-400/40"></div>
              
              <div className="mb-2">
                <h4 className="text-lg font-bold text-white mb-1">{certName}</h4>
                {issuer && <p className="text-amber-300 font-medium">{issuer}</p>}
                {date && <p className="text-slate-400 text-sm mt-1">{date}</p>}
              </div>
            </div>
          )
        })}
      </div>
    )
  }
  
  // Default formatting for other sections with improved presentation
  return (
    <div className="space-y-4">
      {content.split(/\n\s*\n/).filter(para => para.trim()).map((paragraph, idx) => {
        const lines = paragraph.trim().split('\n').filter(line => line.trim())
        
        if (lines.length === 1) {
          // Single line - could be a title or single item
          return (
            <p key={idx} className="text-slate-300 leading-relaxed font-medium">
              {lines[0]}
            </p>
          )
        } else {
          // Multiple lines - format as list or structured content
          return (
            <div key={idx} className="space-y-2">
              {lines.map((line, lineIdx) => {
                const cleanLine = line.trim().replace(/^[•\-\*]\s*/, '')
                const isBullet = line.trim().match(/^[•\-\*]\s*/)
                
                return (
                  <div key={lineIdx} className={isBullet ? "flex items-start gap-3" : ""}>
                    {isBullet && (
                      <div className="w-1.5 h-1.5 bg-slate-400 rounded-full mt-2 flex-shrink-0" />
                    )}
                    <span className="text-slate-300 leading-relaxed text-sm">
                      {cleanLine}
                    </span>
                  </div>
                )
              })}
            </div>
          )
        }
      })}
    </div>
  )
}

// Call the correct backend endpoint to generate final resume
async function generateFinalResume(sessionId: string): Promise<string> {
  try {
    const response = await fetch('/api/generate-final-resume', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ session_id: sessionId }),
    })
    
    if (!response.ok) {
      throw new Error(`Failed to generate final resume: ${response.status}`)
    }
    
    const data = await response.json()
    return data.final_resume || ""
  } catch (error) {
    console.error('Error generating final resume:', error)
    throw error
  }
}

export default function ResumePreview() {
  const router = useRouter()
  const [finalResume, setFinalResume] = React.useState<string>("")
  const [parsedSections, setParsedSections] = React.useState<Array<{ title: string, content: string }>>([])
  const [loading, setLoading] = React.useState(true)
  const [error, setError] = React.useState<string | null>(null)
  const [sessionId, setSessionId] = React.useState<string | null>(null)

  React.useEffect(() => {
    async function loadFinalResume() {
      try {
        // First, try to get session ID from stored analysis data
        const storedSessionData = window.sessionStorage.getItem("analysis_session_data")
        let retrievedSessionId = null
        
        if (storedSessionData) {
          const parsed = JSON.parse(storedSessionData)
          retrievedSessionId = parsed.sessionId
        } else {
          // Fallback to direct session ID storage
          retrievedSessionId = window.sessionStorage.getItem("last_analysis_id")
        }
        
        if (!retrievedSessionId) {
          setError("No analysis session found. Please run an analysis first.")
          return
        }
        
        setSessionId(retrievedSessionId)
        console.log("Loading final resume for session:", retrievedSessionId)
        
        // Call backend to generate the final resume
        const finalResumeText = await generateFinalResume(retrievedSessionId)
        
        if (!finalResumeText) {
          setError("No final resume content received from backend.")
          return
        }
        
        console.log("Final resume received:", finalResumeText.substring(0, 200) + "...")
        
        // Parse the formatted resume into sections
        const sections = parseFinalResume(finalResumeText)
        
        console.log("Parsed sections:", sections.map(s => ({ title: s.title, contentLength: s.content.length })))
        
        setFinalResume(finalResumeText)
        setParsedSections(sections)
        
      } catch (error) {
        console.error("Error loading final resume:", error)
        setError("Failed to load final resume. Please try again.")
      } finally {
        setLoading(false)
      }
    }

    loadFinalResume()
  }, [])

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 to-slate-800 flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="w-8 h-8 mx-auto mb-4 animate-spin text-blue-400" />
          <p className="text-white/70">Generating your final resume...</p>
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
            <h2 className="text-2xl font-semibold mb-4 text-white">Resume Not Available</h2>
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
                <h1 className="text-xl font-bold text-white">Final Resume</h1>
                <p className="text-white/60 text-sm">Your resume has been processed with your approved improvements.</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <Button
                onClick={() => {
                  downloadTxt("resume.txt", finalResume)
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
            {/* Display Success Message */}
            <div className="mb-8 text-center">
              <div className="inline-flex items-center gap-2 px-4 py-2 bg-emerald-500/20 text-emerald-300 rounded-full">
                <CheckCircle className="w-4 h-4" />
                <span className="text-sm font-medium">Professional Resume Ready</span>
              </div>
            </div>
            
            {/* Section-by-Section Rendering */}
            <div className="space-y-12">
              {parsedSections.length > 0 ? (
                parsedSections.map((section, index) => (
                  <section key={index} className="resume-section">
                    <h2 className="text-2xl font-bold text-white mb-6 pb-2 border-b border-white/20">
                      {section.title}
                    </h2>
                    {formatSectionContent(section.title, section.content)}
                  </section>
                ))
              ) : (
                // Fallback to raw resume text if parsing failed
                <div className="space-y-6">
                  <h2 className="text-2xl font-bold text-white mb-6">Professional Resume</h2>
                  <div className="text-slate-300 leading-relaxed whitespace-pre-line">
                    {finalResume || "Resume content not available"}
                  </div>
                </div>
              )}
            </div>
            
            {/* Footer with session info */}
            {sessionId && (
              <div className="mt-12 pt-8 border-t border-white/10">
                <div className="text-center">
                  <p className="text-slate-400 text-sm">
                    Session ID: {sessionId.substring(0, 8)}... • Generated with ResumeWise AI
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
} 