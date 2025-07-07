import os
import json
import logging
from typing import Dict, List, Any, Optional
from uuid import uuid4
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.runnables import RunnablePassthrough

# Judgment Labs imports
try:
    from judgeval.scorers import AnswerRelevancyScorer, FaithfulnessScorer
except ImportError:
    # Fallback if judgeval is not available
    AnswerRelevancyScorer = None
    FaithfulnessScorer = None

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ResumeAgent:
    """
    Comprehensive Resume Analysis Agent with Human-in-the-Loop Review
    
    Features:
    - Multi-format resume parsing
    - Section-based analysis
    - Bullet-point evaluation (clarity, impact, relevance)
    - Human-in-the-loop clarification process
    - Job-specific optimization
    - Judgment Labs tracing integration
    """
    
    def __init__(self, judgment_tracer=None):
        """Initialize the ResumeAgent with Judgment Labs tracing."""
        self.judgment_tracer = judgment_tracer
        
        # Initialize OpenAI client
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.1,
            api_key=api_key  # Pass as plain string for compatibility
        )
        
        self.sections = []  # List of {id, title, original_text, improved_text, ...}
        self.accepted_improvements = {}  # {section_id: "improved" | "original"}
    
    def safe_observe(self, span_type="function"):
        """Safe decorator for Judgment Labs tracing."""
        if self.judgment_tracer:
            return self.judgment_tracer.observe(span_type=span_type)
        else:
            return lambda x: x
    
    def extract_job_keywords(self, job_description: str) -> List[str]:
        """Extract key skills and requirements from job description."""
        try:
            prompt = ChatPromptTemplate.from_template("""
            Extract the most important technical skills, tools, and requirements from this job description.
            Focus on specific technologies, programming languages, frameworks, and tools.
            
            Job Description:
            {job_description}
            
            Return a JSON array of keywords/skills, maximum 20 items.
            Example: ["Python", "React", "AWS", "Docker", "PostgreSQL", "Machine Learning"]
            """)
            
            chain = prompt | self.llm | JsonOutputParser()
            result = chain.invoke({"job_description": job_description})
            
            if isinstance(result, list):
                return result[:20]  # Limit to 20 keywords
            else:
                return []
        except Exception as e:
            logger.error(f"Error extracting job keywords: {e}")
            return []
    
    def parse_resume(self, resume_text: str) -> List[Dict[str, Any]]:
        """Parse the resume into sections using a single LLM call."""
        prompt = ChatPromptTemplate.from_template("""
        Parse this resume into structured sections. For each section, extract:
        - id: section identifier (e.g., "experience", "education")
        - title: section title
        - content: full text of the section
        - original_text: original text from resume
        Return a JSON array of sections.
        Example:
        [
            {{
                "id": "experience",
                "title": "Work Experience",
                "content": "Software Engineer at Tech Corp...",
                "original_text": "Software Engineer at Tech Corp..."
            }}
        ]
        """)
        chain = prompt | self.llm | JsonOutputParser()
        logger.info("[DEBUG] Parsing resume into sections.")
        result = chain.invoke({"resume_text": resume_text})
        self.sections = result if isinstance(result, list) else []
        return self.sections
    
    def analyze_sections(self, job_description: str):
        """Evaluate and suggest improvements for each section as a whole."""
        for section in self.sections:
            prompt = ChatPromptTemplate.from_template("""
            Given the following resume section and job description, evaluate the section for clarity, impact, and relevance. Suggest improvements ONLY if needed, tailored to the job requirements. If the section is strong, say so. If clarification is needed, specify what is missing.
            
            Resume Section:
            {section_text}
            
            Job Description:
            {job_description}
            
            Return JSON:
            {{
                "needs_improvement": true/false,
                "needs_clarification": true/false,
                "clarification_question": "",
                "improved_text": "Improved section text or empty if not needed",
                "explanation": "Reasoning for suggestion or why section is strong"
            }}
            """)
            chain = prompt | self.llm | JsonOutputParser()
            logger.info(f"[DEBUG] Analyzing section {section['id']}.")
            result = chain.invoke({
                "section_text": section["content"],
                "job_description": job_description
            })
            section.update(result)
            section["clarified"] = False
            section["user_clarification"] = ""
    
    def process_clarification(self, section_id: str, user_input: str, job_description: str):
        """Use user clarification in a follow-up LLM call to improve the section."""
        section = next((s for s in self.sections if s["id"] == section_id), None)
        if not section:
            return None
        prompt = ChatPromptTemplate.from_template("""
        Given the original resume section, the job description, and the user's clarification, generate an improved version of the section. Integrate the clarification naturally. Only use information provided by the user.
        
        Original Section:
        {section_text}
        
        Job Description:
        {job_description}
        
        User Clarification:
        {user_clarification}
        
        Return improved section text only.
        """)
        chain = prompt | self.llm
        logger.info(f"[DEBUG] Processing clarification for section {section_id}.")
        improved_text = chain.invoke({
            "section_text": section["content"],
            "job_description": job_description,
            "user_clarification": user_input
        })
        section["improved_text"] = improved_text.content if hasattr(improved_text, "content") else str(improved_text)
        section["clarified"] = True
        section["user_clarification"] = user_input
        return section["improved_text"]
    
    def accept_improvement(self, section_id: str, accept: bool = True):
        self.accepted_improvements[section_id] = "improved" if accept else "original"
    
    def generate_final_resume(self) -> str:
        """Assemble the final resume using accepted improvements or original sections."""
        final_sections = []
        for section in self.sections:
            use_improved = (
                self.accepted_improvements.get(section["id"]) == "improved"
                and section.get("improved_text")
            )
            text = section["improved_text"] if use_improved else section["content"]
            final_sections.append(f"{section['title']}\n{text}\n")
        return "\n".join(final_sections)
    
    async def analyze_resume(self, resume_text: str, job_description: str, review_mode: bool = True) -> Dict[str, Any]:
        """Main function to run complete resume analysis."""
        try:
            # Extract job keywords
            job_keywords = self.extract_job_keywords(job_description)
            
            # Parse resume sections
            self.parse_resume(resume_text)
            
            # Analyze each section
            self.analyze_sections(job_description)
            
            # Generate summary
            summary = {
                "job_keywords_matched": len([kw for kw in job_keywords if any(kw.lower() in section.get("content", "").lower() for section in self.sections)])
            }
            
            # Add evaluation for the analysis
            if self.judgment_tracer and AnswerRelevancyScorer:
                self.judgment_tracer.async_evaluate(
                    scorers=[AnswerRelevancyScorer(threshold=0.7)],
                    input=f"Resume analysis for job: {job_description[:500]}...",
                    actual_output=str(summary),
                    model="gpt-4o"
                )
            
            return {
                "success": True,
                "analysis_id": str(uuid4()),
                "sections": self.sections,
                "summary": summary,
                "job_keywords": job_keywords,
                "review_mode": review_mode,
                "timestamp": "2024-01-01T00:00:00Z"
            }
            
        except Exception as e:
            logger.error(f"Error in resume analysis: {e}")
            return {
                "success": False,
                "error": str(e),
                "analysis_id": None
            } 