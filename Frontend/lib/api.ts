// API service for Resume Critic AI backend integration

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';

export interface ResumeAnalysisRequest {
  job_description: string;
  review_mode: boolean;
}

export interface ClarificationRequest {
  analysis_id: string;
  section_id: string;
  bullet_id: string;
  user_response: string;
  clarification_type: string;
  original_text: string;
  question: string;
}

export interface FinalResumeRequest {
  analysis_id: string;
  accepted_changes: Record<string, string>; // bullet_id -> "original" or "improved"
}

export interface BulletEvaluation {
  clarity_score: number;
  impact_score: number;
  relevance_score: number;
  overall_score: number;
  category: 'strong' | 'needs_improvement' | 'missing_metrics' | 'vague';
  explanation: string;
  strengths: string[];
  weaknesses: string[];
  suggestions: string[];
  needs_clarification: {
    required: boolean;
    question: string;
    type: string;
  };
}

export interface BulletImprovement {
  improved_text: string;
  changes_made: string[];
  improvement_reason: string;
  confidence: 'high' | 'medium' | 'low';
}

export interface ResumeBullet {
  id: string;
  original_text: string;
  evaluation: BulletEvaluation;
  improvement?: BulletImprovement;
  needs_clarification: boolean;
}

export interface ResumeSection {
  id: string;
  title: string;
  bullets: ResumeBullet[];
  original_text: string;
}

export interface AnalysisSummary {
  total_bullets: number;
  strong_bullets: number;
  needs_improvement: number;
  needs_clarification: number;
  overall_score: number;
  job_keywords_matched: number;
}

export interface ResumeAnalysisResponse {
  success: boolean;
  analysis_id: string;
  sections: ResumeSection[];
  summary: AnalysisSummary;
  job_keywords: string[];
  review_mode: boolean;
  timestamp: string;
}

export interface ClarificationResponse {
  success: boolean;
  improved_bullet: {
    improved_text: string;
    original_text: string;
    user_clarification: string;
    improvement_explanation: string;
    new_evaluation: BulletEvaluation;
  };
  analysis_id: string;
  message: string;
}

export interface FinalResumeResponse {
  success: boolean;
  final_resume: {
    resume_text: string;
    sections: Array<{
      title: string;
      content: string[];
    }>;
    accepted_changes_count: number;
    analysis_id: string;
  };
  analysis_id: string;
  message: string;
}

class APIError extends Error {
  constructor(
    message: string,
    public status: number,
    public data?: any
  ) {
    super(message);
    this.name = 'APIError';
  }
}

class ResumeCriticAPI {
  private baseURL: string;

  constructor(baseURL: string = API_BASE_URL) {
    this.baseURL = baseURL;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseURL}${endpoint}`;
    
    const config: RequestInit = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    };

    try {
      const response = await fetch(url, config);
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new APIError(
          errorData.detail || `HTTP ${response.status}: ${response.statusText}`,
          response.status,
          errorData
        );
      }

      return await response.json();
    } catch (error) {
      if (error instanceof APIError) {
        throw error;
      }
      throw new APIError(
        `Network error: ${error instanceof Error ? error.message : 'Unknown error'}`,
        0
      );
    }
  }

  private async uploadFile<T>(
    endpoint: string,
    file: File,
    formData: Record<string, string | boolean>
  ): Promise<T> {
    const url = `${this.baseURL}${endpoint}`;
    
    const data = new FormData();
    data.append('file', file);
    
    // Add other form data
    Object.entries(formData).forEach(([key, value]) => {
      data.append(key, String(value));
    });

    try {
      const response = await fetch(url, {
        method: 'POST',
        body: data,
      });
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new APIError(
          errorData.detail || `HTTP ${response.status}: ${response.statusText}`,
          response.status,
          errorData
        );
      }

      return await response.json();
    } catch (error) {
      if (error instanceof APIError) {
        throw error;
      }
      throw new APIError(
        `Network error: ${error instanceof Error ? error.message : 'Unknown error'}`,
        0
      );
    }
  }

  async analyzeResume(
    file: File,
    jobDescription: string,
    reviewMode: boolean = true
  ): Promise<ResumeAnalysisResponse> {
    return this.uploadFile('/api/analyze-resume', file, {
      job_description: jobDescription,
      review_mode: reviewMode,
    });
  }

  async processClarification(
    request: ClarificationRequest
  ): Promise<ClarificationResponse> {
    return this.request('/api/process-clarification', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  async generateFinalResume(
    request: FinalResumeRequest
  ): Promise<FinalResumeResponse> {
    return this.request('/api/generate-final-resume', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  async getAnalysis(analysisId: string): Promise<ResumeAnalysisResponse> {
    return this.request(`/api/analysis/${analysisId}`);
  }

  async healthCheck(): Promise<{
    status: string;
    version: string;
    features: string[];
    judgment_tracing: boolean;
    openai_configured: boolean;
    supported_formats: string[];
  }> {
    return this.request('/api/health');
  }
}

// Export singleton instance
export const resumeCriticAPI = new ResumeCriticAPI(); 