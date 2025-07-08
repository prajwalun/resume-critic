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
    Section-Based Resume Analysis Agent with Human-in-the-Loop Review
    
    Features:
    - Multi-format resume parsing
    - Section-based analysis (Experience, Education, Skills, Projects)
    - Single improved version per section
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
            temperature=0.1
        )
        
        self.sections: List[Dict[str, Any]] = []  # List of {id, title, original_text, improved_text, ...}
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
        """Parse the resume into sections."""
        prompt = ChatPromptTemplate.from_template("""
        You are a resume parser. Parse the following resume text into structured sections.
        
        Resume Text:
        {resume_text}
        
        For each section, extract:
        - id: section identifier (e.g., "experience", "education", "skills", "projects", "summary")
        - title: section title as it appears in the resume
        - original_text: original text from resume section
        - content_type: "experience" | "education" | "skills" | "projects" | "summary" | "other"
        
        Focus on these main sections:
        1. Experience/Work History
        2. Education
        3. Skills
        4. Projects
        5. Summary/Objective (if present)
        
        Return ONLY a valid JSON array of sections. Do not include any other text or explanations.
        
        Example format:
        [
            {{
                "id": "experience",
                "title": "Work Experience",
                "original_text": "Software Engineer at Tech Corp (2020-2023)\\n- Developed web applications using React and Node.js\\n- Led a team of 5 developers",
                "content_type": "experience"
            }},
            {{
                "id": "education",
                "title": "Education",
                "original_text": "Bachelor of Science in Computer Science\\nUniversity of Technology, 2020",
                "content_type": "education"
            }}
        ]
        
        Parse the resume now and return the JSON array:
        """)
        chain = prompt | self.llm | JsonOutputParser()
        logger.info("[DEBUG] Parsing resume into sections.")
        try:
            result = chain.invoke({"resume_text": resume_text})
            if isinstance(result, list):
                self.sections = [section for section in result if isinstance(section, dict)]
            else:
                self.sections = []
            logger.info(f"[DEBUG] Successfully parsed {len(self.sections)} sections.")
            return self.sections
        except Exception as e:
            logger.error(f"Error parsing resume sections: {e}")
            # Fallback: create a single section with the entire resume
            self.sections = [{
                "id": "resume",
                "title": "Resume",
                "original_text": resume_text,
                "content_type": "other"
            }]
            return self.sections
    
    def analyze_sections(self, job_description: str):
        """Evaluate and suggest improvements for each section as a whole."""
        for section in self.sections:
            if not section.get("original_text"):
                continue
                
            prompt = ChatPromptTemplate.from_template("""
            Analyze this resume section against the job description and provide a comprehensive evaluation and improvement suggestion.
            
            Section Type: {content_type}
            Section Title: {title}
            Original Content:
            {original_text}
            
            Job Description:
            {job_description}
            
            IMPORTANT GUIDELINES:
            1. NEVER fabricate or hallucinate content - only use information that is already present
            2. If the section is unclear or under-specified, ask for clarification instead of making assumptions
            3. Provide ONE improved version of the entire section, not individual bullet points
            4. Focus on relevance to the job description, clarity, and impact
            
            Return JSON with the following structure:
            {{
                "overall_score": 0-10,
                "category": "Experience" | "Education" | "Skills" | "Projects" | "Format",
                "impact": "High" | "Medium" | "Low",
                "analysis": "Detailed analysis of the section's strengths and weaknesses",
                "improved_section": "Complete improved version of the section",
                "reason": "Explanation of why these improvements help",
                "needs_clarification": {{
                    "required": true/false,
                    "question": "Specific question to ask the user for more details",
                    "type": "missing_metrics" | "vague_description" | "none"
                }}
            }}
            
            For the improved_section, provide a complete, professional version that:
            - Maintains all factual information from the original
            - Improves clarity, impact, and relevance to the job
            - Uses consistent formatting and professional language
            - Focuses on achievements and quantifiable results when possible
            """)
            chain = prompt | self.llm | JsonOutputParser()
            logger.info(f"[DEBUG] Analyzing section {section['id']} ({section['content_type']}).")
            
            try:
                result = chain.invoke({
                    "content_type": section.get("content_type", "other"),
                    "title": section.get("title", ""),
                    "original_text": section["original_text"],
                    "job_description": job_description
                })
                
                # Update section with analysis results
                if isinstance(section, dict):
                    section["analysis"] = result.get("analysis", "")
                    section["improved_section"] = result.get("improved_section", "")
                    section["overall_score"] = result.get("overall_score", 5)
                    section["category"] = result.get("category", "Format")
                    section["impact"] = result.get("impact", "Medium")
                    section["reason"] = result.get("reason", "")
                    section["needs_clarification"] = result.get("needs_clarification", {
                        "required": False,
                        "question": "",
                        "type": "none"
                    })
                
                logger.info(f"[DEBUG] Completed analysis for section {section['id']}.")
                
            except Exception as e:
                logger.error(f"Error analyzing section {section.get('id', 'unknown')}: {e}")
                # Set default values if analysis fails
                if isinstance(section, dict):
                    section["analysis"] = "Analysis failed"
                    section["improved_section"] = section.get("original_text", "")
                    section["overall_score"] = 5
                    section["category"] = "Format"
                    section["impact"] = "Medium"
                    section["reason"] = "Unable to analyze this section"
                    section["needs_clarification"] = {
                        "required": False,
                        "question": "",
                        "type": "none"
                    }
    
    def process_clarification(self, section_id: str, user_input: str, job_description: str):
        """Process user clarification and regenerate section improvement."""
        section = next((s for s in self.sections if isinstance(s, dict) and s.get("id") == section_id), None)
        if not section:
            raise ValueError(f"Section {section_id} not found")
        
        prompt = ChatPromptTemplate.from_template("""
        The user has provided additional details for a resume section. Please regenerate the improved version using this new information.
        
        Original Section:
        {original_text}
        
        User's Additional Details:
        {user_input}
        
        Job Description:
        {job_description}
        
        IMPORTANT: Use ONLY the information provided by the user. Do not fabricate or assume additional details.
        
        Return JSON with:
        {{
            "improved_section": "Complete improved version incorporating user's details",
            "reason": "Explanation of how the user's input improved the section"
        }}
        """)
        
        chain = prompt | self.llm | JsonOutputParser()
        
        try:
            result = chain.invoke({
                "original_text": section["original_text"],
                "user_input": user_input,
                "job_description": job_description
            })
            
            # Update section with new improvement
            if isinstance(section, dict):
                section["improved_section"] = result.get("improved_section", section.get("improved_section", ""))
                section["reason"] = result.get("reason", section.get("reason", ""))
                needs_clarification = section.get("needs_clarification", {})
                if isinstance(needs_clarification, dict):
                    needs_clarification["required"] = False
            
            improved_section = ""
            reason = ""
            if isinstance(section, dict):
                improved_section = section.get("improved_section", "")
                reason = section.get("reason", "")
            
            return {
                "success": True,
                "improved_section": improved_section,
                "reason": reason
            }
            
        except Exception as e:
            logger.error(f"Error processing clarification: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def accept_improvement(self, section_id: str, accept: bool = True):
        """Mark a section improvement as accepted or rejected."""
        if isinstance(section_id, str):
            self.accepted_improvements[section_id] = "improved" if accept else "original"
    
    def generate_final_resume(self) -> str:
        """Generate the final resume with accepted improvements."""
        final_sections = []
        
        for section in self.sections:
            if isinstance(section, dict):
                section_id = section.get("id", "")
                if section_id in self.accepted_improvements:
                    if self.accepted_improvements[section_id] == "improved":
                        final_sections.append(f"## {section.get('title', '')}\n\n{section.get('improved_section', '')}")
                    else:
                        final_sections.append(f"## {section.get('title', '')}\n\n{section.get('original_text', '')}")
                else:
                    # Default to original if no decision made
                    final_sections.append(f"## {section.get('title', '')}\n\n{section.get('original_text', '')}")
        
        return "\n\n".join(final_sections)
    
    async def analyze_resume(self, resume_text: str, job_description: str, review_mode: bool = True) -> Dict[str, Any]:
        """
        Main analysis function that orchestrates the entire resume analysis process.
        Returns a robust, predictable structure for the frontend.
        """
        try:
            logger.info("Starting comprehensive resume analysis...")
            job_keywords = self.extract_job_keywords(job_description)
            logger.info(f"Extracted {len(job_keywords)} job keywords")
            sections = self.parse_resume(resume_text)
            logger.info(f"Parsed resume into {len(sections)} sections")
            self.analyze_sections(job_description)
            logger.info("Completed section analysis")
            total_sections = len(self.sections)
            sections_needing_clarification = 0
            total_score = 0
            strong_sections = 0
            needs_improvement = 0
            for section in self.sections:
                if isinstance(section, dict):
                    needs_clarification = section.get("needs_clarification", {})
                    if isinstance(needs_clarification, dict) and needs_clarification.get("required", False):
                        sections_needing_clarification += 1
                    score = section.get("overall_score", 5)
                    if isinstance(score, (int, float)):
                        total_score += score
                        if score >= 7:
                            strong_sections += 1
                        else:
                            needs_improvement += 1
            average_score = total_score / total_sections if total_sections > 0 else 5
            analysis_id = str(uuid4())
            # Build critiques array
            critiques = []
            for section in self.sections:
                if isinstance(section, dict):
                    improved_section = section.get("improved_section", "")
                    original_text = section.get("original_text", "")
                    if improved_section and improved_section != original_text:
                        critiques.append({
                            "id": f"{analysis_id}_{section['id']}",
                            "original": original_text,
                            "suggested": improved_section,
                            "reason": section.get("reason", ""),
                            "category": section.get("category", "Format"),
                            "impact": section.get("impact", "Medium"),
                            "sectionId": section["id"],
                            "needsClarification": section.get("needs_clarification", {}).get("required", False),
                            "clarificationQuestion": section.get("needs_clarification", {}).get("question", ""),
                            "status": "pending"
                        })
            # Defensive: always return arrays/objects
            response_data = {
                "analysis_id": analysis_id,
                "sections": self.sections if isinstance(self.sections, list) else [],
                "critiques": critiques,
                "summary": {
                    "total_sections": total_sections,
                    "sections_analyzed": total_sections,
                    "sections_needing_clarification": sections_needing_clarification,
                    "overall_score": round(average_score, 1),
                    "job_keywords": job_keywords,
                    "strong_sections": strong_sections,
                    "needs_improvement": needs_improvement
                },
                "job_description": job_description,
                "review_mode": review_mode
            }
            logger.info(f"Analysis completed successfully. Generated {len(critiques)} improvement suggestions.")
            return {
                "success": True,
                "data": response_data
            }
        except Exception as e:
            logger.error(f"Error in analyze_resume: {e}")
            return {
                "success": False,
                "error": str(e)
            } 