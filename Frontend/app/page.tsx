"use client"

import React, { useState, useEffect, useRef } from "react"
import {
  Upload,
  FileText,
  Briefcase,
  Brain,
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
  AlertCircle,
  ChevronRight,
  Loader,
  X,
  Check,
  MessageSquare,
  HelpCircle,
  Loader2,
  Edit2,
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { 
  Dialog, 
  DialogContent, 
  DialogDescription, 
  DialogHeader, 
  DialogTitle,
  DialogFooter
} from "@/components/ui/dialog"
import { useTheme } from "next-themes"
import { useRouter } from 'next/navigation'
import { 
  resumeWiseAPI, 
  type AnalysisStartResponse, 
  type SectionAnalysis, 
  type SectionData,
  type JobAnalysis,
  APIError,
  ValidationError,
  NotFoundError
} from "@/lib/api"
import { Input } from "@/components/ui/input"

// Types and Interfaces
interface AnalysisSession {
  sessionId: string
  sections: Record<string, SectionData>
  jobAnalysis: JobAnalysis
  analysisOrder: string[]
  currentSectionIndex: number
  sectionAnalyses: Record<string, SectionAnalysis>
  acceptedChanges: Record<string, boolean>
}

interface ClarificationModal {
  isOpen: boolean
  sectionType: string
  question: string
  context: string
  reason: string
  userResponse: string
}

// Section type mapping for display
const SECTION_DISPLAY_NAMES: Record<string, string> = {
  'skills': 'Technical Skills',
  'education': 'Education',
  'experience': 'Professional Experience',
  'projects': 'Projects',
  'contact_info': 'Contact Information',
  'summary': 'Professional Summary',
  'certifications': 'Certifications'
}

const SECTION_ICONS: Record<string, React.ComponentType<{ className?: string }>> = {
  'skills': Code,
  'education': GraduationCap,
  'experience': Building2,
  'projects': Sparkles,
  'contact_info': Users,
  'summary': FileText,
  'certifications': Shield
}

export default function ResumeWise() {
  // State management
  const [resumeFile, setResumeFile] = useState<File | null>(null)
  const [jobDescription, setJobDescription] = useState("")
  const [isStarting, setIsStarting] = useState(false)
  const [analysisSession, setAnalysisSession] = useState<AnalysisSession | null>(null)
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [clarificationModal, setClarificationModal] = useState<ClarificationModal>({
    isOpen: false,
    sectionType: "",
    question: "",
    context: "",
    reason: "",
    userResponse: ""
  })
  const [isProcessingClarification, setIsProcessingClarification] = useState(false)
  const [showFinalResume, setShowFinalResume] = useState(false)
  const [finalResume, setFinalResume] = useState("")
  const [isGeneratingFinal, setIsGeneratingFinal] = useState(false)
  const [clarificationInput, setClarificationInput] = useState("")
  const [isSubmittingClarification, setIsSubmittingClarification] = useState(false)
  
  // New state for undo functionality
  const [undoHistory, setUndoHistory] = useState<Record<string, boolean | null>>({})
  const [fileValidationError, setFileValidationError] = useState("")
  
  const { theme } = useTheme()
  const router = useRouter()

  const validateResumeFile = (file: File): string | null => {
    // Check file type
    const allowedTypes = [
      'application/pdf',
      'application/msword',
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      'text/plain'
    ]
    
    const allowedExtensions = ['.pdf', '.doc', '.docx', '.txt']
    const fileExtension = '.' + file.name.split('.').pop()?.toLowerCase()
    
    if (!allowedTypes.includes(file.type) && !allowedExtensions.includes(fileExtension)) {
      return "Please upload a valid resume file in PDF, DOC, DOCX, or TXT format."
    }
    
    // Check file size (max 10MB)
    const maxSize = 10 * 1024 * 1024 // 10MB in bytes
    if (file.size > maxSize) {
      return "File size must be less than 10MB. Please compress your resume or use a different format."
    }
    
    // Check if file is too small (likely empty)
    if (file.size < 100) {
      return "The uploaded file appears to be empty. Please upload a valid resume document."
    }
    
    return null // No validation errors
  }

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (file) {
      const validationError = validateResumeFile(file)
      if (validationError) {
        setFileValidationError(validationError)
        setResumeFile(null)
        // Reset the input
        event.target.value = ''
      } else {
        setFileValidationError("")
      setResumeFile(file)
      }
    }
  }

  // 🔍 DEBUG: Monitor analysisSession state changes
  useEffect(() => {
    if (analysisSession) {
      console.log("🔄 ANALYSIS SESSION STATE UPDATED:")
      console.log("Session ID:", analysisSession.sessionId)
      console.log("Sections keys:", Object.keys(analysisSession.sections))
      console.log("Analysis order:", analysisSession.analysisOrder)
      console.log("Section analyses keys:", Object.keys(analysisSession.sectionAnalyses))
      
      // Log each section in detail
      Object.entries(analysisSession.sections).forEach(([sectionType, sectionData]) => {
        console.log(`📄 Session Section ${sectionType}:`)
        console.log(`  - Type: ${typeof sectionData}`)
        console.log(`  - Keys: ${Object.keys(sectionData)}`)
        console.log(`  - Content length: ${sectionData.content?.length || 0}`)
        if (sectionData.content) {
          console.log(`  - Content preview: "${sectionData.content.substring(0, 100)}..."`)
        }
      })
    } else {
      console.log("❌ analysisSession is null/undefined")
    }
  }, [analysisSession])

  // Handlers
  const handleStartAnalysis = async () => {
    if (!resumeFile || !jobDescription.trim()) {
      setError("Please provide both a resume file and job description")
      return
    }

    setIsStarting(true)
    setError(null)

    try {
      console.log("🚀 Starting analysis with file:", resumeFile.name)
      const response = await resumeWiseAPI.startAnalysis(resumeFile, jobDescription)
      
      // 🔍 COMPREHENSIVE DEBUG: Full response analysis
      console.log("=== COMPREHENSIVE DEBUG: API Response ===")
      console.log("Raw response:", response)
      console.log("Response type:", typeof response)
      console.log("Response keys:", Object.keys(response))
      console.log("Success:", response.success)
      console.log("Session ID:", response.session_id)
      console.log("Sections type:", typeof response.sections)
      console.log("Sections keys:", response.sections ? Object.keys(response.sections) : "NO SECTIONS")
      
      // Check each section in detail
      if (response.sections) {
        console.log("📋 SECTION-BY-SECTION ANALYSIS:")
        Object.entries(response.sections).forEach(([sectionType, sectionData]) => {
          console.log(`\n🔍 Section: ${sectionType}`)
          console.log(`  - Type: ${typeof sectionData}`)
          console.log(`  - Keys: ${Object.keys(sectionData as any)}`)
          console.log(`  - Has content field: ${'content' in (sectionData as any)}`)
          console.log(`  - Content type: ${typeof (sectionData as any).content}`)
          console.log(`  - Content length: ${(sectionData as any).content?.length || 0}`)
          if ((sectionData as any).content) {
            console.log(`  - Content preview: "${(sectionData as any).content.substring(0, 150)}..."`)
        } else {
            console.log(`  - ❌ NO CONTENT FOUND`)
          }
        })
      } else {
        console.log("❌ NO SECTIONS OBJECT IN RESPONSE")
      }
      
      // Check section analyses
      console.log("\n📊 SECTION ANALYSES:")
      console.log("Section analyses type:", typeof response.section_analyses)
      console.log("Section analyses keys:", response.section_analyses ? Object.keys(response.section_analyses) : "NO ANALYSES")
      
      if (response.section_analyses) {
        Object.entries(response.section_analyses).forEach(([sectionType, analysis]) => {
          console.log(`\n📈 Analysis: ${sectionType}`)
          console.log(`  - Type: ${typeof analysis}`)
          console.log(`  - Keys: ${Object.keys(analysis as any)}`)
          console.log(`  - Original content length: ${(analysis as any).original_content?.length || 0}`)
          console.log(`  - Has improved content: ${!!(analysis as any).improved_content}`)
          console.log(`  - Score: ${(analysis as any).score}`)
        })
      }
      
      if (response.success && response.session_id) {
        // Set up the complete analysis session with ALL results
        const newSession = {
          sessionId: response.session_id,
          sections: response.sections || {},
          jobAnalysis: response.job_analysis || {
            keywords: [],
            requirements: [],
            experience_level: "mid",
            key_technologies: [],
            soft_skills: [],
            hard_skills: [],
            priorities: []
          },
          analysisOrder: response.analysis_order || [],
          currentSectionIndex: 0,
          sectionAnalyses: response.section_analyses || {},
          acceptedChanges: {}
        }
        
        console.log("💾 STORING SESSION DATA:")
        console.log("Session object:", newSession)
        console.log("Session sections keys:", Object.keys(newSession.sections))
        console.log("Session analyses keys:", Object.keys(newSession.sectionAnalyses))
        
        setAnalysisSession(newSession)
        
        // Verify the state was set correctly
        setTimeout(() => {
          console.log("✅ VERIFICATION: Checking stored state after 100ms")
          // This will be logged after state update
        }, 100)
        
      } else {
        setError(response.error || "Failed to start analysis")
      }
    } catch (error) {
      console.error("💥 ERROR in handleStartAnalysis:", error)
      if (error instanceof ValidationError) {
        setError(`Invalid input: ${error.message}`)
      } else if (error instanceof APIError) {
        setError(`Analysis failed: ${error.message}`)
      } else {
        setError("An unexpected error occurred. Please try again.")
      }
    } finally {
      setIsStarting(false)
    }
  }

  const handleAnalyzeSection = async (sectionType: string) => {
    if (!analysisSession) return

    setIsAnalyzing(true)
    setError(null)

    try {
      const response = await resumeWiseAPI.analyzeSection(analysisSession.sessionId, sectionType)
      
      if (response.success && response.analysis) {
        const analysis = response.analysis
        
        // Update session with analysis
        setAnalysisSession(prev => ({
          ...prev!,
          sectionAnalyses: {
            ...prev!.sectionAnalyses,
            [sectionType]: analysis
          }
        }))

        // Only show clarification modal if specifically requested AND user response needed
        if (analysis.needs_clarification && analysis.clarification_request && !analysis.improved_content) {
    setClarificationModal({
      isOpen: true,
            sectionType,
            question: analysis.clarification_request.question,
            context: analysis.clarification_request.context,
            reason: analysis.clarification_request.reason,
            userResponse: ""
          })
        }
      } else {
        setError(response.error || "Failed to analyze section")
      }
    } catch (error) {
      if (error instanceof NotFoundError) {
        setError("Analysis session not found. Please start a new analysis.")
      } else if (error instanceof APIError) {
        setError(`Section analysis failed: ${error.message}`)
      } else {
        setError("An unexpected error occurred during analysis.")
      }
    } finally {
      setIsAnalyzing(false)
    }
  }

  const handleSubmitClarification = async () => {
    if (!analysisSession || !clarificationModal.userResponse.trim()) return

    setIsSubmittingClarification(true)

    try {
      const response = await resumeWiseAPI.provideClarification(
        analysisSession.sessionId,
        clarificationModal.sectionType,
        clarificationModal.userResponse
      )

      if (response.success && response.analysis) {
        // Update session with new analysis
        setAnalysisSession(prev => ({
          ...prev!,
          sectionAnalyses: {
            ...prev!.sectionAnalyses,
            [clarificationModal.sectionType]: response.analysis!
          }
        }))

        // Close clarification modal
        setClarificationModal({
          isOpen: false,
          sectionType: "",
          question: "",
          context: "",
          reason: "",
          userResponse: ""
        })
      } else {
        setError(response.error || "Failed to process clarification")
      }
    } catch (error) {
      if (error instanceof APIError) {
        setError(`Clarification failed: ${error.message}`)
      } else {
        setError("An unexpected error occurred during clarification.")
      }
    } finally {
      setIsSubmittingClarification(false)
    }
  }

  const handleAcceptChanges = async (sectionType: string, accepted: boolean) => {
    if (!analysisSession) return

    // Store previous state for undo
    const previousState = analysisSession.acceptedChanges[sectionType] ?? null
    setUndoHistory(prev => ({
      ...prev,
      [sectionType]: previousState
    }))

    // Update current state
    setAnalysisSession(prev => {
      if (!prev) return null
      return {
        ...prev,
        acceptedChanges: {
          ...prev.acceptedChanges,
          [sectionType]: accepted
        }
      }
    })
  }

  const handleUndoChanges = (sectionType: string) => {
    if (!analysisSession) return

    const previousState = undoHistory[sectionType]
    
    setAnalysisSession(prev => {
      if (!prev) return null
      const newAcceptedChanges = { ...prev.acceptedChanges }
      
      if (previousState === null) {
        delete newAcceptedChanges[sectionType]
      } else {
        newAcceptedChanges[sectionType] = previousState
      }
      
      return {
        ...prev,
        acceptedChanges: newAcceptedChanges
      }
    })

    // Clear undo history for this section
    setUndoHistory(prev => {
      const newHistory = { ...prev }
      delete newHistory[sectionType]
      return newHistory
    })
  }

  const handleGenerateFinalResume = async () => {
    if (!analysisSession) return

    setIsGeneratingFinal(true)
    setError(null)

    try {
      const response = await resumeWiseAPI.generateFinalResume(analysisSession.sessionId)
      
      if (response.success && response.final_resume) {
        setFinalResume(response.final_resume)
        
        // 🔧 ENHANCED: Store detailed session data for preview page
        const sessionData = {
          sessionId: analysisSession.sessionId,
          sections: analysisSession.sections,
          sectionAnalyses: analysisSession.sectionAnalyses,
          acceptedChanges: analysisSession.acceptedChanges,
          analysisOrder: analysisSession.analysisOrder,
          finalResume: response.final_resume
        }
        
        // Store in sessionStorage for preview page access
        window.sessionStorage.setItem("analysis_session_data", JSON.stringify(sessionData))
        window.sessionStorage.setItem("last_analysis_id", analysisSession.sessionId)
        window.sessionStorage.setItem("last_final_resume", response.final_resume)
        
        setShowFinalResume(true)
      } else {
        setError(response.error || "Failed to generate final resume")
      }
    } catch (error) {
      if (error instanceof APIError) {
        setError(`Resume generation failed: ${error.message}`)
      } else {
        setError("An unexpected error occurred during resume generation.")
      }
    } finally {
      setIsGeneratingFinal(false)
    }
  }

  const handleClarificationSubmit = async (sectionType: string) => {
    if (!analysisSession || !clarificationInput.trim()) return

    setIsSubmittingClarification(true)

    try {
      const response = await resumeWiseAPI.provideClarification(
        analysisSession.sessionId,
        sectionType,
        clarificationInput
      )

      if (response.success && response.analysis) {
        setAnalysisSession(prev => ({
          ...prev!,
          sectionAnalyses: {
            ...prev!.sectionAnalyses,
            [sectionType]: response.analysis!
          }
        }))
        setClarificationInput("")
      } else {
        setError(response.error || "Failed to submit clarification")
      }
    } catch (error) {
      if (error instanceof APIError) {
        setError(`Clarification failed: ${error.message}`)
      } else {
        setError("An unexpected error occurred during clarification.")
      }
    } finally {
      setIsSubmittingClarification(false)
    }
  }

  const downloadResume = () => {
    const element = document.createElement("a")
    const file = new Blob([finalResume], { type: "text/plain" })
    element.href = URL.createObjectURL(file)
    element.download = "ResumeWise-Resume.txt"
    document.body.appendChild(element)
    element.click()
    document.body.removeChild(element)
  }

  const resetAnalysis = () => {
    setAnalysisSession(null)
    setShowFinalResume(false)
    setFinalResume("")
    setResumeFile(null)
    setJobDescription("")
    setError(null)
  }

  // Render functions
  const renderUploadSection = () => (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      {/* Professional Header */}
      <div className="border-b border-slate-700/50 bg-slate-900/80 backdrop-blur-xl">
        <div className="max-w-6xl mx-auto px-6 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 bg-gradient-to-r from-slate-600 to-slate-700 rounded-xl flex items-center justify-center shadow-lg border border-slate-600/30">
                <span className="text-white font-bold text-xl">RW</span>
              </div>
              <div>
                <h1 className="text-2xl font-bold text-slate-100">ResumeWise</h1>
                <p className="text-slate-400 text-sm">Professional Resume Analysis</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-5xl mx-auto px-6 py-16">
        <div className="text-center mb-12">
          <h2 className="text-4xl lg:text-5xl font-bold text-slate-100 mb-6 leading-tight">
            Resume Analysis System
          </h2>
          <p className="text-xl text-slate-300 max-w-3xl mx-auto leading-relaxed">
            Upload your resume and provide the target job description for comprehensive analysis and optimization.
          </p>
        </div>

        {/* Upload Interface - Fixed Alignment */}
        <div className="bg-slate-800/50 backdrop-blur-xl rounded-3xl border border-slate-700/50 shadow-2xl overflow-hidden">
          <div className="p-8 lg:p-12">
            <div className="grid lg:grid-cols-2 gap-12">
              {/* Resume Upload - Improved Layout */}
              <div className="space-y-6 flex flex-col">
                <div className="text-center mb-8">
                  <div className="w-16 h-16 bg-gradient-to-r from-slate-600 to-slate-700 rounded-2xl flex items-center justify-center mx-auto mb-4 shadow-lg border border-slate-600/30">
                    <Upload className="w-8 h-8 text-slate-200" />
        </div>
                  <h3 className="text-xl font-semibold text-slate-100 mb-3">Resume Upload</h3>
                  <p className="text-slate-400">
                    Upload your current resume for analysis
                  </p>
      </div>
                
                <div className="flex-1 flex flex-col">
                  <input
                    type="file"
                    accept=".pdf,.txt,.doc,.docx"
                    onChange={handleFileUpload}
                    className="hidden"
                    id="resume-upload"
                  />
                  <label
                    htmlFor="resume-upload"
                    className={`
                      relative block w-full h-64 border-2 border-dashed rounded-2xl cursor-pointer transition-all duration-300 group flex flex-col items-center justify-center
                      ${resumeFile 
                        ? 'border-emerald-500/50 bg-emerald-500/10 hover:bg-emerald-500/20' 
                        : 'border-slate-600/50 bg-slate-700/30 hover:bg-slate-700/50 hover:border-slate-500/50'
                      }
                    `}
                  >
                    <div className="text-center">
                      {resumeFile ? (
                        <>
                          <CheckCircle className="w-12 h-12 text-emerald-400 mx-auto mb-4 group-hover:scale-110 transition-transform" />
                          <div className="text-lg font-semibold text-emerald-300 mb-2">
                            File Successfully Uploaded
                          </div>
                          <div className="text-emerald-400/80 text-sm font-medium">
                            {resumeFile.name}
                          </div>
                          <div className="text-slate-400 text-sm mt-1">
                            {(resumeFile.size / 1024 / 1024).toFixed(1)} MB
                          </div>
                        </>
                      ) : (
                        <>
                          <Upload className="w-12 h-12 text-slate-400 mx-auto mb-4 group-hover:text-slate-300 group-hover:scale-110 transition-all" />
                          <div className="text-lg font-semibold text-slate-200 mb-2">
                            Select Resume File
                          </div>
                          <div className="text-slate-400 text-sm">
                            PDF, DOC, DOCX, or TXT • Maximum 10MB
                          </div>
                        </>
                      )}
                    </div>
                  </label>
                </div>

                {resumeFile && (
                  <div className="text-center mt-4">
                    <button
                      onClick={() => setResumeFile(null)}
                      className="text-red-400 hover:text-red-300 text-sm transition-colors underline"
                    >
                      Remove File
                    </button>
                  </div>
                )}

                {/* File Validation Error */}
                {fileValidationError && (
                  <div className="mt-4 p-4 bg-red-500/10 border border-red-500/20 rounded-xl">
                    <div className="flex items-center gap-2 text-red-300">
                      <AlertCircle className="w-5 h-5" />
                      <span className="font-medium">{fileValidationError}</span>
        </div>
                  </div>
                )}
              </div>

              {/* Job Description - Improved Layout */}
              <div className="space-y-6 flex flex-col">
                <div className="text-center mb-8">
                  <div className="w-16 h-16 bg-gradient-to-r from-slate-600 to-slate-700 rounded-2xl flex items-center justify-center mx-auto mb-4 shadow-lg border border-slate-600/30">
                    <Briefcase className="w-8 h-8 text-slate-200" />
                  </div>
                  <h3 className="text-xl font-semibold text-slate-100 mb-3">Target Position</h3>
                  <p className="text-slate-400">
                    Provide the job description for targeted analysis
                  </p>
                </div>

                <div className="flex-1 flex flex-col">
                  <Textarea
                    placeholder="Paste the complete job description including requirements, responsibilities, and qualifications..."
                    value={jobDescription}
                    onChange={(e) => setJobDescription(e.target.value)}
                    className="flex-1 h-64 resize-none bg-slate-700/50 border-slate-600/50 text-slate-100 placeholder:text-slate-400 focus:border-slate-500/50 focus:ring-slate-500/20 rounded-2xl p-6 text-base backdrop-blur-sm transition-all duration-200 overflow-y-auto scrollbar-thin scrollbar-track-slate-800 scrollbar-thumb-slate-600"
                  />
                </div>

                {jobDescription && (
                  <div className="p-4 bg-slate-700/30 rounded-xl border border-slate-600/30 mt-4">
                    <div className="flex items-center gap-2 text-slate-300">
                      <CheckCircle className="w-4 h-4" />
                      <span className="text-sm font-medium">Job description ready for analysis</span>
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Error Display */}
            {error && (
              <div className="mt-8 p-4 bg-red-500/10 border border-red-500/20 rounded-xl">
                <div className="flex items-center gap-2 text-red-300">
                  <AlertCircle className="w-5 h-5" />
                  <span className="font-medium">{error}</span>
                </div>
          </div>
            )}

            {/* Start Analysis Button - Improved Alignment */}
            <div className="mt-12 flex flex-col items-center">
              <Button
                onClick={handleStartAnalysis}
                disabled={!resumeFile || !jobDescription.trim() || isStarting}
                size="lg"
                className="bg-gradient-to-r from-slate-700 to-slate-800 hover:from-slate-600 hover:to-slate-700 text-white shadow-xl hover:shadow-2xl transition-all duration-300 disabled:opacity-50 px-12 py-4 text-lg font-semibold rounded-2xl border border-slate-600/30"
              >
                {isStarting ? (
                  <>
                    <Loader className="w-6 h-6 mr-3 animate-spin" />
                    Analyzing Resume...
                  </>
                ) : (
                  <>
                    <BarChart3 className="w-6 h-6 mr-3" />
                    Begin Analysis
                  </>
                )}
              </Button>
              
              {resumeFile && jobDescription && !isStarting && (
                <p className="text-slate-400 text-sm mt-4">
                  Ready to analyze your resume
                </p>
              )}
      </div>
          </div>
        </div>
      </div>
    </div>
  )

  const renderSectionAnalysis = () => {
    if (!analysisSession) return null

    const { analysisOrder, sectionAnalyses, sections, jobAnalysis } = analysisSession
    const analyzedCount = Object.keys(sectionAnalyses).length
    const totalCount = analysisOrder.length

    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
        {/* Professional Header */}
        <div className="border-b border-slate-700/50 bg-slate-900/80 backdrop-blur-xl">
          <div className="max-w-7xl mx-auto px-6 py-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 bg-gradient-to-r from-slate-600 to-slate-700 rounded-xl flex items-center justify-center shadow-lg border border-slate-600/30">
                  <span className="text-white font-bold text-xl">RW</span>
                </div>
                <div>
                  <h1 className="text-2xl font-bold text-slate-100">ResumeWise</h1>
                  <p className="text-slate-400 text-sm">Professional Resume Analysis</p>
                </div>
              </div>
              <div className="flex items-center gap-4">
                <div className="px-4 py-2 bg-slate-700/50 backdrop-blur-sm rounded-lg border border-slate-600/30">
                  <span className="text-slate-300 text-sm font-medium">
                    {analyzedCount}/{totalCount} sections processed
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Main Content */}
        <div className="max-w-7xl mx-auto px-6 py-12">
          {/* Header */}
          <div className="text-center mb-12">
            <h2 className="text-4xl lg:text-5xl font-bold text-slate-100 mb-6 leading-tight">
              Analysis Results
          </h2>
            <p className="text-xl text-slate-300 max-w-3xl mx-auto leading-relaxed">
              Review each section's analysis. Accept or reject changes to customize your final resume.
          </p>
        </div>

          {/* Job Analysis Summary - Clean and Minimal */}
          {(jobAnalysis.key_technologies.length > 0 || jobAnalysis.requirements.length > 0) && (
            <div className="bg-slate-800/30 backdrop-blur-xl rounded-xl border border-slate-700/30 shadow-lg p-6 mb-8">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-8 h-8 bg-slate-700/50 rounded-lg flex items-center justify-center">
                  <Target className="w-4 h-4 text-slate-300" />
                </div>
                <h3 className="text-lg font-semibold text-slate-100">Target Position Overview</h3>
              </div>
              
              <div className="grid md:grid-cols-2 gap-6">
                {jobAnalysis.key_technologies.length > 0 && (
                  <div>
                    <h4 className="text-sm font-medium text-slate-300 mb-3">Key Technologies</h4>
                    <div className="flex flex-wrap gap-2">
                      {jobAnalysis.key_technologies.slice(0, 6).map((tech, idx) => (
                        <span key={idx} className="px-2 py-1 bg-slate-700/40 text-slate-300 text-xs rounded-md">
                          {tech}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
                {jobAnalysis.requirements.length > 0 && (
                  <div>
                    <h4 className="text-sm font-medium text-slate-300 mb-3">Core Requirements</h4>
                    <ul className="space-y-1">
                      {jobAnalysis.requirements.slice(0, 3).map((req, idx) => (
                        <li key={idx} className="flex items-start gap-2 text-slate-300">
                          <div className="w-1 h-1 rounded-full bg-slate-400 mt-2 flex-shrink-0" />
                          <span className="text-xs leading-relaxed">{req}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Section Analysis Cards */}
          <div className="space-y-8">
            {analysisOrder.map((sectionType) => {
              const section = sections[sectionType]
              const analysis = sectionAnalyses[sectionType]
              const isAccepted = analysisSession.acceptedChanges[sectionType]
              const isRejected = isAccepted === false
              const hasUndoHistory = undoHistory[sectionType] !== undefined
              const SectionIcon = SECTION_ICONS[sectionType] || FileText
              
              const displayScore = analysis ? Math.round(analysis.score / 20) : 0
              
              // Get content for display - FIXED: Proper content selection
              let originalContent = ""
              let improvedContent = ""
              
              if (analysis?.original_content) {
                originalContent = analysis.original_content
              } else if (section?.content) {
                originalContent = section.content
              }
              
              if (analysis?.improved_content) {
                improvedContent = analysis.improved_content
              }
              
              const hasValidContent = originalContent && originalContent.length > 0

              return (
                <div key={sectionType} className="bg-slate-800/30 backdrop-blur-xl rounded-xl border border-slate-700/30 shadow-lg overflow-hidden">
                  {/* Section Header - Clean and Minimal */}
                  <div className="bg-slate-700/20 border-b border-slate-600/20 p-5">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 bg-slate-700/50 rounded-lg flex items-center justify-center">
                          <SectionIcon className="w-4 h-4 text-slate-300" />
                        </div>
                        <div>
                          <h3 className="text-lg font-semibold text-slate-100">
                            {SECTION_DISPLAY_NAMES[sectionType] || sectionType}
                          </h3>
                          {analysis && (
                            <div className="flex items-center gap-4 mt-1">
                              <div className="flex items-center gap-1">
                                <Star className="w-3 h-3 text-yellow-500" />
                                <span className="text-slate-400 text-xs">
                                  {displayScore}/5
                                </span>
                              </div>
                              {isAccepted && (
                                <div className="flex items-center gap-1">
                                  <CheckCircle className="w-3 h-3 text-emerald-400" />
                                  <span className="text-emerald-400 text-xs">
                                    Accepted
                                  </span>
                                </div>
                              )}
                              {isRejected && (
                                <div className="flex items-center gap-1">
                                  <XCircle className="w-3 h-3 text-red-400" />
                                  <span className="text-red-400 text-xs">
                                    Rejected
                                  </span>
                                </div>
                              )}
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Section Content - Clean and Minimal */}
                  <div className="p-5">
                    {!hasValidContent ? (
                      <div className="text-center py-8">
                        <div className="w-10 h-10 bg-yellow-500/20 rounded-lg flex items-center justify-center mx-auto mb-3">
                          <AlertCircle className="w-5 h-5 text-yellow-400" />
                        </div>
                        <h4 className="text-base font-medium text-slate-200 mb-1">No Content Available</h4>
                        <p className="text-slate-400 text-sm">This section was not found in your resume.</p>
                      </div>
                    ) : !analysis ? (
                      <div className="text-center py-8">
                        <Loader className="w-5 h-5 mx-auto mb-3 animate-spin text-slate-400" />
                        <p className="text-slate-400 text-sm">Analyzing section...</p>
                      </div>
                    ) : (
                      <div className="space-y-4">
                        {/* Content Comparison - Cleaner Layout */}
                        <div className="grid lg:grid-cols-2 gap-4">
                          {/* Original Content */}
                          <div>
                            <div className="flex items-center gap-2 mb-3">
                              <FileText className="w-3 h-3 text-slate-400" />
                              <h4 className="text-xs font-medium text-slate-300 uppercase tracking-wide">Original</h4>
                            </div>
                            <div className="bg-slate-700/20 border border-slate-600/20 rounded-lg p-3">
                              <pre className="whitespace-pre-wrap text-xs text-slate-200 font-sans leading-relaxed">
                                {originalContent}
                              </pre>
                            </div>
                          </div>

                          {/* Improved Content */}
                          <div>
                            <div className="flex items-center gap-2 mb-3">
                              <Edit3 className="w-3 h-3 text-slate-400" />
                              <h4 className="text-xs font-medium text-slate-300 uppercase tracking-wide">Suggested</h4>
                            </div>
                            <div className="bg-slate-700/20 border border-slate-600/20 rounded-lg p-3">
                              {improvedContent ? (
                                <pre className="whitespace-pre-wrap text-xs text-slate-200 font-sans leading-relaxed">
                                  {improvedContent}
                                </pre>
                              ) : (
                                <p className="text-slate-400 text-xs italic">No improvements suggested</p>
                              )}
                            </div>
                          </div>
                        </div>

                        {/* Analysis Feedback - Minimal */}
                        {analysis.feedback && (
                          <div className="bg-slate-700/10 border border-slate-600/20 rounded-lg p-3">
                            <div className="flex items-start gap-2">
                              <div className="w-6 h-6 bg-slate-700/40 rounded-md flex items-center justify-center flex-shrink-0">
                                <Lightbulb className="w-3 h-3 text-slate-400" />
                              </div>
                              <div>
                                <h5 className="text-xs font-medium text-slate-200 mb-1 uppercase tracking-wide">Notes</h5>
                                <p className="text-slate-300 text-xs leading-relaxed">{analysis.feedback}</p>
                              </div>
                            </div>
                          </div>
                        )}

                        {/* Action Buttons - Clean and Minimal */}
                        {improvedContent && (
                          <div className="flex gap-2 pt-3 border-t border-slate-600/20">
                            <Button
                              onClick={() => handleAcceptChanges(sectionType, true)}
                              disabled={isAccepted === true}
                              size="sm"
                              className="bg-emerald-600 hover:bg-emerald-700 text-white disabled:opacity-50 text-xs px-3 py-1"
                            >
                              <CheckCircle className="w-3 h-3 mr-1" />
                              {isAccepted === true ? 'Accepted' : 'Accept'}
                            </Button>
                            <Button
                              onClick={() => handleAcceptChanges(sectionType, false)}
                              disabled={isAccepted === false}
                              variant="outline"
                              size="sm"
                              className="border-red-400/30 text-red-400 hover:bg-red-500/10 hover:border-red-400/50 disabled:opacity-50 text-xs px-3 py-1"
                            >
                              <XCircle className="w-3 h-3 mr-1" />
                              {isAccepted === false ? 'Rejected' : 'Reject'}
                            </Button>
                            {hasUndoHistory && (
                              <Button
                                onClick={() => handleUndoChanges(sectionType)}
                                variant="outline"
                                size="sm"
                                className="border-slate-600/30 text-slate-400 hover:bg-slate-700/30 text-xs px-3 py-1"
                              >
                                <RefreshCw className="w-3 h-3 mr-1" />
                                Undo
                              </Button>
                            )}
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                </div>
          )
        })}
      </div>

          {/* Generate Final Resume Button */}
          <div className="mt-12 text-center">
            <div className="bg-slate-800/50 backdrop-blur-xl rounded-2xl border border-slate-700/50 shadow-xl p-8">
              <div className="max-w-2xl mx-auto">
                <h3 className="text-2xl font-semibold text-slate-100 mb-4">Generate Final Resume</h3>
                <p className="text-slate-300 mb-6 leading-relaxed">
                  Ready to create your final resume with all approved changes applied.
                </p>
          <Button 
            onClick={handleGenerateFinalResume}
                  disabled={isGeneratingFinal}
                  size="lg"
                  className="bg-gradient-to-r from-slate-700 to-slate-800 hover:from-slate-600 hover:to-slate-700 text-white shadow-xl hover:shadow-2xl transition-all duration-300 px-8 py-3 text-lg font-medium rounded-xl border border-slate-600/30"
          >
            {isGeneratingFinal ? (
              <>
                      <Loader className="w-5 h-5 mr-3 animate-spin" />
                      Generating Resume...
              </>
            ) : (
              <>
                <Download className="w-5 h-5 mr-3" />
                      Generate Resume
              </>
            )}
          </Button>
        </div>
    </div>
      </div>
      </div>
    </div>
  )
  }

  const renderFinalResume = () => {
    if (!finalResume) return null

    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
        {/* Professional Header */}
        <div className="border-b border-slate-700/50 bg-slate-900/80 backdrop-blur-xl">
          <div className="max-w-6xl mx-auto px-6 py-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 bg-gradient-to-r from-slate-600 to-slate-700 rounded-xl flex items-center justify-center shadow-lg border border-slate-600/30">
                  <span className="text-white font-bold text-xl">RW</span>
        </div>
                <div>
                  <h1 className="text-2xl font-bold text-slate-100">ResumeWise</h1>
                  <p className="text-slate-400 text-sm">Professional Resume Analysis</p>
      </div>
              </div>
              <div className="flex items-center gap-4">
              <Button 
                  onClick={downloadResume}
                  className="bg-gradient-to-r from-slate-700 to-slate-800 hover:from-slate-600 hover:to-slate-700 text-white shadow-lg border border-slate-600/30"
              >
                  <Download className="w-4 h-4 mr-2" />
                  Download Resume
              </Button>
              <Button 
                  onClick={resetAnalysis}
                  variant="outline"
                  className="border-slate-600/30 text-slate-300 hover:bg-slate-700/30"
              >
                  New Analysis
              </Button>
            </div>
          </div>
          </div>
        </div>

        {/* Main Content */}
        <div className="max-w-6xl mx-auto px-6 py-12">
          {/* Header */}
          <div className="text-center mb-12">
            <h2 className="text-4xl font-bold text-slate-100 mb-4">
              Final Resume
            </h2>
            <p className="text-lg text-slate-300 leading-relaxed">
              Your resume has been processed with your approved improvements.
            </p>
          </div>

          {/* Resume Content */}
          <div className="bg-slate-800/50 backdrop-blur-xl rounded-2xl border border-slate-700/50 shadow-xl p-8 lg:p-12">
            <div className="bg-white rounded-lg shadow-2xl p-8 lg:p-12 max-w-4xl mx-auto">
              <pre className="whitespace-pre-wrap text-gray-800 font-sans leading-relaxed text-sm lg:text-base">
                {finalResume}
              </pre>
            </div>
          </div>
        </div>
      </div>
    )
  }

  

  // Main render
  return (
    <div className="min-h-screen">
      {/* Error Display */}
      {error && (
        <Alert className="mb-6 border-red-200 bg-red-50">
          <AlertCircle className="h-4 w-4 text-red-600" />
          <AlertDescription className="text-red-800">{error}</AlertDescription>
        </Alert>
      )}

      {/* Main Content */}
      {showFinalResume ? renderFinalResume() : 
       analysisSession ? renderSectionAnalysis() : 
       renderUploadSection()}

      {/* Professional Clarification Modal */}
      <Dialog open={clarificationModal.isOpen} onOpenChange={(open) => {
        if (!open) {
          setClarificationModal({
            isOpen: false,
            sectionType: "",
            question: "",
            context: "",
            reason: "",
            userResponse: ""
          })
        }
      }}>
        <DialogContent className="max-w-4xl max-h-[85vh] overflow-hidden bg-white shadow-2xl border-0 rounded-2xl">
          {/* Header with gradient background */}
          <div className="relative -m-6 mb-6 p-6 bg-gradient-to-r from-blue-600 to-indigo-600 text-white">
            <div className="absolute inset-0 bg-black/10 backdrop-blur-sm"></div>
            <DialogHeader className="relative z-10">
              <DialogTitle className="flex items-center gap-3 text-2xl font-bold">
                <div className="w-10 h-10 bg-white/20 rounded-full flex items-center justify-center backdrop-blur-sm">
                  <MessageCircle className="w-5 h-5" />
        </div>
                Additional Information Required: {SECTION_DISPLAY_NAMES[clarificationModal.sectionType]} Section
              </DialogTitle>
              <DialogDescription className="text-blue-100 text-lg mt-2 leading-relaxed">
                Please provide additional details to enhance the content quality and alignment with the target position.
              </DialogDescription>
            </DialogHeader>
      </div>

          <div className="space-y-8 max-h-[60vh] overflow-y-auto px-2">
            {/* Question Card */}
            <div className="relative">
              <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-xl p-6 shadow-sm">
                <div className="flex items-start gap-4">
                  <div className="w-12 h-12 bg-blue-500 rounded-xl flex items-center justify-center shadow-lg flex-shrink-0">
                    <svg className="w-6 h-6 text-white" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-8-3a1 1 0 00-.867.5 1 1 0 11-1.731-1A3 3 0 0113 8a3.001 3.001 0 01-2 2.83V11a1 1 0 11-2 0v-1a1 1 0 011-1 1 1 0 100-2zm0 8a1 1 0 100-2 1 1 0 000 2z" clipRule="evenodd" />
                    </svg>
          </div>
                  <div className="min-w-0 flex-1">
                    <h3 className="text-lg font-semibold text-blue-900 mb-3">Information Requested:</h3>
                    <p className="text-blue-800 leading-relaxed text-base">{clarificationModal.question}</p>
        </div>
          </div>
              </div>
        </div>

            {/* Context Card */}
            {clarificationModal.context && (
              <div className="bg-gradient-to-r from-slate-50 to-gray-50 border border-slate-200 rounded-xl p-6 shadow-sm">
                <div className="flex items-start gap-4">
                  <div className="w-12 h-12 bg-slate-500 rounded-xl flex items-center justify-center shadow-lg flex-shrink-0">
                    <Lightbulb className="w-6 h-6 text-white" />
          </div>
                  <div className="min-w-0 flex-1">
                    <h3 className="text-lg font-semibold text-slate-900 mb-3">Background Context:</h3>
                    <p className="text-slate-700 leading-relaxed text-base">{clarificationModal.context}</p>
        </div>
                  </div>
              </div>
            )}

            {/* Response Input Section */}
            <div className="space-y-4">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 bg-emerald-500 rounded-lg flex items-center justify-center">
                  <svg className="w-4 h-4 text-white" fill="currentColor" viewBox="0 0 20 20">
                    <path d="M13.586 3.586a2 2 0 112.828 2.828l-.793.793-2.828-2.828.793-.793zM11.379 5.793L3 14.172V17h2.828l8.38-8.379-2.83-2.828z" />
                  </svg>
            </div>
                <h3 className="text-lg font-semibold text-slate-900">Your Response</h3>
          </div>

              <div className="relative">
                <Textarea
                  value={clarificationModal.userResponse}
                  onChange={(e) => setClarificationModal(prev => ({
                    ...prev,
                    userResponse: e.target.value
                  }))}
                  placeholder="Please provide specific details such as technologies used, team size, measurable outcomes, timeframes, or achievements. Detailed information enables more effective content enhancement."
                  className="min-h-[180px] text-base leading-relaxed resize-none border-2 border-slate-200 rounded-xl p-4 focus:border-blue-500 focus:ring-4 focus:ring-blue-500/20 transition-all duration-200 shadow-sm"
                  rows={8}
                />
                <div className="absolute bottom-3 right-3 text-xs text-slate-400 bg-white px-2 py-1 rounded-lg border">
                  {clarificationModal.userResponse.length} characters
                </div>
              </div>
          </div>

            {/* Pro Tips Section */}
            <div className="bg-gradient-to-r from-emerald-50 to-green-50 border border-emerald-200 rounded-xl p-6 shadow-sm">
              <div className="flex items-start gap-4">
                <div className="w-12 h-12 bg-emerald-500 rounded-xl flex items-center justify-center shadow-lg flex-shrink-0">
                  <Star className="w-6 h-6 text-white" />
            </div>
                <div className="min-w-0 flex-1">
                  <h3 className="text-lg font-semibold text-emerald-900 mb-3">Guidelines for Optimal Results:</h3>
                  <div className="space-y-2 text-emerald-800">
                    <div className="flex items-start gap-2">
                      <div className="w-1.5 h-1.5 bg-emerald-500 rounded-full mt-2 flex-shrink-0"></div>
                      <p className="text-sm leading-relaxed"><strong>Quantify results:</strong> Include specific numbers, percentages, and timeframes</p>
                    </div>
                    <div className="flex items-start gap-2">
                      <div className="w-1.5 h-1.5 bg-emerald-500 rounded-full mt-2 flex-shrink-0"></div>
                      <p className="text-sm leading-relaxed"><strong>Technical details:</strong> List specific technologies, tools, and methodologies used</p>
                    </div>
                    <div className="flex items-start gap-2">
                      <div className="w-1.5 h-1.5 bg-emerald-500 rounded-full mt-2 flex-shrink-0"></div>
                      <p className="text-sm leading-relaxed"><strong>Business impact:</strong> Describe results, improvements, or value delivered</p>
                    </div>
                    <div className="flex items-start gap-2">
                      <div className="w-1.5 h-1.5 bg-emerald-500 rounded-full mt-2 flex-shrink-0"></div>
                      <p className="text-sm leading-relaxed"><strong>Project scope:</strong> Include team sizes, budgets, or duration when applicable</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex items-center justify-between pt-6 border-t border-slate-200 mt-8">
            <Button
              onClick={() => setClarificationModal({
                isOpen: false,
                sectionType: "",
                question: "",
                context: "",
                reason: "",
                userResponse: ""
              })}
              variant="outline"
              disabled={isProcessingClarification}
              className="px-6 py-3 text-base border-slate-300 text-slate-600 hover:bg-slate-50 transition-all duration-200"
            >
              Skip This Step
            </Button>
            
            <div className="flex items-center gap-3">
              <div className="text-sm text-slate-500">
                {clarificationModal.userResponse.trim() ? "Information provided" : "Please provide details above"}
              </div>
              <Button
                onClick={handleSubmitClarification}
                disabled={isProcessingClarification || !clarificationModal.userResponse.trim()}
                className="px-8 py-3 text-base bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white shadow-lg hover:shadow-xl transition-all duration-200 transform hover:scale-105 disabled:transform-none disabled:opacity-50"
              >
                {isProcessingClarification ? (
                  <>
                    <Loader className="w-5 h-5 mr-3 animate-spin" />
                    Processing Enhancement...
                </>
              ) : (
                <>
                    <CheckCircle className="w-5 h-5 mr-3" />
                    Submit Information
                </>
              )}
            </Button>
                    </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  )
}
