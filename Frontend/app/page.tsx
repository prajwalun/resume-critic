"use client"

import React from "react"

import { useState } from "react"
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
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { useTheme } from "next-themes"
import { resumeCriticAPI, type ResumeAnalysisResponse, type ResumeBullet, type ClarificationRequest } from "@/lib/api"
import { useRouter } from 'next/navigation'
import { cleanResumeMarkdown } from "./resume-preview/page";
import remarkGfm from "remark-gfm";

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
        // The backend wraps the analysis data in a 'data' field
        const analysisData = (response as any).data || response
        console.log("Analysis response:", response)
        console.log("Analysis data:", analysisData)
        setAnalysisData(analysisData)
        
        // The backend now provides critiques directly
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
        // The backend wraps the response in a 'data' field
        const responseData = (response as any).data || response
        
        // Update the critique with the improved section
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
    setCritiques((prev) => prev.map((c) => 
      c.id === id ? { ...c, status: "accepted" } : c
    ))
  }

  const handleReject = (id: string) => {
    setCritiques((prev) => prev.map((c) => 
      c.id === id ? { ...c, status: "rejected" } : c
    ))
  }

  const handleUndo = (id: string) => {
    setCritiques((prev) => prev.map((c) => 
      c.id === id ? { ...c, status: "pending" } : c
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
        editedText: critique.suggested
      })
    }
  }

  const handleSaveEdit = () => {
    setCritiques((prev) => prev.map((c) => 
      c.id === editModal.critiqueId 
        ? { ...c, status: "edited", editedText: editModal.editedText }
        : c
    ))
    setEditModal({ isOpen: false, critiqueId: "", originalText: "", suggestedText: "", editedText: "" })
  }

  const handleGenerateFinalResume = async () => {
    if (!analysisData) return;
    setIsGeneratingFinal(true);
    try {
      const acceptedChanges: Record<string, string> = {};
      critiques.forEach(critique => {
        if (critique.sectionId) {
          acceptedChanges[critique.sectionId] =
            critique.status === "accepted" || critique.status === "edited"
              ? "improved"
              : "original";
        }
      });
      const response = await resumeCriticAPI.generateFinalResume({
        analysis_id: (analysisData as any).analysis_id,
        accepted_changes: acceptedChanges
      });
      if (response.success) {
        // Navigate to /resume-preview with base64-encoded resume
        const finalResumeText = (response as any).final_resume || (response as any).data?.final_resume || "";
        const encoded = btoa(unescape(encodeURIComponent(finalResumeText)));
        router.push(`/resume-preview?data=${encoded}`);
      }
    } catch (error) {
      setError("Failed to generate final resume. Please try again.");
    } finally {
      setIsGeneratingFinal(false);
    }
  };

  const getCategoryFromScore = (score: number): "Experience" | "Education" | "Skills" | "Projects" | "Format" => {
    if (score >= 7) return "Experience"
    if (score >= 5) return "Education"
    if (score >= 3) return "Skills"
    return "Format"
  }

  const getImpactFromScore = (score: number): "High" | "Medium" | "Low" => {
    if (score >= 7) return "High"
    if (score >= 4) return "Medium"
    return "Low"
  }

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case "Impact":
        return <TrendingUp className="w-4 h-4" />
      case "Clarity":
        return <Target className="w-4 h-4" />
      case "Keywords":
        return <Zap className="w-4 h-4" />
      case "Format":
        return <Star className="w-4 h-4" />
      case "Experience":
        return <Briefcase className="w-4 h-4" />
      case "Education":
        return <GraduationCap className="w-4 h-4" />
      case "Skills":
        return <Code className="w-4 h-4" />
      case "Projects":
        return <Building2 className="w-4 h-4" />
      default:
        return <Brain className="w-4 h-4" />
    }
  }

  const getCategoryColor = (category: string) => {
    switch (category) {
      case "Impact":
        return "bg-gradient-to-r from-emerald-500 to-green-500"
      case "Clarity":
        return "bg-gradient-to-r from-orange-500 to-amber-500"
      case "Keywords":
        return "bg-gradient-to-r from-yellow-500 to-orange-500"
      default:
        return "bg-gradient-to-r from-red-500 to-pink-500"
    }
  }

  // UI/UX Overhaul: Accordion, Two-Column, Formatting, Clarification
  // Placeholder Accordion/Modal components (replace with your UI lib as needed)
  const Accordion = ({ children }: { children: React.ReactNode }) => <div>{children}</div>;
  const AccordionItem = ({ title, children }: { title: string; children: React.ReactNode }) => {
    const [open, setOpen] = React.useState(false);
    return (
      <div className="mb-4 border rounded-lg">
        <button className="w-full text-left px-4 py-2 font-semibold bg-slate-100 dark:bg-slate-800" onClick={() => setOpen(o => !o)}>
          {title}
        </button>
        {open && <div className="p-4 bg-white dark:bg-slate-900">{children}</div>}
      </div>
    );
  };
  const Modal = ({ open, onClose, children }: { open: boolean; onClose: () => void; children: React.ReactNode }) => {
    React.useEffect(() => {
      if (!open) return;
      const handleKey = (e: KeyboardEvent) => { if (e.key === "Escape") onClose(); };
      window.addEventListener("keydown", handleKey);
      return () => window.removeEventListener("keydown", handleKey);
    }, [open, onClose]);
    return open ? (
      <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50" onClick={onClose}>
        <div className="bg-white dark:bg-slate-900 p-6 rounded-lg shadow-lg min-w-[300px] max-w-lg relative" onClick={e => e.stopPropagation()}>
          {children}
          <button aria-label="Close modal" className="absolute top-2 right-2 text-slate-400 hover:text-slate-700 dark:hover:text-white focus:outline-none focus:ring-2 focus:ring-blue-500 rounded-full" onClick={onClose}>
            <span aria-hidden>×</span>
          </button>
        </div>
      </div>
    ) : null;
  };

  // Enhanced formatting for resume sections and highlighting differences
  function formatResumeSection(text: string, highlightDiffs: boolean = false, diffLines: Set<number> = new Set()) {
    // Split into lines, detect bullets, job titles, dates, etc.
    return text.split(/\n|\r/).map((line, i) => {
      const trimmed = line.trim();
      if (!trimmed) return null;
      // Section header (e.g., EXPERIENCE, EDUCATION)
      if (/^[A-Z][A-Z\s]+$/.test(trimmed) && trimmed.length < 30) {
        return <div key={i} className="mt-6 mb-2 text-lg font-bold tracking-wide text-blue-700 dark:text-blue-300 uppercase">{trimmed}</div>;
      }
      // Job title + company + date (simple heuristic)
      if (/^.+ at .+\s+\(.+\)$/.test(trimmed)) {
        return <div key={i} className="font-semibold text-slate-800 dark:text-slate-100 flex flex-wrap gap-2 items-center mb-1">
          <span>{trimmed}</span>
        </div>;
      }
      // Bullet point
      if (/^[-*•]/.test(trimmed)) {
        return <li key={i} className={`ml-8 list-disc text-base leading-relaxed ${highlightDiffs && diffLines.has(i) ? 'bg-yellow-100 dark:bg-yellow-900/30 font-semibold' : ''}`}>{trimmed.replace(/^[-*•]\s*/, "")}</li>;
      }
      // Date line
      if (/\d{4}/.test(trimmed) && trimmed.length < 20) {
        return <div key={i} className="text-xs text-slate-500 dark:text-slate-400 mb-1">{trimmed}</div>;
      }
      // Default
      return <div key={i} className={`mb-1 text-base ${highlightDiffs && diffLines.has(i) ? 'bg-yellow-100 dark:bg-yellow-900/30 font-semibold' : ''}`}>{trimmed}</div>;
    });
  }

  // Helper to compute line diffs (very basic, for demo)
  function getDiffLines(original: string, suggested: string): Set<number> {
    const origLines = original.split(/\n|\r/).map(l => l.trim());
    const suggLines = suggested.split(/\n|\r/).map(l => l.trim());
    const diff = new Set<number>();
    suggLines.forEach((line, i) => {
      if (line && (!origLines[i] || origLines[i] !== line)) diff.add(i);
    });
    return diff;
  }

  // Enhanced section review UI: card-based, side-by-side, clean formatting
  const renderCritiques = () => (
    <div className="space-y-8">
      {critiques.map((critique, idx) => {
        const isEdited = critique.status === "edited";
        const isAccepted = critique.status === "accepted";
        const ReactMarkdown = require('react-markdown').default;
        return (
          <div key={critique.id} className="bg-white dark:bg-slate-900 rounded-2xl shadow border border-slate-200 dark:border-slate-700 p-6 flex flex-col gap-4">
            <div className="flex items-center gap-3 mb-2">
              <span className="text-lg font-semibold text-blue-700 dark:text-blue-300 flex items-center gap-2">
                {getCategoryIcon(critique.category)}
                {critique.category} Suggestion
              </span>
              <span className={`ml-2 px-2 py-0.5 rounded text-xs font-medium ${isAccepted ? 'bg-green-100 text-green-700' : isEdited ? 'bg-blue-100 text-blue-700' : 'bg-slate-100 text-slate-600'}`}>{critique.status.charAt(0).toUpperCase() + critique.status.slice(1)}</span>
              {critique.impact && <span className="ml-2 px-2 py-0.5 rounded text-xs font-medium bg-yellow-50 text-yellow-700">{critique.impact} Impact</span>}
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Original */}
              <div className="bg-slate-50 dark:bg-slate-800 rounded-xl p-4 border border-slate-100 dark:border-slate-700">
                <h4 className="font-semibold mb-2 text-slate-700 dark:text-slate-300 text-base flex items-center gap-2"><XCircle className="w-4 h-4 text-red-400" />Original</h4>
                <div className="text-sm leading-relaxed whitespace-pre-line prose prose-slate max-w-none">
                  <ReactMarkdown
                    remarkPlugins={[remarkGfm]}
                    components={{
                      h1: (props: React.PropsWithChildren<any>) => <h1 className="text-2xl font-bold mt-8 mb-4 border-b border-slate-200 pb-2" {...props} />,
                      h2: (props: React.PropsWithChildren<any>) => <h2 className="text-xl font-bold mt-6 mb-3 text-blue-700" {...props} />,
                      h3: (props: React.PropsWithChildren<any>) => <h3 className="text-lg font-semibold mt-4 mb-2 text-blue-600" {...props} />,
                      ul: (props: React.PropsWithChildren<any>) => <ul className="list-disc ml-6 mb-2" {...props} />,
                      li: (props: React.PropsWithChildren<any>) => <li className="mb-1" {...props} />,
                      strong: (props: React.PropsWithChildren<any>) => <strong className="font-bold text-slate-900" {...props} />,
                      em: (props: React.PropsWithChildren<any>) => <em className="italic text-slate-700" {...props} />,
                      p: (props: React.PropsWithChildren<any>) => <p className="mb-2" {...props} />,
                    }}
                  >
                    {cleanResumeMarkdown(critique.original)}
                  </ReactMarkdown>
                </div>
              </div>
              {/* Suggested */}
              <div className="bg-green-50 dark:bg-green-900/10 rounded-xl p-4 border border-green-100 dark:border-green-800">
                <h4 className="font-semibold mb-2 text-slate-700 dark:text-slate-300 text-base flex items-center gap-2"><CheckCircle className="w-4 h-4 text-green-500" />Suggested</h4>
                <div className="text-sm leading-relaxed whitespace-pre-line font-medium prose prose-slate max-w-none">
                  <ReactMarkdown
                    remarkPlugins={[remarkGfm]}
                    components={{
                      h1: (props: React.PropsWithChildren<any>) => <h1 className="text-2xl font-bold mt-8 mb-4 border-b border-slate-200 pb-2" {...props} />,
                      h2: (props: React.PropsWithChildren<any>) => <h2 className="text-xl font-bold mt-6 mb-3 text-blue-700" {...props} />,
                      h3: (props: React.PropsWithChildren<any>) => <h3 className="text-lg font-semibold mt-4 mb-2 text-blue-600" {...props} />,
                      ul: (props: React.PropsWithChildren<any>) => <ul className="list-disc ml-6 mb-2" {...props} />,
                      li: (props: React.PropsWithChildren<any>) => <li className="mb-1" {...props} />,
                      strong: (props: React.PropsWithChildren<any>) => <strong className="font-bold text-slate-900" {...props} />,
                      em: (props: React.PropsWithChildren<any>) => <em className="italic text-slate-700" {...props} />,
                      p: (props: React.PropsWithChildren<any>) => <p className="mb-2" {...props} />,
                    }}
                  >
                    {cleanResumeMarkdown(critique.status === "edited" ? critique.editedText || critique.suggested : critique.suggested)}
                  </ReactMarkdown>
                </div>
                {critique.needsClarification && (
                  <Button
                    variant="secondary"
                    className="mt-3 px-3 py-1 text-orange-700 bg-orange-100 hover:bg-orange-200 border border-orange-200"
                    onClick={() => handleClarification(critique.sectionId!, critique.clarificationQuestion!, critique.original)}
                  >
                    <MessageCircle className="w-4 h-4 mr-1" /> Provide Context
                  </Button>
                )}
              </div>
            </div>
            {/* Action buttons */}
            <div className="mt-4 flex flex-wrap gap-2">
              <Button onClick={() => handleAccept(critique.id)} disabled={isAccepted} variant="default" className="min-w-[140px]">Accept Suggestion</Button>
              <Button onClick={() => handleReject(critique.id)} disabled={critique.status === "rejected"} variant="destructive" className="min-w-[100px]">Reject</Button>
              <Button onClick={() => handleEdit(critique.id)} variant="secondary" className="min-w-[80px]">Edit</Button>
              {critique.status !== "pending" && (
                <Button onClick={() => handleUndo(critique.id)} variant="outline" className="min-w-[80px]">Undo</Button>
              )}
            </div>
            {critique.reason && (
              <div className="mt-2 text-xs text-slate-500">Why: {critique.reason}</div>
            )}
          </div>
        );
      })}
    </div>
  );

  // Final resume preview (formatted, scrollable, downloadable)
  const renderFinalResume = () => (
    <Modal open={showFinalResume} onClose={() => setShowFinalResume(false)}>
      <div className="max-h-[80vh] overflow-y-auto p-6 bg-white dark:bg-slate-900 rounded-lg shadow-lg min-w-[350px] max-w-2xl mx-auto border border-slate-200 dark:border-slate-700" id="resume-preview">
        <div className="prose dark:prose-invert max-w-none">
          {finalResume.split(/\n{2,}/).map((section, i) => (
            <div key={i} className="mb-6">
              {section.split(/\n/).map((line, j) =>
                j === 0 ? <h3 key={j} className="mt-0 text-lg font-bold tracking-wide text-blue-700 dark:text-blue-300 uppercase">{line.replace(/^#+\s*/, "")}</h3>
                : line.trim().startsWith("-") ? <li key={j} className="ml-8 list-disc text-base leading-relaxed">{line.replace(/^[-*•]\s*/, "")}</li>
                : <div key={j} className="mb-1 text-base">{line}</div>
              )}
            </div>
          ))}
        </div>
      </div>
      {/* Download as PDF button */}
      <button
        className="mt-4 px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded shadow-lg font-semibold disabled:opacity-60"
        disabled={isPdfLoading}
        onClick={async () => {
          setIsPdfLoading(true);
          try {
            const element = document.getElementById('resume-preview');
            if (element) {
              // @ts-ignore
              const html2pdf = (await import('html2pdf.js')).default;
              await html2pdf().from(element).set({
                margin: 0.5,
                filename: 'ResumeWise-Resume.pdf',
                html2canvas: { scale: 2 },
                jsPDF: { unit: 'in', format: 'letter', orientation: 'portrait' }
              }).save();
            }
          } finally {
            setIsPdfLoading(false);
          }
        }}
      >
        {isPdfLoading ? (
          <span className="flex items-center"><span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin mr-2" />Generating PDF...</span>
        ) : (
          <><Download className="w-5 h-5 mr-2 inline" />Download as PDF</>
        )}
      </button>
    </Modal>
  );

  // Loading spinner overlay
  const LoadingOverlay = ({ show, text }: { show: boolean; text?: string }) => show ? (
    <div className="fixed inset-0 bg-black/30 z-[100] flex flex-col items-center justify-center">
      <div className="w-12 h-12 border-4 border-blue-200 border-t-blue-600 rounded-full animate-spin mb-4" />
      {text && <div className="text-white text-lg font-semibold drop-shadow-lg">{text}</div>}
    </div>
  ) : null;

  // Confetti/checkmark indicator
  const SuccessIndicator = ({ show }: { show: boolean }) => show ? (
    <div className="fixed inset-0 flex items-center justify-center z-[200] pointer-events-none">
      <div className="bg-white/80 dark:bg-slate-900/80 rounded-full p-8 shadow-xl flex flex-col items-center animate-bounce-in">
        <CheckCircle className="w-16 h-16 text-green-500 mb-2 animate-pulse" />
        <div className="text-xl font-bold text-green-700 dark:text-green-300">Resume Ready!</div>
      </div>
    </div>
  ) : null;

  // Tooltip wrapper
  const Tooltip = ({ text, children }: { text: string; children: React.ReactNode }) => (
    <span className="relative group">
      {children}
      <span className="absolute left-1/2 -translate-x-1/2 bottom-full mb-2 px-2 py-1 bg-slate-800 text-white text-xs rounded opacity-0 group-hover:opacity-100 transition pointer-events-none whitespace-nowrap z-50">
        {text}
      </span>
    </span>
  );

  return (
    <div className="min-h-screen font-sans bg-gradient-to-br from-slate-50 via-blue-50/30 to-indigo-50/50 dark:bg-gradient-to-br dark:from-slate-900 dark:via-slate-800 dark:to-slate-900 relative overflow-hidden">
      <LoadingOverlay show={isGeneratingFinal} text="Generating your improved resume..." />
      <SuccessIndicator show={showFinalResume} />
      {/* Subtle background elements */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-40 -right-40 w-80 h-80 bg-gradient-to-br from-blue-500/10 to-indigo-600/10 dark:from-blue-500/5 dark:to-indigo-600/5 rounded-full blur-3xl"></div>
        <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-gradient-to-br from-indigo-500/10 to-blue-600/10 dark:from-indigo-500/5 dark:to-blue-600/5 rounded-full blur-3xl"></div>
      </div>

      {/* Header */}
      <header className="border-b border-slate-200/50 dark:border-slate-700/50 backdrop-blur-xl bg-white/90 dark:bg-slate-900/90 sticky top-0 z-50 shadow-sm">
        <div className="container mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-blue-600 to-indigo-600 flex items-center justify-center shadow-sm">
              <Brain className="w-5 h-5 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-semibold text-slate-900 dark:text-white">
                ResumeWise
              </h1>
            </div>
          </div>
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
            className="rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors duration-200"
            aria-label="Toggle theme"
          >
            <Sun className="h-5 w-5 rotate-0 scale-100 transition-all dark:-rotate-90 dark:scale-0" />
            <Moon className="absolute h-5 w-5 rotate-90 scale-0 transition-all dark:rotate-0 dark:scale-100" />
          </Button>
        </div>
      </header>

      <main className="container mx-auto px-6 py-12 max-w-6xl relative z-10">
        {/* Error Display */}
        {error && (
          <div className="mb-8 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
            <p className="text-red-700 dark:text-red-300 text-sm">{error}</p>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setError(null)}
              className="mt-2 text-red-600 dark:text-red-400 hover:text-red-800 dark:hover:text-red-200"
            >
              Dismiss
            </Button>
          </div>
        )}

        {/* Hero Section */}
        <div className="text-center mb-16">
          <div className="inline-flex items-center gap-2 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg px-4 py-2 mb-6">
            <Brain className="w-4 h-4 text-blue-600 dark:text-blue-400" />
            <span className="text-sm font-medium text-blue-700 dark:text-blue-300">AI-Powered Resume Analysis</span>
          </div>
          <h2 className="text-4xl font-semibold mb-6 text-slate-900 dark:text-white leading-tight">
            Professional Resume Enhancement
          </h2>
          <p className="text-lg text-slate-600 dark:text-slate-300 max-w-2xl mx-auto leading-relaxed">
            Get intelligent, data-driven suggestions to optimize your resume for your target role.
          </p>
        </div>

        {!showResults ? (
          /* Upload Section */
          <div className="grid md:grid-cols-2 gap-8 mb-12">
            {/* Resume Upload */}
            <Card className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 shadow-sm hover:shadow-md transition-shadow duration-200">
              <CardHeader className="pb-4">
                <CardTitle className="flex items-center gap-3 text-lg dark:text-white">
                  <div className="p-2 rounded-lg bg-blue-600 text-white">
                    <FileText className="w-5 h-5" />
                  </div>
                  Upload Resume
                </CardTitle>
                <CardDescription className="text-slate-600 dark:text-slate-400">
                  Upload your resume in PDF, DOCX, DOC, or TXT format
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="border-2 border-dashed border-slate-300 dark:border-slate-600 rounded-lg p-8 text-center hover:border-blue-400 dark:hover:border-blue-500 transition-colors duration-200 hover:bg-slate-50 dark:hover:bg-slate-800/50">
                  <input
                    type="file"
                    accept=".pdf,.txt,.doc,.docx"
                    onChange={handleFileUpload}
                    className="hidden"
                    id="resume-upload"
                  />
                  <label htmlFor="resume-upload" className="cursor-pointer block">
                    <div className="w-12 h-12 mx-auto mb-4 rounded-lg bg-blue-600 flex items-center justify-center text-white">
                      <Upload className="w-6 h-6" />
                    </div>
                    <p className="text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                      {resumeFile ? (
                        <span className="text-green-600 dark:text-green-400 flex items-center justify-center gap-2">
                          <CheckCircle className="w-4 h-4" />
                          {resumeFile.name}
                        </span>
                      ) : (
                        "Click to upload or drag and drop"
                      )}
                    </p>
                    <p className="text-xs text-slate-500 dark:text-slate-400">PDF, DOCX, DOC, TXT up to 10MB</p>
                  </label>
                </div>
              </CardContent>
            </Card>

            {/* Job Description */}
            <Card className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 shadow-sm hover:shadow-md transition-shadow duration-200">
              <CardHeader className="pb-4">
                <CardTitle className="flex items-center gap-3 text-lg dark:text-white">
                  <div className="p-2 rounded-lg bg-indigo-600 text-white">
                    <Briefcase className="w-5 h-5" />
                  </div>
                  Job Description
                </CardTitle>
                <CardDescription className="text-slate-600 dark:text-slate-400">
                  Paste the job description you're applying for
                </CardDescription>
              </CardHeader>
              <CardContent>
                <Textarea
                  placeholder="Paste the job description here to get tailored suggestions..."
                  value={jobDescription}
                  onChange={(e) => setJobDescription(e.target.value)}
                  className="min-h-[200px] resize-none bg-white dark:bg-slate-800 border-slate-200 dark:border-slate-600 focus:border-blue-500 dark:focus:border-blue-400 transition-colors duration-200 rounded-lg dark:text-white dark:placeholder:text-slate-400"
                />
              </CardContent>
            </Card>
          </div>
        ) : null}

        {/* Submit Button */}
        {!showResults && (
          <div className="text-center mb-8">
            <Button
              onClick={handleAnalyze}
              disabled={!resumeFile || !jobDescription.trim() || isAnalyzing}
              size="lg"
              className="bg-blue-600 hover:bg-blue-700 text-white px-8 py-3 rounded-lg shadow-sm hover:shadow-md transition-all duration-200 text-base font-medium"
            >
              {isAnalyzing ? (
                <>
                  <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin mr-3" />
                  Analyzing Resume...
                </>
              ) : (
                <>
                  <Brain className="w-5 h-5 mr-3" />
                  Analyze Resume
                </>
              )}
            </Button>
          </div>
        )}

        {/* Results Section */}
        {showResults && (
          <div className="space-y-8">
            <div className="flex items-center justify-between border-b border-slate-200 dark:border-slate-700 pb-6 mb-6">
              <div>
                <h3 className="text-3xl font-semibold text-slate-900 dark:text-white mb-2 tracking-tight">Analysis Results</h3>
                <p className="text-slate-600 dark:text-slate-400">Found {critiques.length} suggestions to improve your resume</p>
                {analysisData && (analysisData as any).summary && (
                  <div className="mt-2 flex gap-4 text-sm text-slate-500 dark:text-slate-400">
                    <span>Overall Score: {((analysisData as any).summary.overall_score || 0).toFixed(1)}/10</span>
                    <span>Strong Sections: {(analysisData as any).summary.strong_sections || 0}</span>
                    <span>Needs Improvement: {(analysisData as any).summary.needs_improvement || 0}</span>
                  </div>
                )}
                
                {/* Progress Tracking */}
                <div className="mt-4 space-y-2">
                  <div className="flex items-center gap-4 text-sm">
                    <span className="flex items-center gap-2">
                      <div className="w-3 h-3 rounded-full bg-slate-300 dark:bg-slate-600"></div>
                      Pending: {critiques.filter(c => c.status === "pending").length}
                    </span>
                    <span className="flex items-center gap-2">
                      <div className="w-3 h-3 rounded-full bg-green-500"></div>
                      Accepted: {critiques.filter(c => c.status === "accepted").length}
                    </span>
                    <span className="flex items-center gap-2">
                      <div className="w-3 h-3 rounded-full bg-blue-500"></div>
                      Edited: {critiques.filter(c => c.status === "edited").length}
                    </span>
                    <span className="flex items-center gap-2">
                      <div className="w-3 h-3 rounded-full bg-red-500"></div>
                      Rejected: {critiques.filter(c => c.status === "rejected").length}
                    </span>
                  </div>
                  <div className="w-full bg-slate-200 dark:bg-slate-700 rounded-full h-2">
                    <div 
                      className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                      style={{ 
                        width: `${((critiques.filter(c => c.status === "accepted" || c.status === "edited").length) / critiques.length) * 100}%` 
                      }}
                    ></div>
                  </div>
                </div>
              </div>
              <div className="flex gap-3">
                <Button
                  onClick={handleGenerateFinalResume}
                  disabled={isGeneratingFinal || critiques.filter(c => c.status === "pending").length > 0}
                  size="lg"
                  className="bg-blue-600 hover:bg-blue-700 text-white shadow-lg hover:shadow-xl transition-all duration-200 rounded-xl px-6 py-3 font-semibold"
                >
                  {isGeneratingFinal ? (
                    <>
                      <RefreshCw className="w-5 h-5 mr-2 animate-spin" />
                      Generating...
                    </>
                  ) : (
                    <>
                      <Download className="w-5 h-5 mr-2" />
                      Generate Final Resume
                    </>
                  )}
                </Button>
                <Button
                  variant="outline"
                  onClick={() => {
                    setShowResults(false)
                    setCritiques([])
                    setResumeFile(null)
                    setJobDescription("")
                    setAnalysisData(null)
                    setError(null)
                  }}
                  className="border-slate-200 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-800 dark:text-white transition-colors duration-200 rounded-xl px-6 py-3 font-semibold"
                >
                  Start New Analysis
                </Button>
              </div>
            </div>

            {renderCritiques()}

            {critiques.length === 0 && (
              <Card className="bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800 shadow-sm">
                <CardContent className="p-12 text-center">
                  <div className="w-16 h-16 mx-auto mb-6 rounded-lg bg-green-600 flex items-center justify-center text-white">
                    <CheckCircle className="w-8 h-8" />
                  </div>
                  <h3 className="text-2xl font-semibold mb-3 text-green-800 dark:text-green-300">Review Complete</h3>
                  <p className="text-green-700 dark:text-green-400 text-lg">
                    You've reviewed all suggestions. Your resume is ready for final generation.
                  </p>
                </CardContent>
              </Card>
            )}
          </div>
        )}
      </main>

      {/* Clarification Modal */}
      {clarificationModal.isOpen && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <Card className="w-full max-w-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 shadow-lg">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-lg dark:text-white">
                <MessageCircle className="w-5 h-5 text-orange-500" />
                Provide Additional Details
              </CardTitle>
              <CardDescription className="text-slate-600 dark:text-slate-400">
                Help us improve this bullet point with more specific information
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div>
                <h4 className="text-sm font-semibold text-slate-600 dark:text-slate-400 mb-2">Original Bullet:</h4>
                <p className="text-sm text-slate-700 dark:text-slate-300 bg-slate-50 dark:bg-slate-800 p-3 rounded-lg">
                  {clarificationModal.originalText}
                </p>
              </div>
              
              <div>
                <h4 className="text-sm font-semibold text-slate-600 dark:text-slate-400 mb-2">Question:</h4>
                <p className="text-sm text-slate-700 dark:text-slate-300 bg-orange-50 dark:bg-orange-900/20 p-3 rounded-lg border border-orange-200 dark:border-orange-800">
                  {clarificationModal.question}
                </p>
              </div>
              
              <div>
                <h4 className="text-sm font-semibold text-slate-600 dark:text-slate-400 mb-2">Your Response:</h4>
                <Textarea
                  value={clarificationModal.userResponse}
                  onChange={(e) => setClarificationModal(prev => ({ ...prev, userResponse: e.target.value }))}
                  placeholder="Provide specific details, metrics, or context..."
                  className="min-h-[100px] resize-none bg-white dark:bg-slate-800 border-slate-200 dark:border-slate-600 focus:border-orange-500 dark:focus:border-orange-400 transition-colors duration-200 rounded-lg dark:text-white dark:placeholder:text-slate-400"
                />
              </div>
              
              <div className="flex gap-3 justify-end">
                <Button
                  variant="outline"
                  onClick={() => setClarificationModal(prev => ({ ...prev, isOpen: false }))}
                  disabled={isProcessingClarification}
                  className="border-slate-200 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-800 dark:text-white"
                >
                  Cancel
                </Button>
                <Button
                  onClick={handleSubmitClarification}
                  disabled={!clarificationModal.userResponse.trim() || isProcessingClarification}
                  className="bg-orange-600 hover:bg-orange-700 text-white shadow-sm hover:shadow-md transition-all duration-200"
                >
                  {isProcessingClarification ? (
                    <>
                      <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                      Processing...
                    </>
                  ) : (
                    <>
                      <Brain className="w-4 h-4 mr-2" />
                      Submit & Improve
                    </>
                  )}
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Edit Modal */}
      {editModal.isOpen && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <Card className="w-full max-w-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 shadow-lg">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-lg dark:text-white">
                <Edit3 className="w-5 h-5 text-blue-500" />
                Edit Bullet Point
              </CardTitle>
              <CardDescription className="text-slate-600 dark:text-slate-400">
                Customize the suggested improvement to better match your experience
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div>
                <h4 className="text-sm font-semibold text-slate-600 dark:text-slate-400 mb-2">Original:</h4>
                <p className="text-sm text-slate-700 dark:text-slate-300 bg-slate-50 dark:bg-slate-800 p-3 rounded-lg">
                  {editModal.originalText}
                </p>
              </div>
              
              <div>
                <h4 className="text-sm font-semibold text-slate-600 dark:text-slate-400 mb-2">AI Suggestion:</h4>
                <p className="text-sm text-slate-700 dark:text-slate-300 bg-blue-50 dark:bg-blue-900/20 p-3 rounded-lg border border-blue-200 dark:border-blue-800">
                  {editModal.suggestedText}
                </p>
              </div>
              
              <div>
                <h4 className="text-sm font-semibold text-slate-600 dark:text-slate-400 mb-2">Your Edit:</h4>
                <Textarea
                  value={editModal.editedText}
                  onChange={(e) => setEditModal(prev => ({ ...prev, editedText: e.target.value }))}
                  placeholder="Edit the suggestion to better match your experience..."
                  className="min-h-[120px] resize-none bg-white dark:bg-slate-800 border-slate-200 dark:border-slate-600 focus:border-blue-500 dark:focus:border-blue-400 transition-colors duration-200 rounded-lg dark:text-white dark:placeholder:text-slate-400"
                />
              </div>
              
              <div className="flex gap-3 justify-end">
                <Button
                  variant="outline"
                  onClick={() => setEditModal({ isOpen: false, critiqueId: "", originalText: "", suggestedText: "", editedText: "" })}
                  className="border-slate-200 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-800 dark:text-white"
                >
                  Cancel
                </Button>
                <Button
                  onClick={handleSaveEdit}
                  disabled={!editModal.editedText.trim()}
                  className="bg-blue-600 hover:bg-blue-700 text-white shadow-sm hover:shadow-md transition-all duration-200"
                >
                  <CheckCircle className="w-4 h-4 mr-2" />
                  Save Edit
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {renderFinalResume()}

      {/* Sticky action bar for final resume preview/download */}
      {showFinalResume && (
        <div className="fixed bottom-0 left-0 w-full bg-white dark:bg-slate-900 border-t border-slate-200 dark:border-slate-700 shadow-lg z-50 flex items-center justify-center py-4 gap-4">
          <Tooltip text="Download your improved resume as a PDF (coming soon)">
            <Button className="bg-blue-600 hover:bg-blue-700 text-white rounded-xl px-6 py-3 font-semibold shadow-lg focus:outline-none focus:ring-2 focus:ring-blue-500" onClick={() => setShowFinalResume(false)} aria-label="Close resume preview">
              Close Preview
            </Button>
          </Tooltip>
          <Tooltip text="Download your improved resume as a PDF (coming soon)">
            <Button className="bg-green-600 hover:bg-green-700 text-white rounded-xl px-6 py-3 font-semibold shadow-lg focus:outline-none focus:ring-2 focus:ring-green-500" onClick={() => {/* TODO: implement download */}} aria-label="Download as PDF">
              <Download className="w-5 h-5 mr-2" />
              Download as PDF
            </Button>
          </Tooltip>
        </div>
      )}

      {/* Footer */}
      <footer className="border-t border-slate-200 dark:border-slate-700 mt-20 bg-white dark:bg-slate-900">
        <div className="container mx-auto px-6 py-8 text-center">
          <p className="text-sm text-slate-600 dark:text-slate-400">
            ResumeWise • Professional Resume Enhancement
          </p>
        </div>
      </footer>
    </div>
  )
}
