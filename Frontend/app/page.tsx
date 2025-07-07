"use client"

import type React from "react"

import { useState } from "react"
import {
  Upload,
  FileText,
  Briefcase,
  Sparkles,
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
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { useTheme } from "next-themes"
import { resumeCriticAPI, type ResumeAnalysisResponse, type ResumeBullet, type ClarificationRequest } from "@/lib/api"

interface CritiqueItem {
  id: string
  original: string
  suggested: string
  reason: string
  category: "Impact" | "Clarity" | "Keywords" | "Format"
  impact: "High" | "Medium" | "Low"
  bulletId?: string
  sectionId?: string
  needsClarification?: boolean
  clarificationQuestion?: string
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
    bulletId: string
    sectionId: string
    question: string
    originalText: string
    userResponse: string
  }>({
    isOpen: false,
    bulletId: "",
    sectionId: "",
    question: "",
    originalText: "",
    userResponse: "",
  })
  const [isProcessingClarification, setIsProcessingClarification] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const { theme, setTheme } = useTheme()

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
        setAnalysisData(analysisData)
        
        // Convert backend data to frontend format
        const convertedCritiques: CritiqueItem[] = []
        
        if (analysisData.sections && Array.isArray(analysisData.sections)) {
          analysisData.sections.forEach((section: any) => {
            if (section.bullets && Array.isArray(section.bullets)) {
              section.bullets.forEach((bullet: any) => {
                const category = getCategoryFromScore(bullet.evaluation.overall_score)
                const impact = getImpactFromScore(bullet.evaluation.overall_score)
                
                const critique: CritiqueItem = {
                  id: bullet.id,
                  original: bullet.original_text,
                  suggested: bullet.improvement?.improved_text || bullet.original_text,
                  reason: bullet.evaluation.explanation,
                  category,
                  impact,
                  bulletId: bullet.id,
                  sectionId: section.id,
                  needsClarification: bullet.needs_clarification,
                  clarificationQuestion: bullet.evaluation.needs_clarification?.question || "",
                }
                
                convertedCritiques.push(critique)
              })
            }
          })
        }
        
        setCritiques(convertedCritiques)
        setShowResults(true)
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

  const handleClarification = async (bulletId: string, sectionId: string, question: string, originalText: string) => {
    setClarificationModal({
      isOpen: true,
      bulletId,
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
        analysis_id: analysisData.analysis_id,
        section_id: clarificationModal.sectionId,
        bullet_id: clarificationModal.bulletId,
        user_response: clarificationModal.userResponse,
        clarification_type: "missing_metrics",
        original_text: clarificationModal.originalText,
        question: clarificationModal.question,
      }

      const response = await resumeCriticAPI.processClarification(request)

      if (response.success) {
        // The backend wraps the response in a 'data' field
        const responseData = (response as any).data || response
        
        // Update the critique with the improved bullet
        setCritiques(prev => prev.map(critique => {
          if (critique.bulletId === clarificationModal.bulletId) {
            return {
              ...critique,
              suggested: responseData.improved_bullet.improved_text,
              reason: responseData.improved_bullet.improvement_explanation,
              needsClarification: false,
            }
          }
          return critique
        }))

        setClarificationModal({
          isOpen: false,
          bulletId: "",
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

  const handleApply = (id: string) => {
    setCritiques((prev) => prev.filter((c) => c.id !== id))
  }

  const handleReject = (id: string) => {
    setCritiques((prev) => prev.filter((c) => c.id !== id))
  }

  const getCategoryFromScore = (score: number): "Impact" | "Clarity" | "Keywords" | "Format" => {
    if (score >= 7) return "Impact"
    if (score >= 5) return "Clarity"
    if (score >= 3) return "Keywords"
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
      default:
        return <Star className="w-4 h-4" />
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

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-orange-50/30 to-amber-50/50 dark:bg-gradient-to-br dark:from-black dark:via-gray-900 dark:to-black relative overflow-hidden">
      {/* Animated background elements */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none gradient-mesh">
        <div className="absolute -top-40 -right-40 w-80 h-80 bg-gradient-to-br from-orange-500/20 to-amber-600/20 dark:from-orange-500/8 dark:to-amber-600/8 rounded-full blur-3xl animate-pulse"></div>
        <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-gradient-to-br from-amber-500/20 to-yellow-600/20 dark:from-amber-500/8 dark:to-yellow-600/8 rounded-full blur-3xl animate-pulse delay-1000"></div>
        <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-gradient-to-br from-orange-400/10 to-amber-600/10 dark:from-orange-400/4 dark:to-amber-600/4 rounded-full blur-3xl animate-pulse delay-500"></div>
      </div>

      {/* Header */}
      <header className="border-b border-white/20 dark:border-gray-800/50 backdrop-blur-xl bg-white/80 dark:bg-black/90 sticky top-0 z-50 shadow-lg shadow-black/5 dark:shadow-black/20">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-orange-500 to-amber-600 flex items-center justify-center shadow-lg shadow-orange-500/25">
              <Sparkles className="w-5 h-5 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold bg-gradient-to-r from-slate-900 to-slate-600 dark:from-white dark:to-gray-300 bg-clip-text text-transparent">
                Resume Critic AI
              </h1>
            </div>
          </div>
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
            className="rounded-full hover:bg-white/20 dark:hover:bg-gray-800/50 transition-all duration-300 hover:scale-110"
          >
            <Sun className="h-5 w-5 rotate-0 scale-100 transition-all dark:-rotate-90 dark:scale-0" />
            <Moon className="absolute h-5 w-5 rotate-90 scale-0 transition-all dark:rotate-0 dark:scale-100" />
          </Button>
        </div>
      </header>

      <main className="container mx-auto px-4 py-8 max-w-6xl relative z-10">
        {/* Error Display */}
        {error && (
          <div className="mb-6 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl">
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
          <div className="inline-flex items-center gap-2 bg-gradient-to-r from-orange-500/10 to-amber-500/10 dark:from-orange-500/20 dark:to-amber-500/20 border border-orange-500/20 dark:border-orange-500/30 rounded-full px-4 py-2 mb-6">
            <Sparkles className="w-4 h-4 text-orange-600 dark:text-orange-400" />
            <span className="text-sm font-medium text-orange-700 dark:text-orange-300">AI-Powered Resume Analysis</span>
          </div>
          <h2 className="text-5xl font-bold mb-6 bg-gradient-to-r from-slate-900 via-orange-800 to-amber-800 dark:from-white dark:via-orange-200 dark:to-amber-200 bg-clip-text text-transparent leading-tight">
            Resume Critic AI
          </h2>
          <p className="text-xl text-slate-600 dark:text-gray-300 max-w-2xl mx-auto leading-relaxed">
            Get smart, trustworthy suggestions to level up your resume and land your dream job.
          </p>
        </div>

        {!showResults ? (
          /* Upload Section */
          <div className="grid md:grid-cols-2 gap-8 mb-12">
            {/* Resume Upload */}
            <Card className="group backdrop-blur-xl bg-white/70 dark:bg-gray-900/70 border-white/20 dark:border-gray-800/50 shadow-xl shadow-black/5 dark:shadow-black/20 hover:shadow-2xl hover:shadow-orange-500/10 dark:hover:shadow-orange-500/5 transition-all duration-500 hover:-translate-y-1">
              <CardHeader className="pb-4">
                <CardTitle className="flex items-center gap-3 text-lg dark:text-white">
                  <div className="p-2 rounded-lg bg-gradient-to-br from-orange-500 to-amber-600 text-white shadow-lg shadow-orange-500/25">
                    <FileText className="w-5 h-5" />
                  </div>
                  Upload Resume
                </CardTitle>
                <CardDescription className="text-slate-600 dark:text-gray-400">
                  Upload your resume in PDF, DOCX, DOC, or TXT format
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="border-2 border-dashed border-orange-300/50 dark:border-orange-500/30 rounded-2xl p-8 text-center hover:border-orange-400/70 dark:hover:border-orange-400/50 transition-all duration-300 group-hover:bg-orange-50/50 dark:group-hover:bg-orange-900/10">
                  <input
                    type="file"
                    accept=".pdf,.txt,.doc,.docx"
                    onChange={handleFileUpload}
                    className="hidden"
                    id="resume-upload"
                  />
                  <label htmlFor="resume-upload" className="cursor-pointer block">
                    <div className="w-12 h-12 mx-auto mb-4 rounded-full bg-gradient-to-br from-orange-500 to-amber-600 flex items-center justify-center text-white shadow-lg shadow-orange-500/25 group-hover:scale-110 transition-transform duration-300">
                      <Upload className="w-6 h-6" />
                    </div>
                    <p className="text-sm font-medium text-slate-700 dark:text-gray-300 mb-2">
                      {resumeFile ? (
                        <span className="text-emerald-600 dark:text-emerald-400 flex items-center justify-center gap-2">
                          <CheckCircle className="w-4 h-4" />
                          {resumeFile.name}
                        </span>
                      ) : (
                        "Click to upload or drag and drop"
                      )}
                    </p>
                    <p className="text-xs text-slate-500 dark:text-gray-500">PDF, DOCX, DOC, TXT up to 10MB</p>
                  </label>
                </div>
              </CardContent>
            </Card>

            {/* Job Description */}
            <Card className="group backdrop-blur-xl bg-white/70 dark:bg-gray-900/70 border-white/20 dark:border-gray-800/50 shadow-xl shadow-black/5 dark:shadow-black/20 hover:shadow-2xl hover:shadow-amber-500/10 dark:hover:shadow-amber-500/5 transition-all duration-500 hover:-translate-y-1">
              <CardHeader className="pb-4">
                <CardTitle className="flex items-center gap-3 text-lg dark:text-white">
                  <div className="p-2 rounded-lg bg-gradient-to-br from-amber-500 to-orange-600 text-white shadow-lg shadow-amber-500/25">
                    <Briefcase className="w-5 h-5" />
                  </div>
                  Job Description
                </CardTitle>
                <CardDescription className="text-slate-600 dark:text-gray-400">
                  Paste the job description you're applying for
                </CardDescription>
              </CardHeader>
              <CardContent>
                <Textarea
                  placeholder="Paste the job description here to get tailored suggestions..."
                  value={jobDescription}
                  onChange={(e) => setJobDescription(e.target.value)}
                  className="min-h-[200px] resize-none bg-white/50 dark:bg-gray-800/50 border-slate-200/50 dark:border-gray-700/50 focus:border-orange-400 dark:focus:border-orange-400 transition-colors duration-300 rounded-xl dark:text-white dark:placeholder:text-gray-400"
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
              className="bg-gradient-to-r from-orange-600 via-amber-600 to-yellow-600 hover:from-orange-700 hover:via-amber-700 hover:to-yellow-700 text-white px-12 py-4 rounded-2xl shadow-2xl shadow-orange-500/25 hover:shadow-amber-500/30 transition-all duration-300 hover:scale-105 disabled:hover:scale-100 text-lg font-semibold"
            >
              {isAnalyzing ? (
                <>
                  <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin mr-3" />
                  Analyzing Resume...
                </>
              ) : (
                <>
                  <Sparkles className="w-5 h-5 mr-3" />
                  Analyze Resume
                </>
              )}
            </Button>
          </div>
        )}

        {/* Results Section */}
        {showResults && (
          <div className="space-y-8">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-3xl font-bold bg-gradient-to-r from-slate-900 to-slate-600 dark:from-white dark:to-gray-300 bg-clip-text text-transparent mb-2">
                  Resume Analysis Results
                </h3>
                <p className="text-slate-600 dark:text-gray-400">
                  Found {critiques.length} suggestions to improve your resume
                </p>
                {analysisData && (
                  <div className="mt-2 flex gap-4 text-sm text-slate-500 dark:text-gray-500">
                    <span>Overall Score: {analysisData.summary.overall_score.toFixed(1)}/10</span>
                    <span>Strong Bullets: {analysisData.summary.strong_bullets}</span>
                    <span>Needs Improvement: {analysisData.summary.needs_improvement}</span>
                  </div>
                )}
              </div>
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
                className="border-slate-200 dark:border-gray-700 hover:bg-slate-50 dark:hover:bg-gray-800 dark:text-white transition-all duration-300 hover:scale-105"
              >
                Start New Analysis
              </Button>
            </div>

            <div className="grid gap-6">
              {critiques.map((critique, index) => (
                <Card
                  key={critique.id}
                  className="group backdrop-blur-xl bg-white/80 dark:bg-gray-900/80 border-white/20 dark:border-gray-800/50 shadow-xl shadow-black/5 dark:shadow-black/20 hover:shadow-2xl hover:shadow-orange-500/10 dark:hover:shadow-orange-500/5 transition-all duration-500 hover:-translate-y-1"
                  style={{ animationDelay: `${index * 100}ms` }}
                >
                  <CardContent className="p-8">
                    <div className="flex items-start justify-between mb-6">
                      <div className="flex items-center gap-3">
                        <Badge
                          className={`${getCategoryColor(critique.category)} text-white border-0 px-3 py-1 shadow-lg`}
                        >
                          <span className="flex items-center gap-1">
                            {getCategoryIcon(critique.category)}
                            {critique.category}
                          </span>
                        </Badge>
                        <Badge
                          variant={
                            critique.impact === "High"
                              ? "destructive"
                              : critique.impact === "Medium"
                                ? "default"
                                : "secondary"
                          }
                          className="shadow-sm dark:bg-gray-800 dark:text-gray-200 dark:border-gray-700"
                        >
                          {critique.impact} Impact
                        </Badge>
                        {critique.needsClarification && (
                          <Badge
                            variant="outline"
                            className="border-orange-300 text-orange-600 dark:border-orange-600 dark:text-orange-400"
                          >
                            <MessageCircle className="w-3 h-3 mr-1" />
                            Needs Clarification
                          </Badge>
                        )}
                      </div>
                    </div>

                    <div className="space-y-6">
                      <div className="relative">
                        <h4 className="text-sm font-semibold text-slate-600 dark:text-gray-400 mb-3 flex items-center gap-2">
                          <XCircle className="w-4 h-4 text-red-500" />
                          Original:
                        </h4>
                        <div className="relative p-4 bg-gradient-to-r from-red-50 to-red-50/50 dark:from-red-900/20 dark:to-red-800/10 border border-red-200/50 dark:border-red-800/30 rounded-xl">
                          <p className="text-sm text-slate-700 dark:text-gray-300 leading-relaxed">
                            {critique.original}
                          </p>
                        </div>
                      </div>

                      <div className="relative">
                        <h4 className="text-sm font-semibold text-slate-600 dark:text-gray-400 mb-3 flex items-center gap-2">
                          <CheckCircle className="w-4 h-4 text-emerald-500" />
                          Suggested:
                        </h4>
                        <div className="relative p-4 bg-gradient-to-r from-emerald-50 to-emerald-50/50 dark:from-emerald-900/20 dark:to-emerald-800/10 border border-emerald-200/50 dark:border-emerald-800/30 rounded-xl">
                          <p className="text-sm text-slate-700 dark:text-gray-300 leading-relaxed font-medium">
                            {critique.suggested}
                          </p>
                        </div>
                      </div>

                      <div className="relative">
                        <h4 className="text-sm font-semibold text-slate-600 dark:text-gray-400 mb-3 flex items-center gap-2">
                          <Sparkles className="w-4 h-4 text-orange-500" />
                          Why this helps:
                        </h4>
                        <p className="text-sm text-slate-600 dark:text-gray-400 leading-relaxed bg-orange-50/50 dark:bg-orange-900/10 p-4 rounded-xl border border-orange-200/30 dark:border-orange-800/20">
                          {critique.reason}
                        </p>
                      </div>
                    </div>

                    <div className="flex gap-3 mt-8">
                      {critique.needsClarification ? (
                        <Button
                          size="sm"
                          onClick={() => handleClarification(
                            critique.bulletId!,
                            critique.sectionId!,
                            critique.clarificationQuestion!,
                            critique.original
                          )}
                          className="bg-gradient-to-r from-orange-500 to-amber-500 hover:from-orange-600 hover:to-amber-600 text-white shadow-lg hover:shadow-xl transition-all duration-300 hover:scale-105"
                        >
                          <MessageCircle className="w-4 h-4 mr-2" />
                          Provide Details
                        </Button>
                      ) : (
                        <Button
                          size="sm"
                          onClick={() => handleApply(critique.id)}
                          className="bg-gradient-to-r from-emerald-500 to-green-500 hover:from-emerald-600 hover:to-green-600 text-white shadow-lg hover:shadow-xl transition-all duration-300 hover:scale-105"
                        >
                          <CheckCircle className="w-4 h-4 mr-2" />
                          Apply
                        </Button>
                      )}
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => handleReject(critique.id)}
                        className="border-slate-200 dark:border-gray-700 hover:bg-slate-50 dark:hover:bg-gray-800 dark:text-white transition-all duration-300 hover:scale-105"
                      >
                        <Edit3 className="w-4 h-4 mr-2" />
                        Edit
                      </Button>
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => handleReject(critique.id)}
                        className="text-slate-500 dark:text-gray-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 transition-all duration-300 hover:scale-105"
                      >
                        <XCircle className="w-4 h-4 mr-2" />
                        Reject
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>

            {critiques.length === 0 && (
              <Card className="backdrop-blur-xl bg-gradient-to-br from-emerald-50 to-green-50 dark:from-emerald-900/20 dark:to-green-900/20 border-emerald-200/50 dark:border-emerald-800/30 shadow-xl">
                <CardContent className="p-12 text-center">
                  <div className="w-16 h-16 mx-auto mb-6 rounded-full bg-gradient-to-br from-emerald-500 to-green-500 flex items-center justify-center text-white shadow-2xl shadow-emerald-500/25">
                    <Sparkles className="w-8 h-8" />
                  </div>
                  <h3 className="text-2xl font-bold mb-3 text-emerald-800 dark:text-emerald-300">Congratulations!</h3>
                  <p className="text-emerald-700 dark:text-emerald-400 text-lg">
                    You've reviewed all suggestions. Your resume is looking much better!
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
          <Card className="w-full max-w-2xl backdrop-blur-xl bg-white/90 dark:bg-gray-900/90 border-white/20 dark:border-gray-800/50 shadow-2xl">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-lg dark:text-white">
                <MessageCircle className="w-5 h-5 text-orange-500" />
                Provide Additional Details
              </CardTitle>
              <CardDescription className="text-slate-600 dark:text-gray-400">
                Help us improve this bullet point with more specific information
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div>
                <h4 className="text-sm font-semibold text-slate-600 dark:text-gray-400 mb-2">Original Bullet:</h4>
                <p className="text-sm text-slate-700 dark:text-gray-300 bg-slate-50 dark:bg-gray-800 p-3 rounded-lg">
                  {clarificationModal.originalText}
                </p>
              </div>
              
              <div>
                <h4 className="text-sm font-semibold text-slate-600 dark:text-gray-400 mb-2">Question:</h4>
                <p className="text-sm text-slate-700 dark:text-gray-300 bg-orange-50 dark:bg-orange-900/20 p-3 rounded-lg border border-orange-200/30 dark:border-orange-800/20">
                  {clarificationModal.question}
                </p>
              </div>
              
              <div>
                <h4 className="text-sm font-semibold text-slate-600 dark:text-gray-400 mb-2">Your Response:</h4>
                <Textarea
                  value={clarificationModal.userResponse}
                  onChange={(e) => setClarificationModal(prev => ({ ...prev, userResponse: e.target.value }))}
                  placeholder="Provide specific details, metrics, or context..."
                  className="min-h-[100px] resize-none bg-white/50 dark:bg-gray-800/50 border-slate-200/50 dark:border-gray-700/50 focus:border-orange-400 dark:focus:border-orange-400 transition-colors duration-300 rounded-xl dark:text-white dark:placeholder:text-gray-400"
                />
              </div>
              
              <div className="flex gap-3 justify-end">
                <Button
                  variant="outline"
                  onClick={() => setClarificationModal(prev => ({ ...prev, isOpen: false }))}
                  disabled={isProcessingClarification}
                  className="border-slate-200 dark:border-gray-700 hover:bg-slate-50 dark:hover:bg-gray-800 dark:text-white"
                >
                  Cancel
                </Button>
                <Button
                  onClick={handleSubmitClarification}
                  disabled={!clarificationModal.userResponse.trim() || isProcessingClarification}
                  className="bg-gradient-to-r from-orange-500 to-amber-500 hover:from-orange-600 hover:to-amber-600 text-white shadow-lg hover:shadow-xl transition-all duration-300"
                >
                  {isProcessingClarification ? (
                    <>
                      <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                      Processing...
                    </>
                  ) : (
                    <>
                      <Sparkles className="w-4 h-4 mr-2" />
                      Submit & Improve
                    </>
                  )}
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Footer */}
      <footer className="border-t border-white/20 dark:border-gray-800/50 mt-20 backdrop-blur-xl bg-white/50 dark:bg-black/50">
        <div className="container mx-auto px-4 py-8 text-center">
          <p className="text-sm text-slate-600 dark:text-gray-400">
            Powered by AI Agent • Built with ❤️ for better resumes
          </p>
        </div>
      </footer>
    </div>
  )
}
