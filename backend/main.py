import os
import asyncio
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn
from dotenv import load_dotenv
from uuid import uuid4
import json

# Judgment Labs imports
from judgeval.tracer import Tracer, wrap
from judgeval.scorers import AnswerRelevancyScorer, FaithfulnessScorer
from judgeval.data import Example

# Import our modules
from pdf_parser import extract_resume_text, clean_resume_text
from resume_agent import ResumeAgent

# Load environment variables
load_dotenv()

# Initialize Judgment Labs tracing
def get_judgment_tracer():
    """Initialize Judgment Labs tracer with proper error handling."""
    try:
        api_key = os.getenv("JUDGMENT_API_KEY")
        
        if not api_key:
            print("Warning: JUDGMENT_API_KEY not found in environment variables")
            return None
            
        tracer_config = {
            "api_key": api_key,
            "project_name": "resume-critic-ai",
            "enable_monitoring": True
        }
            
        return Tracer(**tracer_config)
    except Exception as e:
        print(f"Warning: Could not initialize Judgment Labs tracer: {e}")
        return None

judgment = get_judgment_tracer()

# Wrap OpenAI client for automatic LLM call tracing
if judgment:
    from openai import OpenAI
    client = wrap(OpenAI(api_key=os.getenv("OPENAI_API_KEY")))
else:
    from openai import OpenAI
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Safe decorator for Judgment Labs tracing
def safe_observe(span_type="span"):
    def decorator(func):
        if judgment and hasattr(judgment, 'observe'):
            # Map custom span types to valid Judgment Labs span types
            valid_span_type = "span" if span_type == "endpoint" else span_type
            return judgment.observe(span_type=valid_span_type)(func)
        else:
            return func
    return decorator

app = FastAPI(
    title="Resume Critic AI",
    description="AI-powered resume analysis and improvement with human-in-the-loop review",
    version="2.0.0"
)

# Add CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the resume agent
resume_agent = ResumeAgent(judgment_tracer=judgment)

# In-memory storage for analysis results (in production, use a proper database)
analysis_results_store = {}

# Pydantic models for request/response
class ResumeAnalysisRequest(BaseModel):
    job_description: str
    review_mode: bool = True

class ResumeAnalysisResponse(BaseModel):
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class ClarificationRequest(BaseModel):
    analysis_id: str
    section_id: str
    bullet_id: str
    user_response: str
    clarification_type: str
    original_text: str
    question: str

class FinalResumeRequest(BaseModel):
    analysis_id: str
    accepted_changes: Dict[str, str]  # bullet_id -> "original" or "improved"

@safe_observe("span")
@app.get("/")
async def root():
    """Health check endpoint."""
    return {"message": "Resume Critic AI is running!", "version": "2.0.0"}

@safe_observe("span")
@app.post("/api/analyze-resume", response_model=ResumeAnalysisResponse)
async def analyze_resume(
    file: UploadFile = File(...),
    job_description: str = Form(...),
    review_mode: bool = Form(True)
):
    """
    Analyze a resume file and provide detailed improvement suggestions.
    
    Features:
    - Multi-format support (PDF, DOCX, DOC, TXT)
    - Section-based analysis
    - Bullet-point evaluation
    - Human-in-the-loop clarification process
    - Job-specific optimization
    """
    try:
        # Validate file type
        allowed_extensions = ['pdf', 'docx', 'doc', 'txt']
        file_extension = file.filename.lower().split('.')[-1] if file.filename else 'txt'
        if file_extension not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type. Allowed: {', '.join(allowed_extensions)}"
            )
        
        # Read and extract text from file
        await file.seek(0)
        file_content = await file.read()
        resume_text = extract_resume_text(file_content, file.filename or "resume.txt")
        
        if not resume_text:
            raise HTTPException(
                status_code=400,
                detail="Could not extract text from the uploaded file"
            )
        
        # Clean the resume text
        cleaned_text = clean_resume_text(resume_text)
        
        # Run comprehensive analysis
        analysis_results = await resume_agent.analyze_resume(
            resume_text=cleaned_text,
            job_description=job_description,
            review_mode=review_mode
        )
        
        if not analysis_results.get("success", False):
            raise HTTPException(
                status_code=500,
                detail=f"Analysis failed: {analysis_results.get('error', 'Unknown error')}"
            )
        
        # Store results for later use
        analysis_id = analysis_results.get("analysis_id") or str(uuid4())
        analysis_results_store[analysis_id] = {
            "results": analysis_results,
            "job_description": job_description,
            "resume_text": cleaned_text,
            "review_mode": review_mode
        }
        
        # Add evaluation for the analysis
        if judgment:
            judgment.async_evaluate(
                scorers=[AnswerRelevancyScorer(threshold=0.7)],
                input=f"Resume: {cleaned_text[:500]}... Job: {job_description[:500]}...",
                actual_output=str(analysis_results.get("summary", {})),
                model="gpt-4o"
            )
        
        return ResumeAnalysisResponse(
            success=True,
            data=analysis_results
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in analyze_resume: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )

