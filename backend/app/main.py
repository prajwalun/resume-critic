"""
ResumeWise FastAPI Application

Production-ready API for ResumeWise - AI-powered resume analysis and improvement.
Provides structured section-by-section analysis with human-in-the-loop clarification.
"""

import os
from typing import Dict, Any, Optional, List
from uuid import uuid4

from fastapi import FastAPI, File, UploadFile, Form, Body, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .utils.pdf_parser import extract_resume_text, clean_resume_text
from .core.resume_agent import IterativeResumeAgent as ResumeWiseAgent
from .core.logging_config import setup_clean_logging, get_clean_logger

# Setup clean logging
setup_clean_logging()
logger = get_clean_logger(__name__)

# Judgment framework for API-level tracing
try:
    from .core.judgment_config import get_judgment_tracer
    judgment = get_judgment_tracer()
    JUDGMENT_AVAILABLE = True
except ImportError:
    judgment = None
    JUDGMENT_AVAILABLE = False

# Initialize FastAPI app
app = FastAPI(
    title="ResumeWise API",
    description="AI-powered resume analysis and improvement with human-in-the-loop clarification",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize ResumeWise agent
resume_agent = ResumeWiseAgent()

# Pydantic models for request/response validation
class AnalysisStartRequest(BaseModel):
    job_description: str = Field(..., description="Job description to analyze against")

class AnalysisStartResponse(BaseModel):
    success: bool
    session_id: Optional[str] = None
    sections: Optional[Dict[str, Any]] = None
    job_analysis: Optional[Dict[str, Any]] = None
    analysis_order: Optional[List[str]] = None
    section_analyses: Optional[Dict[str, Any]] = None  # Include all section analyses
    error: Optional[str] = None

class SectionAnalysisRequest(BaseModel):
    session_id: str = Field(..., description="Analysis session ID")
    section_type: str = Field(..., description="Type of section to analyze")

class SectionAnalysisResponse(BaseModel):
    success: bool
    analysis: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class ClarificationRequest(BaseModel):
    session_id: str = Field(..., description="Analysis session ID")
    section_type: str = Field(..., description="Type of section to clarify")
    user_response: str = Field(..., description="User's clarification response")

class ClarificationResponse(BaseModel):
    success: bool
    analysis: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class AcceptChangesRequest(BaseModel):
    session_id: str = Field(..., description="Analysis session ID")
    section_type: str = Field(..., description="Type of section")
    accepted: bool = Field(..., description="Whether changes are accepted")

class AcceptChangesResponse(BaseModel):
    success: bool
    message: Optional[str] = None
    error: Optional[str] = None

class FinalResumeRequest(BaseModel):
    session_id: str = Field(..., description="Analysis session ID")

class FinalResumeResponse(BaseModel):
    success: bool
    final_resume: Optional[str] = None
    sections: Optional[List[str]] = None
    session_id: Optional[str] = None
    error: Optional[str] = None

class SessionStatusResponse(BaseModel):
    success: bool
    session_id: Optional[str] = None
    current_phase: Optional[str] = None
    sections_analyzed: Optional[int] = None
    pending_clarifications: Optional[int] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    error: Optional[str] = None

# API Endpoints

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "ResumeWise API"}

def _trace_if_available(func):
    """Decorator to add judgment tracing if available."""
    if JUDGMENT_AVAILABLE and judgment:
        return judgment.observe(name="resume_analysis_workflow", span_type="workflow")(func)
    return func

