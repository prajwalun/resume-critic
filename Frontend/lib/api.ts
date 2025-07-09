/**
 * ResumeWise API Client
 * 
 * TypeScript client for the ResumeWise backend API.
 * Provides structured section-by-section resume analysis with human-in-the-loop clarification.
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Request/Response Types

export interface AnalysisStartRequest {
  job_description: string;
}

export interface AnalysisStartResponse {
  success: boolean;
  session_id?: string;
  sections?: Record<string, SectionData>;
  job_analysis?: JobAnalysis;
  analysis_order?: string[];
  section_analyses?: Record<string, SectionAnalysis>;  // Include all section analyses
  error?: string;
}

export interface SectionData {
  type: string;
  content: string;
  original_type: string;
  metadata: SectionMetadata;
}

export interface SectionMetadata {
  word_count: number;
  has_metrics: boolean;
  has_dates: boolean;
  length: number;
}

export interface JobAnalysis {
  keywords: string[];
  requirements: string[];
  experience_level: string;
  key_technologies: string[];
  soft_skills: string[];
  hard_skills: string[];
  priorities: string[];
}

export interface SectionAnalysisRequest {
  session_id: string;
  section_type: string;
}

export interface SectionAnalysisResponse {
  success: boolean;
  analysis?: SectionAnalysis;
  error?: string;
}

export interface SectionAnalysis {
  section_type: string;
  original_content: string;
  improved_content?: string;
  score: number;
  feedback: string;
  needs_clarification: boolean;
  clarification_request?: ClarificationRequest;
  user_context?: string;
}

export interface ClarificationRequest {
  question: string;
  context: string;
  reason: string;
}

export interface ClarificationSubmitRequest {
  session_id: string;
  section_type: string;
  user_response: string;
}

export interface ClarificationResponse {
  success: boolean;
  analysis?: SectionAnalysis;
  error?: string;
}

export interface AcceptChangesRequest {
  session_id: string;
  section_type: string;
  accepted: boolean;
}

export interface AcceptChangesResponse {
  success: boolean;
  message?: string;
  error?: string;
}

export interface FinalResumeRequest {
  session_id: string;
}

export interface FinalResumeResponse {
  success: boolean;
  final_resume?: string;
  sections?: string[];
  session_id?: string;
  error?: string;
}

export interface SessionStatusResponse {
  success: boolean;
  session_id?: string;
  current_phase?: string;
  sections_analyzed?: number;
  pending_clarifications?: number;
  created_at?: string;
  updated_at?: string;
  error?: string;
}

export interface HealthCheckResponse {
  status: string;
  service: string;
}

// Error Classes

export class APIError extends Error {
  constructor(
    message: string,
    public status: number,
    public data?: any
  ) {
    super(message);
    this.name = 'APIError';
  }
}

export class ValidationError extends APIError {
  constructor(message: string, data?: any) {
    super(message, 400, data);
    this.name = 'ValidationError';
  }
}

export class NotFoundError extends APIError {
  constructor(message: string = 'Resource not found') {
    super(message, 404);
    this.name = 'NotFoundError';
  }
}

// Main API Client

export class ResumeWiseAPI {
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
        const errorMessage = errorData.detail || `HTTP ${response.status}: ${response.statusText}`;
        
        if (response.status === 404) {
          throw new NotFoundError(errorMessage);
        } else if (response.status === 400) {
          throw new ValidationError(errorMessage, errorData);
        } else {
          throw new APIError(errorMessage, response.status, errorData);
        }
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
        const errorMessage = errorData.detail || `HTTP ${response.status}: ${response.statusText}`;
        
        if (response.status === 404) {
          throw new NotFoundError(errorMessage);
        } else if (response.status === 400) {
          throw new ValidationError(errorMessage, errorData);
        } else {
          throw new APIError(errorMessage, response.status, errorData);
        }
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

  // API Methods

  /**
   * Start a new resume analysis session
   */
  async startAnalysis(
    file: File,
    jobDescription: string
  ): Promise<AnalysisStartResponse> {
    return this.uploadFile('/api/start-analysis', file, {
      job_description: jobDescription,
    });
  }

  /**
   * Analyze a specific section of the resume
   */
  async analyzeSection(
    sessionId: string,
    sectionType: string
  ): Promise<SectionAnalysisResponse> {
    return this.request('/api/analyze-section', {
      method: 'POST',
      body: JSON.stringify({
        session_id: sessionId,
        section_type: sectionType,
      }),
    });
  }

  /**
   * Provide clarification for a section and regenerate analysis
   */
  async provideClarification(
    sessionId: string,
    sectionType: string,
    userResponse: string
  ): Promise<ClarificationResponse> {
    return this.request('/api/provide-clarification', {
      method: 'POST',
      body: JSON.stringify({
        session_id: sessionId,
        section_type: sectionType,
        user_response: userResponse,
      }),
    });
  }

  /**
   * Accept or reject changes for a section
   */
  async acceptChanges(
    sessionId: string,
    sectionType: string,
    accepted: boolean
  ): Promise<AcceptChangesResponse> {
    return this.request('/api/accept-changes', {
      method: 'POST',
      body: JSON.stringify({
        session_id: sessionId,
        section_type: sectionType,
        accepted: accepted,
      }),
    });
  }

  /**
   * Generate the final resume based on user's accepted changes
   */
  async generateFinalResume(
    sessionId: string
  ): Promise<FinalResumeResponse> {
    return this.request('/api/generate-final-resume', {
      method: 'POST',
      body: JSON.stringify({
        session_id: sessionId,
      }),
    });
  }

  /**
   * Get the current status of an analysis session
   */
  async getSessionStatus(
    sessionId: string
  ): Promise<SessionStatusResponse> {
    return this.request(`/api/session-status/${sessionId}`);
  }

  /**
   * Health check endpoint
   */
  async healthCheck(): Promise<HealthCheckResponse> {
    return this.request('/api/health');
  }

  // Legacy support methods for backward compatibility
  
  /**
   * Legacy method - redirects to new workflow
   * @deprecated Use startAnalysis instead
   */
  async analyzeResume(
    file: File,
    jobDescription: string,
    reviewMode: boolean = true
  ): Promise<any> {
    console.warn('analyzeResume is deprecated. Use startAnalysis instead.');
    return this.startAnalysis(file, jobDescription);
  }

  /**
   * Legacy method - use provideClarification instead
   * @deprecated Use provideClarification instead
   */
  async processClarification(request: any): Promise<any> {
    console.warn('processClarification is deprecated. Use provideClarification instead.');
    return this.provideClarification(
      request.session_id,
      request.section_type,
      request.user_response
    );
  }
}

// Export singleton instance
export const resumeWiseAPI = new ResumeWiseAPI();

// Export legacy instance for backward compatibility
export const resumeCriticAPI = resumeWiseAPI;

// Export types for backward compatibility
export type { 
  AnalysisStartResponse as ResumeAnalysisResponse,
  ClarificationSubmitRequest as LegacyClarificationRequest,
  FinalResumeResponse as LegacyFinalResumeResponse,
  SectionAnalysis as ResumeBullet,
  SectionData as ResumeSection,
  SessionStatusResponse as AnalysisSummary
}; 