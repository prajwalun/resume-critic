"use client"

import React, { useState, useEffect, useRef } from "react"
import {
  Upload,
  FileText,
  Briefcase,
  Brain,
  Moon,
  Sun,
  CheckCircle,
  XCircle,
  Edit3,
  Zap,
  TrendingUp,
  Target,
  Star,
  MessageCircle,
  Download,
  RefreshCw,
  GraduationCap,
  Code,
  Building2,
  Sparkles,
  ArrowRight,
  Lightbulb,
  Shield,
  Clock,
  Users,
  BarChart3,
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { useTheme } from "next-themes"
import { resumeCriticAPI, type ResumeAnalysisResponse, type ResumeBullet, type ClarificationRequest } from "@/lib/api"
import { useRouter } from 'next/navigation'
import { cleanResumeMarkdown } from "./resume-preview/page"
import renderSection from "./resume-preview/page"
import remarkGfm from "remark-gfm";
import { formatResumeSections } from "./resume-preview/page";
import ReactMarkdown from 'react-markdown';

interface CritiqueItem {
  id: string
  original: string
  suggested: string
  reason: string
  category: "Experience" | "Education" | "Skills" | "Projects" | "Format"
  impact: "High" | "Medium" | "Low"
  sectionId?: string
  needsClarification?: boolean
  clarificationQuestion?: string
  status: "pending" | "accepted" | "rejected" | "edited"
  editedText?: string
}

export default function ResumeCriticAI() {
  const [resumeFile, setResumeFile] = useState<File | null>(null)
  const [jobDescription, setJobDescription] = useState("")
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [critiques, setCritiques] = useState<CritiqueItem[]>([])
  const [showResults, setShowResults] = useState(false)
  const [analysisData, setAnalysisData] = useState<ResumeAnalysisResponse | null>(null)
  const [clarificationModal, setClarificationModal] = useState<{
    isOpen: boolean
    sectionId: string
    question: string
    originalText: string
    userResponse: string
  }>({
    isOpen: false,
    sectionId: "",
    question: "",
    originalText: "",
    userResponse: ""
  })
  const [editModal, setEditModal] = useState<{
    isOpen: boolean
    critiqueId: string
    originalText: string
    suggestedText: string
    editedText: string
  }>({
    isOpen: false,
    critiqueId: "",
    originalText: "",
    suggestedText: "",
    editedText: "",
  })
  const [isProcessingClarification, setIsProcessingClarification] = useState(false)
  const [isGeneratingFinal, setIsGeneratingFinal] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const { theme, setTheme } = useTheme()
  const [showFinalResume, setShowFinalResume] = useState(false)
  const [finalResume, setFinalResume] = useState("")
  const [isPdfLoading, setIsPdfLoading] = useState(false)
  const router = useRouter()

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (file) {
      setResumeFile(file)
      setError(null)
    }
  }

  const handleAnalyze = async () => {
    if (!resumeFile || !jobDescription.trim()) return

    setIsAnalyzing(true)
    setError(null)

    try {
      const response = await resumeCriticAPI.analyzeResume(
        resumeFile,
        jobDescription,
        true // review mode
      )

      if (response.success) {
        const analysisData = (response as any).data || response
        console.log("Analysis response:", response)
        console.log("Analysis data:", analysisData)
        setAnalysisData(analysisData)
        
        if (analysisData.critiques && Array.isArray(analysisData.critiques)) {
          const convertedCritiques: CritiqueItem[] = analysisData.critiques.map((critique: any) => ({
            id: critique.id,
            original: critique.original,
            suggested: critique.suggested,
            reason: critique.reason,
            category: critique.category,
            impact: critique.impact,
            sectionId: critique.sectionId,
            needsClarification: critique.needsClarification,
            clarificationQuestion: critique.clarificationQuestion,
            status: "pending"
          }))
          
          setCritiques(convertedCritiques)
        } else {
          setCritiques([])
        }
        
        setShowResults(true);
      } else {
        setError("Analysis failed. Please try again.")
      }
    } catch (error) {
      console.error("Analysis error:", error)
      setError(error instanceof Error ? error.message : "An unexpected error occurred")
    } finally {
    setIsAnalyzing(false)
    }
  }

  const handleClarification = async (sectionId: string, question: string, originalText: string) => {
    setClarificationModal({
      isOpen: true,
      sectionId,
      question,
      originalText,
      userResponse: "",
    })
  }

  const handleSubmitClarification = async () => {
    if (!analysisData || !clarificationModal.userResponse.trim()) return

    setIsProcessingClarification(true)

    try {
      const request: ClarificationRequest = {
        analysis_id: (analysisData as any).analysis_id,
        section_id: clarificationModal.sectionId,
        user_response: clarificationModal.userResponse,
        original_text: clarificationModal.originalText,
        question: clarificationModal.question,
      }

      const response = await resumeCriticAPI.processClarification(request)

      if (response.success) {
        const responseData = (response as any).data || response
        
        setCritiques(prev => prev.map(critique => {
          if (critique.sectionId === clarificationModal.sectionId) {
            return {
              ...critique,
              suggested: responseData.improved_section.improved_text,
              reason: responseData.improved_section.improvement_explanation,
              needsClarification: false,
            }
          }
          return critique
        }))

        setClarificationModal({
          isOpen: false,
          sectionId: "",
          question: "",
          originalText: "",
          userResponse: "",
        })
      } else {
        setError("Failed to process clarification. Please try again.")
      }
    } catch (error) {
      console.error("Clarification error:", error)
      setError(error instanceof Error ? error.message : "An unexpected error occurred")
    } finally {
      setIsProcessingClarification(false)
    }
  }

  const handleAccept = (id: string) => {
    setCritiques(prev => prev.map(critique => 
      critique.id === id ? { ...critique, status: "accepted" } : critique
    ))
  }

  const handleReject = (id: string) => {
    setCritiques(prev => prev.map(critique => 
      critique.id === id ? { ...critique, status: "rejected" } : critique
    ))
  }

  const handleUndo = (id: string) => {
    setCritiques(prev => prev.map(critique => 
      critique.id === id ? { ...critique, status: "pending" } : critique
    ))
  }

  const handleEdit = (id: string) => {
    const critique = critiques.find(c => c.id === id)
    if (critique) {
      setEditModal({
        isOpen: true,
        critiqueId: id,
        originalText: critique.original,
        suggestedText: critique.suggested,
        editedText: critique.suggested,
      })
    }
  }

  const handleSaveEdit = () => {
    setCritiques(prev => prev.map(critique => 
      critique.id === editModal.critiqueId 
        ? { ...critique, status: "edited", editedText: editModal.editedText }
        : critique
    ))
    setEditModal({ isOpen: false, critiqueId: "", originalText: "", suggestedText: "", editedText: "" })
  }

  const handleGenerateFinalResume = async () => {
    if (!analysisData) return

    setIsGeneratingFinal(true)

    try {
      const acceptedChanges = critiques
        .filter(critique => critique.status === "accepted" || critique.status === "edited" || critique.status === "rejected")
        .reduce((acc, critique) => {
          // Send "improved" for accepted/edited and "original" for rejected
          acc[critique.sectionId || critique.id] = (critique.status === "accepted" || critique.status === "edited") ? "improved" : "original"
          return acc
        }, {} as Record<string, string>)

      const response = await resumeCriticAPI.generateFinalResume({
        analysis_id: (analysisData as any).analysis_id,
        accepted_changes: acceptedChanges
      })

      if (response.success) {
        const finalResumeData = (response as any).data || response
        setFinalResume(finalResumeData.final_resume)
        setShowFinalResume(true)
        // Store in sessionStorage for preview fallback
        if (typeof window !== 'undefined') {
          window.sessionStorage.setItem('last_final_resume', finalResumeData.final_resume || '')
          window.sessionStorage.setItem('last_analysis_id', finalResumeData.analysis_id || '')
        }
      } else {
        setError("Failed to generate final resume. Please try again.")
      }
    } catch (error) {
      console.error("Final resume generation error:", error)
      setError(error instanceof Error ? error.message : "An unexpected error occurred")
    } finally {
      setIsGeneratingFinal(false)
    }
  }

  const getCategoryFromScore = (score: number): "Experience" | "Education" | "Skills" | "Projects" | "Format" => {
    if (score >= 80) return "Experience"
    if (score >= 60) return "Education"
    if (score >= 40) return "Skills"
    if (score >= 20) return "Projects"
    return "Format"
  }

  const getImpactFromScore = (score: number): "High" | "Medium" | "Low" => {
    if (score >= 7) return "High"
    if (score >= 4) return "Medium"
    return "Low"
  }

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case "Experience": return <Briefcase className="w-4 h-4" />
      case "Education": return <GraduationCap className="w-4 h-4" />
      case "Skills": return <Code className="w-4 h-4" />
      case "Projects": return <Building2 className="w-4 h-4" />
      case "Format": return <FileText className="w-4 h-4" />
      default: return <FileText className="w-4 h-4" />
    }
  }

  const getCategoryColor = (category: string) => {
    switch (category) {
      case "Experience": return "bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300"
      case "Education": return "bg-emerald-100 text-emerald-800 dark:bg-emerald-900/30 dark:text-emerald-300"
      case "Skills": return "bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-300"
      case "Projects": return "bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-300"
      case "Format": return "bg-slate-100 text-slate-800 dark:bg-slate-900/30 dark:text-slate-300"
      default: return "bg-slate-100 text-slate-800 dark:bg-slate-900/30 dark:text-slate-300"
    }
  }

  const getImpactColor = (impact: string) => {
    switch (impact) {
      case "High": return "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300"
      case "Medium": return "bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-300"
      case "Low": return "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300"
      default: return "bg-slate-100 text-slate-800 dark:bg-slate-900/30 dark:text-slate-300"
    }
  }

  // Modern Modal Component
  const Modal = ({ open, onClose, children }: { open: boolean; onClose: () => void; children: React.ReactNode }) => {
    if (!open) return null;

    useEffect(() => {
      const handleKey = (e: KeyboardEvent) => { if (e.key === "Escape") onClose(); };
      document.addEventListener("keydown", handleKey);
      return () => document.removeEventListener("keydown", handleKey);
    }, [onClose]);

  return (
      <div className="modal-overlay" onClick={onClose}>
        <div className="modal-content" onClick={(e) => e.stopPropagation()}>
          {children}
        </div>
      </div>
    );
  };

  function formatResumeSection(text: string, highlightDiffs: boolean = false, diffLines: Set<number> = new Set()) {
    if (!text) return ""
    
    const lines = text.split('\n')
    return lines.map((line, index) => {
      const isDiffLine = diffLines.has(index)
      const className = highlightDiffs && isDiffLine 
        ? "bg-emerald-100 dark:bg-emerald-900/30 border-l-4 border-emerald-500 pl-3 py-1 rounded-r-lg" 
        : ""
      
      return (
        <div key={index} className={className}>
          {line || '\u00A0'}
        </div>
      )
    })
  }

  function getDiffLines(original: string, suggested: string): Set<number> {
    const originalLines = original.split('\n')
    const suggestedLines = suggested.split('\n')
    const diffLines = new Set<number>()
    
    suggestedLines.forEach((line, index) => {
      if (originalLines[index] !== line) {
        diffLines.add(index)
      }
    })
    
    return diffLines
  }

  // Utility to parse a section into heading and content
  function parseSection(section: string) {
    const lines = section.trim().split(/\n+/);
    const heading = lines[0]?.replace(/^#+\s*/, "").trim();
    const content = lines.slice(1).join("\n").trim();
    return { heading, content };
  }

  // Utility to render a section with proper formatting
  function renderSection(section: string, i: number) {
    const { heading, content } = parseSection(section);
    // Skills/Technologies/Tools: chips
    if (/skills|technologies|tools|languages|certifications/i.test(heading || "")) {
      const items = content.split(/[,•\-\n]+/).map(s => s.trim()).filter(Boolean);
      return (
        <section key={i} className="resume-section mb-10">
          <h2 className="resume-heading text-2xl font-bold text-emerald-700 mb-4 tracking-tight">{heading}</h2>
          <ul className="resume-list flex flex-wrap gap-2">
            {items.map((item, idx) => <li key={idx} className="resume-chip bg-emerald-50 text-emerald-800 px-3 py-1 rounded-full text-sm font-medium border border-emerald-100">{item}</li>)}
          </ul>
        </section>
      );
    }
    // Experience/Projects/Education: block entries
    if (/projects|experience|education/i.test(heading || "")) {
      // Split by double newlines or project markers
      const entries = content.split(/\n{2,}|(?=^([A-Z][^\n]+\|[^\n]+|\*\*.+\*\*))/gm).map(e => e.trim()).filter(Boolean);
      // Track subheadings to avoid repetition
      const seenSubheadings = new Set();
      return (
        <section key={i} className="resume-section mb-10">
          <h2 className="resume-heading text-2xl font-bold text-emerald-700 mb-4 tracking-tight">{heading}</h2>
          <div className="space-y-8">
            {entries.map((entry, idx) => {
              // Remove markdown bold/italic artifacts
              let cleanEntry = entry.replace(/\*\*|__/g, '').replace(/\*/g, '');
              // Try to split job/project/degree line and details
              const [firstLine, ...rest] = cleanEntry.split('\n');
              let title = firstLine, meta = '', details = rest.join('\n').trim();
              // For education, try to split degree, institution, date/location
              if (/education/i.test(heading || "")) {
                const eduMatch = firstLine.match(/^(.*?)(?:,|\|)(.*?)(\d{4}.*)?$/);
                if (eduMatch) {
                  title = eduMatch[1].trim();
                  meta = [eduMatch[2], eduMatch[3]].filter(Boolean).join(' | ').trim();
                }
              } else {
                // For experience/projects
                const match = firstLine.match(/^(.*?\|.*?)\|\s*(.*?\d{4}.*?)\s*(.*)$/);
                if (match) {
                  title = match[1].trim();
                  meta = match[2].trim();
                  details = (match[3] + '\n' + details).trim();
                }
              }
              // Remove repeated subheadings (e.g., 'Relevant Coursework')
              let detailsNode = null;
              let lines = details.split(/\n/).map(l => l.trim()).filter(Boolean);
              lines = lines.filter(line => {
                const lower = line.toLowerCase();
                if (/^(relevant coursework|achievements?|responsibilities?|skills?):?$/i.test(lower)) {
                  if (seenSubheadings.has(lower)) return false;
                  seenSubheadings.add(lower);
                }
                return true;
              });
              // If details look like a list or comma-separated, render as bullets
              if (lines.length > 1 || /,/.test(details)) {
                let items = lines;
                if (lines.length === 1 && /,/.test(lines[0])) {
                  items = lines[0].split(/,|•|\u2022/).map(s => s.trim()).filter(Boolean);
                }
                detailsNode = (
                  <ul className="list-disc ml-6 space-y-1">
                    {items.map((l, j) => <li key={j} className="text-slate-700 text-base leading-relaxed font-normal">{l}</li>)}
                  </ul>
                );
              } else if (details) {
                detailsNode = <div className="text-slate-700 text-base leading-relaxed font-normal whitespace-pre-line">{details}</div>;
              }
              return (
                <div key={idx} className="mb-4">
                  <div className="font-bold text-lg text-slate-900 mb-1">{title}</div>
                  {meta && <div className="text-slate-500 text-sm mb-1">{meta}</div>}
                  {detailsNode}
                </div>
              );
            })}
          </div>
        </section>
      );
    }
    // Default: paragraph or list
    if (new RegExp('^[-*] ', 'm').test(content) || /,/.test(content)) {
      let items = content.split(/\n/).map(l => l.trim()).filter(Boolean);
      if (items.length === 1 && /,/.test(items[0])) {
        items = items[0].split(/,|•|\u2022/).map(s => s.trim()).filter(Boolean);
      }
      return (
        <section key={i} className="resume-section mb-10">
          <h2 className="resume-heading text-2xl font-bold text-emerald-700 mb-4 tracking-tight">{heading}</h2>
          <ul className="list-disc ml-6 space-y-1">
            {items.map((l, j) => <li key={j} className="text-slate-700 text-base leading-relaxed font-normal">{l}</li>)}
          </ul>
        </section>
      );
    }
    return (
      <section key={i} className="resume-section mb-10">
        <h2 className="resume-heading text-2xl font-bold text-emerald-700 mb-4 tracking-tight">{heading}</h2>
        <div className="text-slate-700 text-base leading-relaxed font-normal whitespace-pre-line">{content}</div>
      </section>
    );
  }

  function renderFormattedSectionFromMarkdown(md: string) {
    return (
      <div className="prose max-w-none">
        <ReactMarkdown remarkPlugins={[remarkGfm]}>{md}</ReactMarkdown>
      </div>
    );
  }

  function preprocessForMarkdown(text: string, fallbackHeading: string) {
    if (!text) return '';
    let md = text.trim();
    // If no heading, add one
    if (!/^#+ /.test(md)) {
      md = `## ${fallbackHeading}\n` + md;
    }
    // For experience/education/projects, don't bulletize, just preserve structure
    if (/(experience|education|project)/i.test(fallbackHeading)) {
      return md;
    }
    // If not already markdown bullets, but has multiple sentences, try to bulletize
    if (!/\n[-*] /.test(md) && /\n/.test(md)) {
      const lines = md.split('\n').map(l => l.trim());
      if (lines.length > 2) {
        const heading = lines[0];
        const rest = lines.slice(1).map(l => l ? `- ${l}` : '').join('\n');
        md = `${heading}\n${rest}`;
      }
    }
    return md;
  }

  // Add a new utility to further clean and format resume markdown for display
  function formatResumeMarkdown(md: string) {
    // Remove duplicate subheadings within a section
    md = md.replace(/(Relevant Coursework:)([\s\S]*?)(?=Relevant Coursework:|$)/g, (block: string) => {
      // Only keep the first 'Relevant Coursework:' per section
      const lines = block.split('\n');
      const seen = new Set();
      return lines.filter((line: string) => {
        if (/^Relevant Coursework:/i.test(line)) {
          if (seen.has('rc')) return false;
          seen.add('rc');
        }
        return true;
      }).join('\n');
    });
    // Bulletize comma-separated lists
    md = md.replace(/(Relevant Coursework:|Skills:|Technologies:|Tools:|Languages:|Achievements:|Responsibilities:)[ \t]*\n?([^-\n][^\n]*)/gi, (match: string, heading: string, items: string) => {
      if (!items) return match;
      const bullets = items.split(/,|•|\u2022/).map((s: string) => s.trim()).filter(Boolean);
      if (bullets.length > 1) {
        return `${heading}\n` + bullets.map((b: string) => `- ${b}`).join('\n');
      }
      return match;
    });
    // Bulletize any line with multiple comma-separated items (not already a list)
    md = md.replace(/^(?![-*] )([^\n]+,[^\n]+)$/gm, (line: string) => {
      const items = line.split(/,|•|\u2022/).map((s: string) => s.trim()).filter(Boolean);
      if (items.length > 1) {
        return items.map((b: string) => `- ${b}`).join('\n');
      }
      return line;
    });
    // Remove extra blank lines
    md = md.replace(/\n{3,}/g, '\n\n');
    return md;
  }

  const renderCritiques = () => (
    <div className="space-y-6 animate-fade-in">
      <div className="text-center mb-8">
        <h2 className="text-3xl font-bold text-slate-900 dark:text-white mb-4">
          AI Analysis Results
          </h2>
        <p className="text-slate-600 dark:text-slate-400 max-w-2xl mx-auto">
          Review and refine your resume with our AI-powered suggestions. Each recommendation is tailored to your target role.
          </p>
        </div>

      <div className="grid gap-6">
        {critiques.map((critique) => {
          const diffLines = getDiffLines(critique.original, critique.suggested)
          const isAccepted = critique.status === "accepted"
          const isRejected = critique.status === "rejected"
          const isEdited = critique.status === "edited"

          return (
            <Card key={critique.id} className={`card-modern transition-all duration-300 ${isAccepted ? 'ring-2 ring-emerald-500/20' : isRejected ? 'ring-2 ring-red-500/20' : ''}`}>
              <CardHeader className="pb-4">
                <div className="flex items-start justify-between">
                  <div className="flex items-center space-x-3">
                    <div className={`p-2 rounded-lg ${getCategoryColor(critique.category)}`}>
                      {getCategoryIcon(critique.category)}
                    </div>
                    <div>
                      <CardTitle className="text-lg font-semibold text-slate-900 dark:text-white">
                        {critique.category} Improvement
                      </CardTitle>
                      <div className="flex items-center space-x-2 mt-1">
                        <Badge className={`badge-modern ${getCategoryColor(critique.category)}`}>
                          {critique.category}
                        </Badge>
                        <Badge className={`badge-modern ${getImpactColor(critique.impact)}`}>
                          {critique.impact} Impact
                        </Badge>
                        {critique.needsClarification && (
                          <Badge className="badge-modern bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-300">
                            Needs Clarification
                          </Badge>
                        )}
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    {critique.status === "pending" && (
                      <>
                        <Button onClick={() => handleAccept(critique.id)} className="btn-primary flex items-center gap-2 text-sm px-5 py-2 min-w-[110px]">
                          <CheckCircle className="w-4 h-4" /> Accept
                        </Button>
                        <Button onClick={() => handleReject(critique.id)} className="btn-danger flex items-center gap-2 text-sm px-5 py-2 min-w-[110px]">
                          <XCircle className="w-4 h-4" /> Reject
                        </Button>
                        <Button onClick={() => handleEdit(critique.id)} className="btn-secondary flex items-center gap-2 text-sm px-5 py-2 min-w-[110px]">
                          <Edit3 className="w-4 h-4" /> Edit
                        </Button>
                      </>
                    )}
                    {(isAccepted || isRejected || isEdited) && (
                      <Button onClick={() => handleUndo(critique.id)} className="btn-ghost flex items-center gap-2 text-sm px-5 py-2 min-w-[110px]">
                        <RefreshCw className="w-4 h-4" /> Undo
                      </Button>
                    )}
                  </div>
                </div>
              </CardHeader>

              <CardContent className="space-y-6">
                {critique.needsClarification && critique.clarificationQuestion && (
                  <div className="bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-xl p-4">
                    <div className="flex items-start space-x-3">
                      <MessageCircle className="w-5 h-5 text-amber-600 dark:text-amber-400 mt-0.5 flex-shrink-0" />
                      <div className="flex-1">
                        <h4 className="font-semibold text-amber-900 dark:text-amber-100 mb-2">
                          Clarification Needed
                        </h4>
                        <p className="text-amber-800 dark:text-amber-200 mb-3">
                          {critique.clarificationQuestion}
                        </p>
                        <Button 
                          onClick={() => handleClarification(critique.sectionId!, critique.clarificationQuestion!, critique.original)}
                          className="btn-primary text-sm"
                        >
                          Provide Details
                        </Button>
                      </div>
                    </div>
                  </div>
                )}

                <div className="grid md:grid-cols-2 gap-6">
                  <div>
                    <h4 className="font-semibold text-slate-900 mb-3 flex items-center">
                      <FileText className="w-4 h-4 mr-2 text-slate-500" />
                      Current Version
                    </h4>
                    <div className="bg-slate-50 rounded-xl p-4 border border-slate-200">
                      {critique.original && critique.original.trim() ? (
                        renderFormattedSectionFromMarkdown(preprocessForMarkdown(critique.original, critique.category || 'Section'))
                      ) : (
                        <div className="text-slate-400 italic">No original content available.</div>
                      )}
                    </div>
                  </div>

                  <div>
                    <h4 className="font-semibold text-slate-900 mb-3 flex items-center">
                      <Sparkles className="w-4 h-4 mr-2 text-emerald-500" />
                      Agent Suggestion
                    </h4>
                    <div className="bg-emerald-50 rounded-xl p-4 border border-emerald-200">
                      {critique.status === "edited" && critique.editedText
                        ? renderFormattedSectionFromMarkdown(preprocessForMarkdown(critique.editedText, critique.category || 'Section'))
                        : renderFormattedSectionFromMarkdown(preprocessForMarkdown(critique.suggested, critique.category || 'Section'))}
                    </div>
                  </div>
                </div>

                <div className="bg-slate-50 dark:bg-slate-800/50 rounded-xl p-4 border border-slate-200 dark:border-slate-700">
                  <h4 className="font-semibold text-slate-900 dark:text-white mb-2 flex items-center">
                    <Lightbulb className="w-4 h-4 mr-2 text-amber-500" />
                    Why This Change?
                  </h4>
                  <p className="text-slate-700 dark:text-slate-300 text-sm leading-relaxed">
                    {critique.reason}
                  </p>
                </div>
              </CardContent>
            </Card>
          )
        })}
      </div>

      {critiques.length > 0 && (
        <div className="text-center pt-8">
          <Button 
            onClick={handleGenerateFinalResume}
            disabled={isGeneratingFinal || critiques.every(c => c.status === "pending")}
            className="btn-primary text-lg px-8 py-4"
          >
            {isGeneratingFinal ? (
              <>
                <div className="progress-ring mr-3" />
                Generating Final Resume...
              </>
            ) : (
              <>
                <Download className="w-5 h-5 mr-3" />
                Generate Final Resume
              </>
            )}
          </Button>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-3">
            Accept or edit suggestions to enable final resume generation
          </p>
        </div>
      )}
    </div>
  )

  const renderFinalResume = () => (
    <div className="animate-fade-in">
      {/* Top bar with New Analysis button and download icon */}
      <div className="flex items-center justify-between mb-6">
        <Button onClick={() => {
          setShowFinalResume(false)
          setShowResults(false)
          setCritiques([])
          setAnalysisData(null)
          setResumeFile(null)
          setJobDescription("")
        }} className="btn-secondary">
          <RefreshCw className="w-4 h-4 mr-2" /> New Analysis
        </Button>
        <button
          className="btn-ghost relative group"
          onClick={() => downloadTxt("ResumeWise-Resume.txt", finalResume)}
          title="Download as TXT"
          style={{ padding: 8, borderRadius: 8 }}
        >
          <Download className="w-6 h-6 text-slate-500 group-hover:text-blue-600 transition" />
          <span className="tooltip group-hover:opacity-100 group-focus:opacity-100">Download as TXT</span>
        </button>
      </div>
      <div className="text-center mb-8">
        <h2 className="text-3xl font-bold text-slate-900 dark:text-white mb-4">
          Your Improved Resume
        </h2>
        <p className="text-slate-600 dark:text-slate-400">
          Here's your resume with all accepted improvements applied.
        </p>
      </div>
      <div className="resume-card">
        <div className="max-w-3xl mx-auto">
          {renderFormattedSectionFromMarkdown(finalResume)}
        </div>
      </div>
    </div>
  )

  // Utility function for downloading
  function downloadTxt(filename: string, text: string) {
    const element = document.createElement("a");
    const file = new Blob([text], { type: "text/plain" });
    element.href = URL.createObjectURL(file);
    element.download = filename;
    document.body.appendChild(element);
    element.click();
    document.body.removeChild(element);
  }

  // Loading overlay
  const LoadingOverlay = ({ show, text }: { show: boolean; text?: string }) => show ? (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center">
      <div className="card-modern p-8 text-center">
        <div className="progress-ring mx-auto mb-4" />
        <p className="text-lg font-semibold text-slate-900 dark:text-white">
          {text || "Processing..."}
        </p>
      </div>
    </div>
  ) : null

  function ClarificationInputModal({ question, value, onChange, onCancel, onSubmit, isProcessing }: {
    question: string;
    value: string;
    onChange: (val: string) => void;
    onCancel: () => void;
    onSubmit: () => void;
    isProcessing: boolean;
  }) {
    const textareaRef = useRef<HTMLTextAreaElement>(null);
    useEffect(() => {
      if (textareaRef.current) textareaRef.current.focus();
    }, []);
    return (
      <div className="p-6">
        <h3 className="text-xl font-semibold text-slate-900 dark:text-white mb-4">
          Provide Additional Details
        </h3>
        <p className="text-slate-600 dark:text-slate-400 mb-4">
          {question}
        </p>
        <Textarea
          ref={textareaRef}
          value={value}
          onChange={e => onChange(e.target.value)}
          placeholder="Enter your response..."
          className="input-modern mb-4 min-h-[120px]"
        />
        <div className="flex justify-end space-x-3">
          <Button onClick={onCancel} className="btn-secondary">
            Cancel
          </Button>
          <Button onClick={onSubmit} disabled={isProcessing || !value.trim()} className="btn-primary">
            {isProcessing ? "Processing..." : "Submit"}
          </Button>
        </div>
      </div>
    );
  }

  if (showFinalResume) {
    return renderFinalResume()
  }

  if (showResults) {
    return (
      <div className="animate-fade-in">
        {renderCritiques()}
        
        <Modal open={clarificationModal.isOpen} onClose={() => setClarificationModal({ isOpen: false, sectionId: "", question: "", originalText: "", userResponse: "" })}>
          <ClarificationInputModal
            question={clarificationModal.question}
            value={clarificationModal.userResponse}
            onChange={val => setClarificationModal(prev => ({ ...prev, userResponse: val }))}
            onCancel={() => setClarificationModal({ isOpen: false, sectionId: "", question: "", originalText: "", userResponse: "" })}
            onSubmit={handleSubmitClarification}
            isProcessing={isProcessingClarification}
          />
        </Modal>

        <Modal open={editModal.isOpen} onClose={() => setEditModal({ isOpen: false, critiqueId: "", originalText: "", suggestedText: "", editedText: "" })}>
          <div className="p-6">
            <h3 className="text-xl font-semibold text-slate-900 dark:text-white mb-4">
              Edit Suggestion
            </h3>
            <Textarea
              value={editModal.editedText}
              onChange={(e) => setEditModal(prev => ({ ...prev, editedText: e.target.value }))}
              placeholder="Edit the suggested text..."
              className="input-modern mb-4 min-h-[200px]"
            />
            <div className="flex justify-end space-x-3">
              <Button 
                onClick={() => setEditModal({ isOpen: false, critiqueId: "", originalText: "", suggestedText: "", editedText: "" })}
                className="btn-secondary"
              >
                Cancel
              </Button>
              <Button 
                onClick={handleSaveEdit}
                className="btn-primary"
              >
                Save Changes
              </Button>
            </div>
          </div>
        </Modal>
      </div>
    )
  }

  return (
    <div className="animate-fade-in">
      {/* Hero Section */}
      <div className="text-center mb-12">
        <div className="inline-flex items-center space-x-2 bg-emerald-100 text-emerald-800 px-4 py-2 rounded-full text-sm font-medium mb-6">
          <span className="inline-block w-4 h-4 bg-[var(--accent)] rounded-full" />
          <span>AI-Powered Resume Analysis</span>
        </div>
        <h1 className="hero-title">
          Transform Your Resume with <span className="hero-highlight">AI Intelligence</span>
        </h1>
        <p className="text-xl text-slate-600 max-w-3xl mx-auto leading-relaxed">
          Get professional, personalized feedback on your resume. Our AI analyzes your content against job requirements and provides actionable improvements.
        </p>
      </div>

      {/* Features Grid */}
      <div className="grid md:grid-cols-3 gap-6 mb-12">
        <div className="card-modern text-center p-6">
          <div className="w-12 h-12 bg-blue-50 rounded-xl flex items-center justify-center mx-auto mb-4">
            <span className="inline-block w-6 h-6 bg-blue-400 rounded-full" />
          </div>
          <h3 className="text-lg font-semibold text-slate-900 mb-2">AI Analysis</h3>
          <p className="text-slate-600 text-sm">Advanced AI reviews your resume against job requirements</p>
        </div>

        <div className="card-modern text-center p-6">
          <div className="w-12 h-12 bg-emerald-50 rounded-xl flex items-center justify-center mx-auto mb-4">
            <span className="inline-block w-6 h-6 bg-emerald-400 rounded-full" />
          </div>
          <h3 className="text-lg font-semibold text-slate-900 mb-2">Targeted Feedback</h3>
          <p className="text-slate-600 text-sm">Personalized suggestions based on your target role</p>
        </div>

        <div className="card-modern text-center p-6">
          <div className="w-12 h-12 bg-purple-50 rounded-xl flex items-center justify-center mx-auto mb-4">
            <span className="inline-block w-6 h-6 bg-purple-400 rounded-full" />
          </div>
          <h3 className="text-lg font-semibold text-slate-900 mb-2">Instant Results</h3>
          <p className="text-slate-600 text-sm">Get comprehensive feedback in seconds, not days</p>
        </div>
                  </div>

      {/* Upload Section */}
      <Card className="card-modern max-w-4xl mx-auto">
        <CardHeader className="text-center pb-6">
          <CardTitle className="text-2xl font-bold text-slate-900 mb-2">
            Upload Your Resume
                </CardTitle>
          <CardDescription className="text-slate-600">
            Upload your resume and provide the job description for targeted analysis
                </CardDescription>
              </CardHeader>

        <CardContent className="space-y-6">
          {/* File Upload */}
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-3">
              Resume File (PDF, DOCX, TXT)
            </label>
            <div className={`upload-area ${resumeFile ? 'border-emerald-500 bg-emerald-50' : ''}`}>
              <input
                type="file"
                accept=".pdf,.docx,.txt"
                onChange={handleFileUpload}
                className="hidden"
                id="resume-upload"
              />
              <label htmlFor="resume-upload" className="cursor-pointer">
                <Upload className="w-12 h-12 text-slate-400 mx-auto mb-4" />
                <p className="text-lg font-medium text-slate-900 mb-2">
                  {resumeFile ? resumeFile.name : "Choose a file or drag it here"}
                </p>
                <p className="text-sm text-slate-500">
                  {resumeFile ? "File selected successfully" : "Supports PDF, DOCX, and TXT formats"}
                </p>
              </label>
            </div>
          </div>

          {/* Job Description */}
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-3">
              Job Description
            </label>
                <Textarea
                  value={jobDescription}
                  onChange={(e) => setJobDescription(e.target.value)}
              placeholder="Paste the job description here to get targeted feedback..."
              className="input-modern min-h-[120px] resize-none"
                />
            <p className="text-sm text-slate-500 mt-2">
              The more detailed the job description, the better our analysis will be.
            </p>
          </div>

          {/* Error Display */}
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-xl p-4">
              <p className="text-red-800 text-sm">{error}</p>
            </div>
          )}

          {/* Analyze Button */}
          <div className="text-center pt-4">
            <Button
              onClick={handleAnalyze}
              disabled={!resumeFile || !jobDescription.trim() || isAnalyzing}
              className="btn-primary text-lg px-8 py-4"
            >
              {isAnalyzing ? (
                <>
                  <div className="progress-ring mr-3" />
                  Analyzing Resume...
                </>
              ) : (
                <>
                  <Zap className="w-5 h-5 mr-3" />
                  Analyze Resume
                </>
              )}
            </Button>
            <p className="text-sm text-slate-500 mt-3">
              Upload both files to start your analysis
            </p>
                    </div>
                  </CardContent>
                </Card>

      {/* Loading Overlay */}
      <LoadingOverlay show={isAnalyzing} text="Analyzing your resume..." />
    </div>
  )
}