@safe_observe("span")
@app.post("/api/process-clarification", response_model=ResumeAnalysisResponse)
async def process_clarification(request: ClarificationRequest):
    """
    Process user clarification and generate improved content.
    This is the core of the human-in-the-loop process where users
    provide additional context for vague or missing metrics.
    """
    try:
        # Get the original analysis
        analysis_data = analysis_results_store.get(request.analysis_id)
        if not analysis_data:
            raise HTTPException(status_code=404, detail="Analysis not found")

        # Process the clarification using the new section-level method
        improved_section = resume_agent.process_clarification(
            section_id=request.section_id,
            user_input=request.user_response,
            job_description=analysis_data["job_description"]
        )

        # Update the stored analysis with the improved section
        if "results" in analysis_data:
            for section in analysis_data["results"].get("sections", []):
                if section.get("id") == request.section_id:
                    section["improved_text"] = improved_section
                    section["clarified"] = True
                    section["user_clarification"] = request.user_response
                    break

        # Add evaluation for the clarification process
        if judgment:
            judgment.async_evaluate(
                scorers=[FaithfulnessScorer(threshold=0.8)],
                input=f"Clarification for section {request.section_id}: {request.user_response}",
                actual_output=improved_section,
                model="gpt-4o"
            )

        return ResumeAnalysisResponse(
            success=True,
            data={
                "improved_section": improved_section,
                "analysis_id": request.analysis_id,
                "message": "Clarification processed successfully"
            }
        )

    except Exception as e:
        print(f"Error processing clarification: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing clarification: {str(e)}"
        )

@safe_observe("span")
@app.post("/api/generate-final-resume", response_model=ResumeAnalysisResponse)
async def generate_final_resume(request: FinalResumeRequest):
    """
    Generate the final improved resume based on user choices.
    Users can choose which improvements to accept for each section.
    """
    try:
        # Get the original analysis
        analysis_data = analysis_results_store.get(request.analysis_id)
        if not analysis_data:
            raise HTTPException(status_code=404, detail="Analysis not found")

        # Update accepted improvements in the agent
        for section_id, choice in request.accepted_changes.items():
            resume_agent.accept_improvement(section_id, choice == "improved")

        # Generate final resume using the agent's internal state
        final_resume_text = resume_agent.generate_final_resume()

        # Add evaluation for the final resume
        if judgment:
            judgment.async_evaluate(
                scorers=[AnswerRelevancyScorer(threshold=0.8)],
                input=f"Job: {analysis_data['job_description'][:500]}... | Accepted changes: {len(request.accepted_changes)}",
                actual_output=final_resume_text[:1000],
                model="gpt-4o"
            )

        return ResumeAnalysisResponse(
            success=True,
            data={
                "final_resume": final_resume_text,
                "analysis_id": request.analysis_id,
                "message": "Final resume generated successfully"
            }
        )

    except Exception as e:
        print(f"Error generating final resume: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error generating final resume: {str(e)}"
        )

@safe_observe("span")
@app.get("/api/analysis/{analysis_id}")
async def get_analysis(analysis_id: str):
    """Retrieve a stored analysis by ID."""
    try:
        analysis_data = analysis_results_store.get(analysis_id)
        if not analysis_data:
            raise HTTPException(status_code=404, detail="Analysis not found")
        
        return ResumeAnalysisResponse(
            success=True,
            data=analysis_data["results"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error retrieving analysis: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving analysis: {str(e)}"
        )

@safe_observe("span")
@app.get("/api/health")
async def health_check():
    """Comprehensive health check endpoint."""
    return {
        "status": "healthy",
        "version": "2.0.0",
        "features": [
            "Multi-format resume parsing",
            "Section-based analysis",
            "Bullet-point evaluation",
            "Human-in-the-loop clarification",
            "Job-specific optimization",
            "Judgment Labs tracing"
        ],
        "judgment_tracing": judgment is not None,
        "openai_configured": bool(os.getenv("OPENAI_API_KEY")),
        "supported_formats": ["PDF", "DOCX", "DOC", "TXT"]
    }

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler with Judgment tracing."""
    if judgment:
        judgment.async_evaluate(
            scorers=[AnswerRelevancyScorer(threshold=0.0)],
            input=f"Error in {request.url.path}",
            actual_output=str(exc),
            model="gpt-4o"
        )
    
    return JSONResponse(
        status_code=500,
        content={"error": f"Internal server error: {str(exc)}"}
    )

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000) 