@app.post("/api/start-analysis", response_model=AnalysisStartResponse)
@_trace_if_available
async def start_analysis(
    job_description: str = Form(...),
    file: UploadFile = File(...)
):
    """
    Start a new resume analysis session.
    
    This endpoint:
    1. Parses the uploaded resume file
    2. Analyzes the job description
    3. Initializes a new analysis session
    4. Returns session ID and parsed sections
    """
    try:
        # Validate file upload
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No file uploaded"
            )
        
        # Read and extract resume content
        resume_content = await file.read()
        resume_text = extract_resume_text(resume_content, file.filename)
        cleaned_text = clean_resume_text(resume_text)
        
        if not cleaned_text:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not extract text from resume file"
            )
        
        # Start analysis session
        result = await resume_agent.start_analysis(cleaned_text, job_description)
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get("error", "Failed to start analysis")
            )
        
        logger.info(f"📋 Analysis session {result['session_id'][:8]} - {len(result.get('sections', {}))} sections parsed")
        
        return AnalysisStartResponse(
            success=True,
            session_id=result["session_id"],
            sections=result["sections"],
            job_analysis=result["job_analysis"],
            analysis_order=result["analysis_order"],
            section_analyses=result["section_analyses"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting analysis: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@app.post("/api/analyze-section", response_model=SectionAnalysisResponse)
async def analyze_section(request: SectionAnalysisRequest):
    """
    Analyze a specific section of the resume.
    
    This endpoint:
    1. Analyzes the specified section content
    2. Determines if clarification is needed
    3. Provides improvement suggestions if possible
    4. Returns analysis results or clarification request
    """
    try:
        result = await resume_agent.analyze_section(
            request.session_id,
            request.section_type
        )
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND if "not found" in result.get("error", "").lower() else status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get("error", "Analysis failed")
            )
        
        logger.info(f"Analyzed section {request.section_type} for session {request.session_id}")
        
        return SectionAnalysisResponse(
            success=True,
            analysis=result["analysis"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing section: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@app.post("/api/provide-clarification", response_model=ClarificationResponse)
async def provide_clarification(request: ClarificationRequest):
    """
    Provide clarification for a section and regenerate analysis.
    
    This endpoint:
    1. Accepts user's clarification response
    2. Regenerates section analysis with additional context
    3. Returns updated analysis results
    """
    try:
        result = await resume_agent.provide_clarification(
            request.session_id,
            request.section_type,
            request.user_response
        )
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND if "not found" in result.get("error", "").lower() else status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get("error", "Clarification processing failed")
            )
        
        logger.info(f"Processed clarification for section {request.section_type} in session {request.session_id}")
        
        return ClarificationResponse(
            success=True,
            analysis=result["analysis"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing clarification: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@app.post("/api/accept-changes", response_model=AcceptChangesResponse)
async def accept_changes(request: AcceptChangesRequest):
    """
    Accept or reject changes for a section.
    
    This endpoint:
    1. Records user's acceptance/rejection of suggested changes
    2. Updates the analysis session state
    3. Returns confirmation message
    """
    try:
        result = await resume_agent.accept_section_changes(
            request.session_id,
            request.section_type,
            request.accepted
        )
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND if "not found" in result.get("error", "").lower() else status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get("error", "Failed to update section status")
            )
        
        logger.info(f"Updated section {request.section_type} status in session {request.session_id}")
        
        return AcceptChangesResponse(
            success=True,
            message=result["message"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error accepting changes: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@app.post("/api/generate-final-resume", response_model=FinalResumeResponse)
async def generate_final_resume(request: FinalResumeRequest):
    """
    Generate the final resume based on user's accepted changes.
    
    This endpoint:
    1. Collects all accepted/rejected changes
    2. Assembles the final resume
    3. Returns the complete formatted resume
    """
    try:
        result = await resume_agent.generate_final_resume(request.session_id)
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND if "not found" in result.get("error", "").lower() else status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get("error", "Failed to generate final resume")
            )
        
        logger.info(f"Generated final resume for session {request.session_id}")
        
        return FinalResumeResponse(
            success=True,
            final_resume=result["final_resume"],
            sections=result["sections"],
            session_id=result["session_id"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating final resume: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@app.get("/api/session-status/{session_id}", response_model=SessionStatusResponse)
async def get_session_status(session_id: str):
    """
    Get the current status of an analysis session.
    
    This endpoint:
    1. Retrieves session information
    2. Returns current phase and progress
    3. Shows pending clarifications
    """
    try:
        result = resume_agent.get_session_status(session_id)
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result.get("error", "Session not found")
            )
        
        return SessionStatusResponse(
            success=True,
            session_id=result["session_id"],
            current_phase=result["current_phase"],
            sections_analyzed=result["sections_analyzed"],
            pending_clarifications=result["pending_clarifications"],
            created_at=result["created_at"],
            updated_at=result["updated_at"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting session status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

# Legacy endpoint for backward compatibility (can be removed later)
@app.post("/api/analyze-resume")
async def analyze_resume_legacy(
    job_description: str = Form(...),
    review_mode: bool = Form(True),
    file: UploadFile = File(...)
):
    """
    Legacy endpoint for backward compatibility.
    Redirects to the new structured workflow.
    """
    try:
        # Start analysis session
        result = await start_analysis(job_description, file)
        
        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to start analysis"
            )
        
        return {
            "success": True,
            "data": {
                "analysis_id": result.session_id,
                "sections": result.sections,
                "job_analysis": result.job_analysis,
                "analysis_order": result.analysis_order,
                "message": "Analysis started. Use the new structured endpoints for section-by-section analysis."
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in legacy endpoint: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 