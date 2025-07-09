"""
ResumeWise - Truly Iterative Agentic Resume Analysis System

This is the ultimate agentic implementation that:
1. Generates multiple iterations of improvements
2. Self-evaluates and critiques each version
3. Refines content through multiple passes
4. Uses different analysis perspectives
5. Achieves excellence through iteration
"""

import os
import json
import logging
import asyncio
import re
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from datetime import datetime
from uuid import uuid4

from openai import AsyncOpenAI
from openai.types.chat import ChatCompletionMessageParam
from dotenv import load_dotenv

from app.utils.pdf_parser import split_resume_sections

# Judgment framework imports
from .judgment_config import (
    get_judgment_tracer, 
    get_judgment_evaluator, 
    get_judgment_monitor,
    ResumeMetrics,
    setup_judgment_environment
)

# Setup judgment environment
setup_judgment_environment()

# Get judgment instances
judgment = get_judgment_tracer()
evaluator = get_judgment_evaluator()
monitor = get_judgment_monitor()

# Load environment variables with proper path
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(os.path.dirname(current_dir))
env_path = os.path.join(backend_dir, ".env")
load_dotenv(dotenv_path=env_path)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SectionType(Enum):
    """Enum for resume section types."""
    CONTACT_INFO = "contact_info"
    SUMMARY = "summary"
    SKILLS = "skills"
    EDUCATION = "education"
    EXPERIENCE = "experience"
    PROJECTS = "projects"
    CERTIFICATIONS = "certifications"

class AnalysisPerspective(Enum):
    """Different analysis perspectives for multi-pass evaluation."""
    HIRING_MANAGER = "hiring_manager"
    TECHNICAL_LEAD = "technical_lead"
    HR_RECRUITER = "hr_recruiter"
    ATS_OPTIMIZER = "ats_optimizer"
    INDUSTRY_EXPERT = "industry_expert"
    EXECUTIVE_COACH = "executive_coach"

@dataclass
class IterationResult:
    """Results from a single iteration of improvement."""
    version: int
    content: str
    perspective: AnalysisPerspective
    quality_score: int
    strengths: List[str]
    weaknesses: List[str]
    improvement_notes: str
    timestamp: datetime

@dataclass
class ClarificationRequest:
    """Data class for clarification requests."""
    section_type: SectionType
    question: str
    context: str
    original_content: str
    reason: str
    timestamp: datetime

@dataclass
class SectionAnalysis:
    """Enhanced section analysis with iteration history."""
    section_type: SectionType
    original_content: str
    best_content: Optional[str]
    iterations: List[IterationResult]
    final_score: int
    improvement_journey: str
    needs_clarification: bool
    clarification_request: Optional[ClarificationRequest]

@dataclass
class JobAnalysis:
    """Comprehensive job analysis."""
    keywords: List[str]
    requirements: List[str]
    experience_level: str
    key_technologies: List[str]
    priorities: List[str]
    soft_skills: List[str]
    hard_skills: List[str]
    industry: str
    company_size: str
    role_type: str

class IterativeResumeAgent:
    """Truly iterative agentic resume system that achieves excellence through multiple passes."""
    
    def __init__(self):
        """Initialize the iterative agentic system."""
        load_dotenv(dotenv_path=env_path)
        
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.error("❌ OPENAI_API_KEY environment variable is not set!")
            raise ValueError("OpenAI API key is required. Please set OPENAI_API_KEY in your .env file.")
        
        try:
            from judgeval.common.tracer import wrap
            self.client = wrap(AsyncOpenAI(
                api_key=api_key,
                timeout=60.0,  # Longer timeout for iterative analysis
                max_retries=3
            ))
            logger.info("✅ Iterative Agentic OpenAI client initialized successfully with Judgment tracing")
        except ImportError:
            # Fallback if wrap is not available
            self.client = AsyncOpenAI(
                api_key=api_key,
                timeout=60.0,  # Longer timeout for iterative analysis
                max_retries=3
            )
            logger.info("✅ Iterative Agentic OpenAI client initialized successfully (without Judgment tracing)")
        except Exception as e:
            logger.error(f"❌ Failed to initialize OpenAI client: {str(e)}")
            raise
        
        # Iterative analysis configuration
        self.max_iterations = 5  # Maximum refinement iterations
        self.quality_threshold = 90  # Don't stop until we reach this score
        self.perspective_rotation = list(AnalysisPerspective)
        
        # Analysis state
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.analysis_order = [
            SectionType.SKILLS,
            SectionType.EDUCATION,
            SectionType.EXPERIENCE,
            SectionType.PROJECTS
        ]
        
        # Common formatting rules
        self.base_formatting_rules = """
CRITICAL RESUME FORMATTING RULES:
🚫 NEVER FABRICATE - Only use information that exists in the original content
🚫 NEVER ADD FAKE SKILLS - Don't mention technologies not in the original
🚫 NEVER INVENT ACHIEVEMENTS - Don't create metrics that weren't provided
🚫 NEVER HALLUCINATE EXPERIENCES - Don't add roles, projects, or accomplishments
"""

        self.conservative_rules = """
CONSERVATIVE CONTENT VERIFICATION:
1. AUDIT CHECK: Before suggesting any addition, verify it exists in original content
2. FABRICATION DETECTION: If considering adding something not in original, STOP
3. CLARIFICATION TRIGGER: Instead of fabricating, mark for user clarification
4. ENHANCEMENT ONLY: Focus on improving presentation of existing information

CONSERVATIVE ENHANCEMENT APPROACH:
- If uncertain about adding details, ask for clarification instead of guessing
- Focus on improving presentation of existing information
- Use stronger action verbs and professional language
- Reorganize content for better flow and readability
- Only add context that can be reasonably inferred from existing content
"""
        
        # Section-specific prompts with enhanced formatting rules
        self.section_prompts = {
            SectionType.SKILLS: f"""
CRITICAL RESUME FORMATTING RULES:
🚫 NEVER FABRICATE - Only use information that exists in the original content
🚫 NEVER ADD FAKE SKILLS - Don't mention technologies not in the original
🚫 NEVER INVENT ACHIEVEMENTS - Don't create metrics that weren't provided
🚫 NEVER HALLUCINATE EXPERIENCES - Don't add roles, projects, or accomplishments

🔒 CRITICAL SKILLS FORMATTING RULES - MUST FOLLOW EXACTLY:

❌ ABSOLUTELY FORBIDDEN:
- Converting structured skills to paragraph format
- Using phrases like "Proficient in", "Skilled in", "Experienced in"
- Creating sentences about skills: "Strong programming skills in..."
- Bullet points with explanations: "• JavaScript - for building applications"

✅ MANDATORY STRUCTURE PRESERVATION:
If original uses categories like:
▸ Languages: Python, HTML, CSS3, JavaScript, TypeScript
▸ Framework and Libraries: React Native, Django, Node.js

THEN OUTPUT MUST MAINTAIN EXACT SAME STRUCTURE:
▸ Languages: Python, HTML, CSS3, JavaScript, TypeScript  
▸ Framework and Libraries: React Native, Django, Node.js

📋 SKILLS SECTION FORMATTING REQUIREMENTS:
✅ PRESERVE original categorization markers (▸, bullets, colons)
✅ MAINTAIN comma-separated lists within categories
✅ KEEP same category names from original
✅ ONLY reorganize existing skills - NEVER add new ones
✅ Fix minor formatting inconsistencies (spacing, capitalization)

EXAMPLE - CORRECT TRANSFORMATION:
ORIGINAL:
Languages: Python, HTML, CSS3, JavaScript, TypeScript,
Framework and Libraries: React Native, Django, Node.js, NestJS, Langchain, MCP

IMPROVED:
▸ Languages: Python, HTML, CSS3, JavaScript, TypeScript
▸ Framework and Libraries: React Native, Django, Node.js, NestJS, Langchain, MCP

EXAMPLE - FORBIDDEN TRANSFORMATION:
❌ NEVER DO THIS:
"• Proficient in programming languages including Python, JavaScript, and TypeScript, with experience in web development frameworks such as React and Django."

🔒 STRUCTURE PRESERVATION PROTOCOL:
1. Identify the exact formatting pattern in original (bullets, categories, lists)
2. PRESERVE that exact pattern in improved version
3. Only clean up spacing, fix typos, improve organization within existing structure
4. NEVER convert lists to paragraphs or sentences

{self.conservative_rules}

OUTPUT: Return ONLY the improved skills content maintaining the EXACT structural format of the original. No explanations or descriptions.
""",
            SectionType.EXPERIENCE: f"""
{self.base_formatting_rules}

💼 EXPERIENCE Section: Company, role, dates, bullet points of achievements
   - Only enhance existing bullet points, never add new fake ones
   - Do NOT invent technologies or responsibilities not mentioned
   - Use action verbs and quantify achievements when data exists
   - Format: Company | Role | Dates, then bullet points of accomplishments

{self.conservative_rules}

OUTPUT: Return ONLY the improved {SectionType.EXPERIENCE.value} content. No explanations or descriptions.
""",
            SectionType.EDUCATION: f"""
{self.base_formatting_rules}

🎓 CRITICAL EDUCATION FORMATTING RULES - MUST FOLLOW EXACTLY:

❌ ABSOLUTELY FORBIDDEN:
- Converting course names into "project" descriptions
- Fabricating project titles from coursework listings
- Adding achievements not mentioned in original education
- Creating experience bullets from educational content
- Turning "Data Structures" coursework into "Data Structures Project"

✅ EDUCATION SECTION REQUIREMENTS:
- Institution name, degree, graduation date/timeline
- GPA if provided in original
- Relevant coursework AS COURSEWORK (not projects)
- Honors/awards if mentioned in original
- Clean, professional educational formatting

🔒 STRUCTURE PRESERVATION FOR EDUCATION:
If original shows:
California State University, Dominguez Hill Aug 2023 – Dec 2025 (Expected)
Master of Science in Computer Science, GPA: 3.8 California, US
Coursework: Data Structures, Algorithm Analysis, Object Oriented Analysis

THEN OUTPUT MUST MAINTAIN EDUCATIONAL FORMAT:
**California State University, Dominguez Hills**
Master of Science in Computer Science, Aug 2023 – Dec 2025 (Expected), GPA: 3.8
- Relevant Coursework: Data Structures, Algorithm Analysis, Object Oriented Analysis

❌ NEVER CONVERT TO PROJECT FORMAT:
"- Collaborative Project: Led a team of 4 in a Software Project course..."
"- Data Science Project: Analyzed real-world datasets..."

✅ PROPER EDUCATION ENHANCEMENT:
- Clean up formatting and spacing
- Fix institution name spelling/formatting
- Organize coursework in clean lists
- Maintain academic tone and structure
- Only enhance presentation of existing educational content

{self.conservative_rules}

OUTPUT: Return ONLY the improved {SectionType.EDUCATION.value} content maintaining proper educational formatting. No explanations or descriptions.
""",
            SectionType.PROJECTS: f"""
{self.base_formatting_rules}

🛠️ PROJECTS Section: Project name, brief description, technologies used
   - Only work with projects explicitly mentioned in original
   - Do NOT add fake projects even if they match job requirements
   - Format: Project Name | Brief Description | Technologies Used
   - Focus on impact and outcomes when mentioned in original

{self.conservative_rules}

OUTPUT: Return ONLY the improved {SectionType.PROJECTS.value} content. No explanations or descriptions.
"""
        }
    
    @judgment.observe(name="resume_analysis_session", span_type="chain")
    async def start_analysis(self, resume_text: str, job_description: str) -> Dict[str, Any]:
        """Start iterative analysis with multiple improvement cycles."""
        session_id = str(uuid4())
        
        # Log analysis start for monitoring
        monitor.log_agent_action("analysis_started", {
            "session_id": session_id,
            "resume_length": len(resume_text),
            "job_description_length": len(job_description),
            "timestamp": datetime.now().isoformat()
        })
        
        try:
            logger.info(f"🚀 Starting ITERATIVE AGENTIC analysis for session {session_id}")
            
            # Parse resume sections
            parsed_sections = await self._parse_resume_sections(resume_text)
            
            # Comprehensive job analysis
            job_analysis = await self._analyze_job_description_comprehensive(job_description)
            
            # Initialize session with accepted changes tracking
            self.sessions[session_id] = {
                "id": session_id,
                "resume_text": resume_text,
                "job_description": job_description,
                "job_analysis": job_analysis,
                "sections": parsed_sections,
                "section_analyses": {},
                "accepted_changes": {},  # Track accepted/rejected changes per section
                "created_at": datetime.now().isoformat(),
            }
            
            # ITERATIVE ANALYSIS: Process each section through multiple improvement cycles
            for section_type in self.analysis_order:
                section_key = section_type.value
                
                if section_key in parsed_sections and parsed_sections[section_key]["content"].strip():
                    logger.info(f"🔄 Starting iterative improvement for {section_key}")
                    
                    try:
                        analysis = await self._iterative_section_improvement(
                            parsed_sections[section_key]["content"],
                            section_type,
                            job_analysis,
                            parsed_sections
                        )
                        self.sessions[session_id]["section_analyses"][section_key] = analysis
                        
                        logger.info(f"✅ Completed iterative analysis for {section_key}: "
                                  f"{len(analysis.iterations)} iterations, final score: {analysis.final_score}")
                    except Exception as e:
                        logger.error(f"❌ Error in iterative analysis for {section_key}: {str(e)}")
                        # Create fallback analysis
                        self.sessions[session_id]["section_analyses"][section_key] = SectionAnalysis(
                            section_type=section_type,
                            original_content=parsed_sections[section_key]["content"],
                            best_content=None,
                            iterations=[],
                            final_score=50,
                            improvement_journey="Iterative analysis temporarily unavailable.",
                            needs_clarification=False,
                            clarification_request=None
                        )
            
            return {
                "success": True,
                "session_id": session_id,
                "sections": parsed_sections,
                "job_analysis": job_analysis.__dict__,
                "analysis_order": [section.value for section in self.analysis_order],
                "section_analyses": {
                    section_type: {
                        "section_type": analysis.section_type.value,
                        "original_content": analysis.original_content,
                        "improved_content": analysis.best_content,
                        "score": analysis.final_score,
                        "feedback": analysis.improvement_journey,
                        "iteration_count": len(analysis.iterations),
                        "needs_clarification": analysis.needs_clarification,
                        "clarification_request": {
                            "question": analysis.clarification_request.question,
                            "context": analysis.clarification_request.context,
                            "reason": analysis.clarification_request.reason
                        } if analysis.clarification_request else None
                    } for section_type, analysis in self.sessions[session_id]["section_analyses"].items()
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Error starting iterative analysis: {str(e)}")
            
            # Log analysis error
            monitor.log_error("analysis_error", {
                "session_id": session_id,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })
            
            return {
                "success": False,
                "error": str(e)
            }
    
    @judgment.observe(name="section_improvement", span_type="chain")
    async def _iterative_section_improvement(
        self,
        content: str,
        section_type: SectionType,
        job_analysis: JobAnalysis,
        all_sections: Dict[str, Dict[str, Any]]
    ) -> SectionAnalysis:
        """Core iterative improvement engine - keeps improving until excellence."""
        
        # Initialize monitoring for this section
        monitor.log_agent_action("section_analysis_started", {
            "section_type": section_type.value,
            "original_length": len(content),
            "timestamp": datetime.now().isoformat()
        })
        
        iterations = []
        current_content = content
        best_content = content
        best_score = 0
        
        logger.info(f"🎯 Starting iterative improvement for {section_type.value}")
        
        # ITERATION LOOP: Keep improving until we reach excellence
        for iteration in range(self.max_iterations):
            perspective = self.perspective_rotation[iteration % len(self.perspective_rotation)]
            
            logger.info(f"🔄 Iteration {iteration + 1}/{self.max_iterations} - Perspective: {perspective.value}")
            
            try:
                # STEP 1: Generate improvement from current perspective
                improved_content = await self._generate_content_with_perspective(
                    current_content, section_type, job_analysis, perspective, iteration + 1
                )
                
                # STEP 2: CRITICAL VERIFICATION - Check if suggestion maintains format integrity
                verification_result = await self._verify_suggestion_quality(
                    content, improved_content, section_type  # Use original content as baseline
                )
                
                # Log iteration attempt for monitoring
                monitor.log_iteration_attempt(
                    section_type.value, 
                    iteration + 1, 
                    verification_result["is_valid"]
                )
                
                # STEP 3: Handle verification results
                if not verification_result["is_valid"]:
                    logger.warning(f"🚫 Iteration {iteration + 1} rejected due to verification issues:")
                    for issue in verification_result["issues"]:
                        logger.warning(f"  - {issue['severity']}: {issue['description']}")
                    
                    # Log verification failure
                    monitor.log_error("verification_failure", {
                        "section_type": section_type.value,
                        "iteration": iteration + 1,
                        "issues": verification_result["issues"]
                    })
                    
                    # If critical issues, try format-preserving cleanup instead
                    if verification_result["recommendation"] == "reject":
                        logger.info("🔧 Applying format-preserving cleanup instead")
                        improved_content = await self._ensure_proper_formatting(content, section_type)
                        
                        # Re-verify the cleanup
                        cleanup_verification = await self._verify_suggestion_quality(content, improved_content, section_type)
                        if not cleanup_verification["is_valid"]:
                            logger.warning("🚫 Even format cleanup failed verification - keeping original")
                            improved_content = content
                
                # STEP 4: PRIMARY SCORING SYSTEM - Fast agent decision making
                primary_score = await self._score_content_quality(
                    content=improved_content,
                    section_type=section_type,
                    job_analysis=job_analysis
                )
                
                # Apply verification penalties to primary score
                quality_score = primary_score
                if verification_result["issues"]:
                    penalty = sum(10 if issue["severity"] == "critical" else 
                                 5 if issue["severity"] == "high" else 2 
                                 for issue in verification_result["issues"])
                    quality_score = max(1, primary_score - penalty)
                    logger.info(f"📉 Applied verification penalty: -{penalty} points (final score: {quality_score})")
                
                # STEP 5: JUDGMENT FRAMEWORK - Comprehensive async evaluation (non-blocking)
                self._trigger_judgment_evaluation(
                    original_content=content,
                    improved_content=improved_content,
                    section_type=section_type,
                    job_analysis=job_analysis,
                    primary_score=quality_score,
                    iteration=iteration + 1
                )
                
                # STEP 6: Get detailed evaluation for iteration logging (lightweight)
                evaluation = await self._self_evaluate_content(
                    improved_content, section_type, job_analysis, perspective
                )
                
                # STEP 7: Create iteration result using primary score
                iteration_result = IterationResult(
                    version=iteration + 1,
                    content=improved_content,
                    perspective=perspective,
                    quality_score=quality_score,  # Use primary score for agent decisions
                    strengths=evaluation["strengths"],
                    weaknesses=evaluation["weaknesses"] + [f"Verification: {issue['description']}" for issue in verification_result["issues"]],
                    improvement_notes=evaluation["improvement_notes"],
                    timestamp=datetime.now()
                )
                
                iterations.append(iteration_result)
                
                # STEP 8: Track best version (considering verification)
                if quality_score > best_score:
                    best_content = improved_content
                    best_score = quality_score
                    logger.info(f"🏆 New best version! Score: {best_score} (with verification)")
                
                # STEP 9: Check if we've reached excellence (with verification)
                if quality_score >= self.quality_threshold:
                    logger.info(f"🎉 Excellence achieved! Score: {quality_score} >= {self.quality_threshold}")
                    break
                
                # STEP 10: If not excellent, use critique to improve further
                if iteration < self.max_iterations - 1:
                    current_content = await self._refine_based_on_critique(
                        improved_content, evaluation["weaknesses"], section_type, job_analysis
                    )
                
                # Small delay to avoid rate limiting
                await asyncio.sleep(0.5)
                
            except Exception as e:
                # Log iteration error
                monitor.log_error("iteration_error", {
                    "section_type": section_type.value,
                    "iteration": iteration + 1,
                    "error": str(e)
                })
                logger.error(f"❌ Error in iteration {iteration + 1}: {str(e)}")
                break
        
        # Generate improvement journey narrative with accurate change detection
        improvement_journey = await self._generate_improvement_narrative(iterations, section_type, content)
        
        # Check if we need format-first improvements regardless of JD requirements
        if best_score < 80 or not iterations:  # If quality is low or no iterations ran
            logger.info(f"🔧 Applying format-first improvements for {section_type.value}")
            format_improved = await self._ensure_proper_formatting(content, section_type)
            
            # Check if format improvement actually made changes
            format_changes = self._detect_actual_changes(content, format_improved)
            if format_changes["has_meaningful_changes"]:
                best_content = format_improved
                improvement_journey = ". ".join(format_changes["specific_changes"]) + "."
                logger.info(f"✅ Format-first improvements applied: {improvement_journey}")
        
        # Final monitoring log
        monitor.log_agent_action("section_analysis_completed", {
            "section_type": section_type.value,
            "iterations_completed": len(iterations),
            "final_score": best_score,
            "improvement_made": best_content != content,
            "timestamp": datetime.now().isoformat()
        })
        
        # JUDGMENT EVALUATION - Final evaluation of agent decision
        evaluator.evaluate_agent_decision(
            decision_context=f"Section: {section_type.value}, Original length: {len(content)}, Iterations: {len(iterations)}",
            decision_made=f"Applied {len(iterations)} iterations, final score: {best_score}",
            reasoning=improvement_journey,
            confidence_score=best_score / 100.0
        )
        
        return SectionAnalysis(
            section_type=section_type,
            original_content=content,
            best_content=best_content,
            iterations=iterations,
            final_score=best_score,
            improvement_journey=improvement_journey,
            needs_clarification=False,
            clarification_request=None
        )
    
    # @judgment.observe(name="generate_content_with_perspective", span_type="llm")  # Removed for cleaner traces
    async def _generate_content_with_perspective(
        self,
        content: str,
        section_type: SectionType,
        job_analysis: JobAnalysis,
        perspective: AnalysisPerspective,
        iteration: int
    ) -> str:
        """Generate improved content from a specific professional perspective."""
        
        perspective_prompts = {
            AnalysisPerspective.HIRING_MANAGER: f"""
You are a senior hiring manager at a {job_analysis.company_size} {job_analysis.industry} company with 10+ years of experience hiring {job_analysis.experience_level}-level professionals.

HIRING MANAGER PERSPECTIVE:
- Focus on BUSINESS IMPACT and measurable results
- Look for evidence of problem-solving and leadership
- Prioritize relevant experience and skill progression
- Ensure content demonstrates value to the organization
- Emphasize achievements that solve business problems
- Include metrics that matter to business outcomes

HIRING PRIORITIES for this role:
- Must demonstrate: {', '.join(job_analysis.priorities[:5])}
- Technical requirements: {', '.join(job_analysis.key_technologies[:8])}
- Experience level: {job_analysis.experience_level}

Transform this {section_type.value} section to make me want to immediately schedule an interview:""",

            AnalysisPerspective.TECHNICAL_LEAD: f"""
You are a technical lead/architect with deep expertise in {job_analysis.industry} technology stacks, evaluating candidates for technical excellence.

TECHNICAL LEAD PERSPECTIVE:
- Focus on TECHNICAL DEPTH and implementation details
- Look for evidence of system design and architecture skills
- Prioritize relevant technologies and frameworks
- Ensure content demonstrates technical problem-solving
- Include specific technologies, methodologies, and approaches
- Show technical leadership and mentoring capabilities

TECHNICAL REQUIREMENTS:
- Core technologies: {', '.join(job_analysis.key_technologies[:10])}
- Required skills: {', '.join(job_analysis.hard_skills[:8])}
- Experience level: {job_analysis.experience_level}

Enhance this {section_type.value} section to demonstrate exceptional technical competency:""",

            AnalysisPerspective.HR_RECRUITER: f"""
You are an experienced technical recruiter who knows what makes candidates stand out in a competitive market.

HR RECRUITER PERSPECTIVE:
- Focus on MARKETABILITY and competitive positioning
- Ensure content passes ATS systems with right keywords
- Optimize for searchability and initial screening
- Include relevant certifications and credentials
- Format for maximum readability and impact
- Balance technical skills with communication abilities

MARKET POSITIONING:
- Target role: {job_analysis.experience_level} {job_analysis.role_type}
- Industry: {job_analysis.industry}
- Key differentiators needed: {', '.join(job_analysis.priorities[:6])}

Optimize this {section_type.value} section for maximum market appeal and ATS compatibility:""",

            AnalysisPerspective.ATS_OPTIMIZER: f"""
You are an ATS (Applicant Tracking System) optimization expert focused on ensuring resumes pass automated screening.

ATS OPTIMIZATION PERSPECTIVE:
- Focus on KEYWORD DENSITY and semantic matching
- Ensure proper formatting and structure
- Include exact terminology from job descriptions
- Optimize for parsing algorithms and ranking systems
- Use industry-standard section headers and formatting
- Balance keyword optimization with readability

ATS OPTIMIZATION TARGETS:
- Primary keywords: {', '.join(job_analysis.keywords[:15])}
- Required technologies: {', '.join(job_analysis.key_technologies[:10])}
- Industry terms: {job_analysis.industry} terminology

Optimize this {section_type.value} section for maximum ATS scoring and automated ranking:""",

            AnalysisPerspective.INDUSTRY_EXPERT: f"""
You are a recognized expert in the {job_analysis.industry} industry with deep knowledge of current trends, best practices, and market demands.

INDUSTRY EXPERT PERSPECTIVE:
- Focus on INDUSTRY RELEVANCE and current best practices
- Include cutting-edge technologies and methodologies
- Demonstrate understanding of industry challenges
- Use proper industry terminology and standards
- Show awareness of industry trends and future direction
- Position candidate as industry-aware professional

INDUSTRY CONTEXT:
- Industry: {job_analysis.industry}
- Current trends: emerging technologies and methodologies
- Market demands: {', '.join(job_analysis.priorities[:6])}
- Required expertise: {', '.join(job_analysis.hard_skills[:8])}

Enhance this {section_type.value} section with deep industry expertise and market awareness:""",

            AnalysisPerspective.EXECUTIVE_COACH: f"""
You are an executive coach specializing in career advancement for {job_analysis.experience_level}-level professionals in {job_analysis.industry}.

EXECUTIVE COACH PERSPECTIVE:
- Focus on CAREER PROGRESSION and professional growth
- Emphasize leadership potential and strategic thinking
- Include soft skills and emotional intelligence indicators
- Show increasing responsibility and impact over time
- Demonstrate communication and collaboration abilities
- Position for next-level career advancement

CAREER DEVELOPMENT FOCUS:
- Current level: {job_analysis.experience_level}
- Target growth: towards {job_analysis.role_type} excellence
- Leadership indicators: {', '.join(job_analysis.soft_skills[:6])}
- Professional development areas: strategic thinking, team leadership

Elevate this {section_type.value} section to showcase executive potential and career trajectory:"""
        }
        
        system_prompt = perspective_prompts[perspective]
        
        messages = [
            {
                "role": "system",
                "content": f"""{system_prompt}

ITERATION CONTEXT: This is iteration {iteration}. Build upon any previous improvements while addressing remaining weaknesses.

CRITICAL RESUME FORMATTING RULES:
🚫 NEVER FABRICATE - Only use information that exists in the original content
🚫 NEVER ADD FAKE SKILLS - Don't mention technologies not in the original
🚫 NEVER INVENT ACHIEVEMENTS - Don't create metrics that weren't provided
🚫 NEVER HALLUCINATE EXPERIENCES - Don't add roles, projects, or accomplishments

SECTION-SPECIFIC FORMATTING STANDARDS:
📋 SKILLS Section: Keep as bullet points or comma-separated lists, NOT paragraphs
   - Only list technologies/tools that are explicitly mentioned in original
   - Do NOT add skills based on job description requirements
   - Do NOT write explanatory sentences about proficiency levels
   - Format: "• Python, JavaScript, React, Node.js" or "Python • JavaScript • React"

🎓 EDUCATION Section: Institution, degree, dates, relevant coursework only
   - Do NOT add fake projects or achievements not mentioned in original
   - Do NOT fabricate coursework that wasn't listed
   - Do NOT add technologies or skills under education unless they were coursework
   - Format: Institution, Degree, Date, GPA (if provided), Listed Coursework

💼 EXPERIENCE Section: Company, role, dates, bullet points of achievements
   - Only enhance existing bullet points, never add new fake ones
   - Do NOT invent technologies or responsibilities not mentioned

🛠️ PROJECTS Section: Project name, brief description, technologies used
   - Only work with projects explicitly mentioned in original
   - Do NOT add fake projects even if they match job requirements

CONSERVATIVE CONTENT VERIFICATION:
1. AUDIT CHECK: Before suggesting any addition, verify it exists in original content
2. FABRICATION DETECTION: If considering adding something not in original, STOP
3. CLARIFICATION TRIGGER: Instead of fabricating, mark for user clarification
4. ENHANCEMENT ONLY: Focus on improving presentation of existing information

TRANSFORMATION REQUIREMENTS:
1. PRESERVE ALL FACTUAL INFORMATION - Never fabricate experiences or achievements
2. IMPROVE EXISTING CONTENT - Enhance what's already there without adding false info
3. CLARIFY AND STRUCTURE - Reorganize for better readability and impact
4. PROFESSIONAL LANGUAGE - Use industry-appropriate terminology and action verbs
5. PROPER FORMATTING - Maintain section-appropriate structure (bullets vs paragraphs)
6. KEYWORD OPTIMIZATION - Only integrate keywords that can be naturally applied to existing content
7. QUANTIFY WHEN POSSIBLE - If metrics exist, highlight them; if not, don't invent them

CONSERVATIVE ENHANCEMENT APPROACH:
- If uncertain about adding details, ask for clarification instead of guessing
- Focus on improving presentation of existing information
- Use stronger action verbs and professional language
- Reorganize content for better flow and readability
- Only add context that can be reasonably inferred from existing content

OUTPUT: Return ONLY the improved {section_type.value} content. No explanations or descriptions."""
            },
            {
                "role": "user",
                "content": f"Iteration {iteration} - {perspective.value} perspective enhancement:\n\n{content}"
            }
        ]
        
        response = await self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.4,
            max_tokens=2000
        )
        
        return response.choices[0].message.content.strip()
    
    async def _self_evaluate_content(
        self,
        content: str,
        section_type: SectionType,
        job_analysis: JobAnalysis,
        perspective: AnalysisPerspective
    ) -> Dict[str, Any]:
        """Self-evaluate content quality and identify areas for improvement."""
        
        messages = [
            {
                "role": "system",
                "content": f"""You are an expert resume evaluator conducting a rigorous quality assessment from a {perspective.value} perspective.

EVALUATION CRITERIA:
1. CONTENT QUALITY (25 points): Accuracy, relevance, completeness
2. PRESENTATION (25 points): Professional language, structure, formatting
3. IMPACT DEMONSTRATION (25 points): Metrics, achievements, results
4. JOB ALIGNMENT (25 points): Keyword match, requirement coverage, relevance

SCORING SCALE:
- 95-100: Exceptional, industry-leading quality
- 90-94: Excellent, highly competitive
- 85-89: Very good, strong candidate presentation
- 80-84: Good, solid professional quality
- 75-79: Adequate, some improvements needed
- 70-74: Below average, notable weaknesses
- Below 70: Poor quality, major improvements required

TARGET JOB CONTEXT:
- Role: {job_analysis.experience_level} {job_analysis.role_type}
- Industry: {job_analysis.industry}
- Required skills: {', '.join(job_analysis.key_technologies[:10])}
- Priorities: {', '.join(job_analysis.priorities[:8])}

EVALUATION TASK: Provide detailed analysis with specific feedback.

Return ONLY a JSON object:
{{
  "quality_score": integer (0-100),
  "strengths": array of strings (3-5 specific strengths),
  "weaknesses": array of strings (3-5 specific areas for improvement),
  "improvement_notes": string (detailed suggestions for next iteration),
  "keyword_coverage": integer (0-100, how well it covers required keywords),
  "professional_impact": integer (0-100, how compelling and impactful it is)
}}"""
            },
            {
                "role": "user",
                "content": f"Evaluate this {section_type.value} content from {perspective.value} perspective:\n\n{content}"
            }
        ]
        
        response = await self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.1
        )
        
        try:
            return json.loads(response.choices[0].message.content)
        except:
            # Fallback evaluation
            return {
                "quality_score": 75,
                "strengths": ["Professional presentation", "Relevant content"],
                "weaknesses": ["Could use more specific metrics", "Needs stronger action verbs"],
                "improvement_notes": "Focus on quantifying achievements and using more impactful language.",
                "keyword_coverage": 70,
                "professional_impact": 75
            }
    
    async def _refine_based_on_critique(
        self,
        content: str,
        weaknesses: List[str],
        section_type: SectionType,
        job_analysis: JobAnalysis
    ) -> str:
        """Refine content based on identified weaknesses."""
        
        weakness_focus = "; ".join(weaknesses[:3])
        
        messages = [
            {
                "role": "system",
                "content": f"""You are a perfectionist resume editor focused on addressing specific weaknesses to achieve excellence.

REFINEMENT MISSION: Address these specific weaknesses while preserving all strengths:
{weakness_focus}

REFINEMENT STRATEGY:
1. TARGET SPECIFIC ISSUES - Address each weakness directly
2. PRESERVE STRENGTHS - Keep what's working well
3. ENHANCE IMPACT - Make every word count
4. ADD MISSING ELEMENTS - Include metrics, keywords, achievements as needed
5. PROFESSIONAL POLISH - Ensure industry-appropriate language

TARGET CONTEXT:
- Role: {job_analysis.experience_level} {job_analysis.role_type}
- Industry: {job_analysis.industry}
- Required focus: {', '.join(job_analysis.priorities[:5])}

CRITICAL: Make focused improvements that directly address the identified weaknesses.

OUTPUT: Return ONLY the refined {section_type.value} content."""
            },
            {
                "role": "user",
                "content": f"Refine this content to address weaknesses: {weakness_focus}\n\n{content}"
            }
        ]
        
        response = await self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.3
        )
        
        return response.choices[0].message.content.strip()
    
    async def _generate_improvement_narrative(
        self,
        iterations: List[IterationResult],
        section_type: SectionType,
        original_content: str = None
    ) -> str:
        """Generate accurate improvement summary based on actual changes detected."""
        
        if not iterations:
            return "No changes applied."
        
        best_iteration = max(iterations, key=lambda x: x.quality_score)
        
        # Detect actual changes made
        if original_content:
            changes_analysis = self._detect_actual_changes(original_content, best_iteration.content)
            
            # If no meaningful changes were made
            if not changes_analysis["has_meaningful_changes"]:
                if changes_analysis["similarity_score"] > 0.98:
                    return "Content reviewed - no improvements needed."
                else:
                    return "Minor formatting adjustments applied."
            
            # If meaningful changes were made, describe them accurately
            if changes_analysis["specific_changes"]:
                return ". ".join(changes_analysis["specific_changes"]) + "."
        
        # Fallback to section-specific messages if we can't detect changes
        if section_type == SectionType.SKILLS:
            return "Skills organization reviewed and optimized."
        elif section_type == SectionType.EXPERIENCE:
            return "Experience descriptions enhanced for clarity."
        elif section_type == SectionType.EDUCATION:
            return "Educational background formatting improved."
        elif section_type == SectionType.PROJECTS:
            return "Project presentations refined."
        else:
            return "Content formatting reviewed."
    
    async def _ensure_proper_formatting(self, content: str, section_type: SectionType) -> str:
        """
        Proactively fix formatting issues regardless of JD requirements.
        This ensures content follows baseline resume format standards.
        """
        
        # Check if content needs structural improvements
        needs_formatting = self._assess_formatting_needs(content, section_type)
        
        if not needs_formatting:
            return content  # Already well-formatted
        
        logger.info(f"🔧 Content needs formatting improvements: {', '.join(needs_formatting)}")
        
        # Apply format-first improvements based on section type
        if section_type == SectionType.SKILLS:
            return await self._format_skills_section(content)
        elif section_type == SectionType.EXPERIENCE:
            return await self._format_experience_section(content)
        elif section_type == SectionType.EDUCATION:
            return await self._format_education_section(content)
        elif section_type == SectionType.PROJECTS:
            return await self._format_projects_section(content)
        else:
            return await self._format_generic_section(content)
    
    def _assess_formatting_needs(self, content: str, section_type: SectionType) -> List[str]:
        """Assess what formatting improvements are needed."""
        issues = []
        
        # Check for common formatting issues
        lines = [line.strip() for line in content.split('\n') if line.strip()]
        
        # Skills section specific checks
        if section_type == SectionType.SKILLS:
            # Check if skills are in paragraph format (bad)
            if any(len(line.split()) > 8 for line in lines):
                issues.append("paragraph_format")
            
            # Check for missing categorization
            if ':' not in content and len(lines) > 3:
                issues.append("missing_categories")
            
            # Check for inconsistent bullet formatting
            bullets = ['▸', '•', '-', '*']
            bullet_count = sum(content.count(b) for b in bullets)
            if bullet_count < len(lines) // 2:
                issues.append("missing_bullets")
        
        # Experience section checks
        elif section_type == SectionType.EXPERIENCE:
            # Check for missing bullet points
            if content.count('•') + content.count('-') + content.count('▸') < len(lines) // 3:
                issues.append("missing_bullets")
            
            # Check for inconsistent formatting
            if not any(line.startswith(('•', '-', '▸')) for line in lines[1:]):
                issues.append("inconsistent_bullets")
        
        # Education section checks
        elif section_type == SectionType.EDUCATION:
            # Check for overly verbose format
            if any(len(line.split()) > 15 for line in lines):
                issues.append("verbose_format")
        
        # Projects section checks
        elif section_type == SectionType.PROJECTS:
            # Check for missing structure
            if content.count(':') < len(lines) // 4:
                issues.append("missing_structure")
        
        return issues
    
    async def _format_skills_section(self, content: str) -> str:
        """Apply professional formatting to skills section."""
        
        prompt = f"""
        FORMAT the following skills section to follow professional resume standards:
        
        REQUIREMENTS:
        - Use structured categorization with categories like: Languages, Frameworks, Databases, Tools, Cloud
        - Format as: ▸ Category: skill1, skill2, skill3
        - NO paragraph format allowed
        - NO sentences like "Proficient in..." or "Skilled in..."
        - Keep all original skills, just reorganize structure
        - Use consistent bullet formatting with ▸ symbol
        
        ORIGINAL SKILLS:
        {content}
        
        Return ONLY the formatted skills section:
        """
        
        response = await self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1
        )
        
        return response.choices[0].message.content.strip()
    
    async def _format_experience_section(self, content: str) -> str:
        """Apply professional formatting to experience section."""
        
        prompt = f"""
        FORMAT the following experience section for professional resume standards:
        
        REQUIREMENTS:
        - Use consistent bullet points (▸ or •)
        - Each bullet should be concise and action-oriented
        - Maintain original content, improve structure only
        - No fabrication allowed
        
        ORIGINAL EXPERIENCE:
        {content}
        
        Return ONLY the formatted experience section:
        """
        
        response = await self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1
        )
        
        return response.choices[0].message.content.strip()
    
    async def _format_education_section(self, content: str) -> str:
        """Apply professional formatting to education section."""
        
        prompt = f"""
        FORMAT the following education section for professional resume standards:
        
        REQUIREMENTS:
        - Keep educational entries concise and structured
        - Include degree, institution, year in clean format
        - NO fabricated projects or coursework details
        - Maintain original content accuracy
        
        ORIGINAL EDUCATION:
        {content}
        
        Return ONLY the formatted education section:
        """
        
        response = await self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1
        )
        
        return response.choices[0].message.content.strip()
    
    async def _format_projects_section(self, content: str) -> str:
        """Apply professional formatting to projects section."""
        
        prompt = f"""
        FORMAT the following projects section for professional resume standards:
        
        REQUIREMENTS:
        - Use clear project titles and descriptions
        - Include technologies used in consistent format
        - Maintain original project details - NO fabrication
        - Use bullet points for project details
        
        ORIGINAL PROJECTS:
        {content}
        
        Return ONLY the formatted projects section:
        """
        
        response = await self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1
        )
        
        return response.choices[0].message.content.strip()
    
    async def _format_generic_section(self, content: str) -> str:
        """Apply basic professional formatting to any section."""
        
        prompt = f"""
        FORMAT the following resume section for professional standards:
        
        REQUIREMENTS:
        - Use consistent formatting and structure
        - Improve readability without changing content
        - No fabrication or content addition allowed
        - Maintain original information accuracy
        
        ORIGINAL CONTENT:
        {content}
        
        Return ONLY the formatted content:
        """
        
        response = await self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1
        )
        
        return response.choices[0].message.content.strip()
    
    async def _detect_fabrication_and_clarify(self, section_type: SectionType, original_content: str, job_description: str) -> dict:
        """
        Detect potential fabrication opportunities and generate clarification questions
        instead of allowing the agent to hallucinate content.
        """
        
        fabrication_detection_prompt = f"""
FABRICATION DETECTION AND CLARIFICATION SYSTEM

You are a conservative resume enhancement system that NEVER fabricates information.
Your job is to identify areas where you might be tempted to add content not explicitly present in the original resume.

ORIGINAL {section_type.value.upper()} CONTENT:
{original_content}

JOB DESCRIPTION REQUIREMENTS:
{job_description}

DETECTION RULES:
1. Identify any skills/technologies mentioned in job description but NOT in original content
2. Detect any potential projects/experiences that could be added but aren't mentioned
3. Find any quantifiable achievements that could be assumed but aren't stated
4. Spot any educational details that could be enhanced but aren't provided

ANALYSIS REQUIRED:
1. List any items from job description that are missing from original content
2. For each missing item, determine if it could reasonably be clarified with the user
3. Generate specific clarification questions for ambiguous areas
4. Mark items as "SAFE_TO_ENHANCE" (clearly in original) vs "NEEDS_CLARIFICATION" (questionable)

OUTPUT FORMAT (JSON):
{{
    "fabrication_risks": [
        {{
            "item": "specific skill/achievement/detail",
            "risk_level": "high|medium|low",
            "reason": "why this might be fabricated",
            "clarification_question": "specific question to ask user"
        }}
    ],
    "safe_enhancements": [
        "items that can be safely improved from original content"
    ],
    "needs_user_input": [
        {{
            "category": "skills|experience|education|projects",
            "question": "specific clarification question",
            "context": "why this clarification is needed"
        }}
    ]
}}

Focus on being EXTREMELY conservative. When in doubt, ask for clarification rather than assuming.
"""

        try:
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "system", "content": fabrication_detection_prompt}],
                temperature=0.3,
                max_tokens=1000
            )
            
            content = response.choices[0].message.content
            if content:
                return json.loads(content.strip())
            else:
                return {"fabrication_risks": [], "safe_enhancements": [], "needs_user_input": []}
                
        except Exception as e:
            logger.error(f"Error in fabrication detection: {str(e)}")
            # Fail safe - assume everything needs clarification
            return {
                "fabrication_risks": [{"item": "unknown", "risk_level": "high", "reason": "analysis failed", "clarification_question": "Please verify the content to be enhanced"}],
                "safe_enhancements": [],
                "needs_user_input": [{"category": "general", "question": "Please confirm all details to be enhanced", "context": "system verification failed"}]
            }
    
    async def _verify_suggestion_quality(self, original_content: str, suggested_content: str, section_type: SectionType) -> dict:
        """
        Critical verification step to ensure suggestions maintain format integrity
        and don't fabricate content or convert structures inappropriately.
        """
        
        verification_issues = []
        
        # Skills section specific checks
        if section_type == SectionType.SKILLS:
            # Check if original was structured but suggestion is paragraph-style
            original_has_categories = any(marker in original_content for marker in ['▸', ':', 'Languages:', 'Framework', 'Database', 'Tools:', 'Cloud'])
            suggested_is_paragraph = any(phrase in suggested_content.lower() for phrase in ['proficient in', 'skilled in', 'experienced in', 'competent in'])
            
            if original_has_categories and suggested_is_paragraph:
                verification_issues.append({
                    "severity": "critical",
                    "issue": "structure_violation",
                    "description": "Original skills were structured with categories, but suggestion converts to paragraph format",
                    "action": "preserve_original_structure"
                })
            
            # Check for fabricated skills not in original
            original_skills = set(self._extract_skills_from_text(original_content))
            suggested_skills = set(self._extract_skills_from_text(suggested_content))
            fabricated_skills = suggested_skills - original_skills
            
            if fabricated_skills:
                verification_issues.append({
                    "severity": "high",
                    "issue": "fabricated_content",
                    "description": f"Suggested skills not in original: {list(fabricated_skills)}",
                    "action": "request_user_confirmation"
                })
        
        # Education section specific checks  
        elif section_type == SectionType.EDUCATION:
            # Check for fabricated projects
            if "project" in suggested_content.lower() and "project" not in original_content.lower():
                verification_issues.append({
                    "severity": "critical",
                    "issue": "fabricated_projects",
                    "description": "Suggestion adds projects not mentioned in original education",
                    "action": "remove_fabricated_content"
                })
            
            # Check for course names being converted to project titles
            original_courses = self._extract_course_names(original_content)
            if any(course.lower() in suggested_content.lower() and "project" in suggested_content.lower() for course in original_courses):
                verification_issues.append({
                    "severity": "critical", 
                    "issue": "course_to_project_conversion",
                    "description": "Coursework being incorrectly converted to project descriptions",
                    "action": "preserve_coursework_format"
                })
        
        # General fabrication check
        original_length = len(original_content.split())
        suggested_length = len(suggested_content.split())
        if suggested_length > original_length * 1.5:  # 50% increase threshold
            verification_issues.append({
                "severity": "medium",
                "issue": "excessive_content_addition",
                "description": f"Suggestion is {((suggested_length/original_length-1)*100):.0f}% longer than original",
                "action": "verify_additions"
            })
        
        return {
            "is_valid": len([issue for issue in verification_issues if issue["severity"] in ["critical", "high"]]) == 0,
            "issues": verification_issues,
            "recommendation": "reject" if any(issue["severity"] == "critical" for issue in verification_issues) else "review"
        }
    
    def _extract_skills_from_text(self, text: str) -> list:
        """Extract individual skills/technologies from text."""
        # Common technology patterns
        tech_patterns = [
            r'\b(?:Python|Java|JavaScript|TypeScript|C\+\+|React|Node\.js|MongoDB|PostgreSQL|AWS|Docker|Git)\b',
            r'\b[A-Z][a-z]+(?:\.[a-z]+)?\b'  # Camel case or dot notation
        ]
        
        skills = []
        for pattern in tech_patterns:
            import re
            matches = re.findall(pattern, text, re.IGNORECASE)
            skills.extend(matches)
        
        # Also split by common delimiters
        for delimiter in [',', '•', '▸', ':']:
            if delimiter in text:
                parts = text.split(delimiter)
                for part in parts:
                    clean_part = part.strip().split()[0] if part.strip() else ""
                    if clean_part and len(clean_part) > 2:
                        skills.append(clean_part)
        
        return list(set(skills))
    
    def _extract_course_names(self, education_text: str) -> list:
        """Extract course names from education section."""
        courses = []
        lines = education_text.split('\n')
        
        for line in lines:
            if any(keyword in line.lower() for keyword in ['course', 'coursework', 'relevant']):
                # Extract course names after common patterns
                import re
                course_matches = re.findall(r'(?:Course\w*:?\s*)([\w\s,]+)', line, re.IGNORECASE)
                for match in course_matches:
                    course_names = [c.strip() for c in match.split(',')]
                    courses.extend(course_names)
        
        return [course for course in courses if len(course) > 3]
    
    def _detect_actual_changes(self, original_content: str, improved_content: str) -> dict:
        """
        Accurately detect if meaningful changes were made to the content.
        Returns detailed analysis of what changed and whether improvements are real.
        """
        
        # Normalize content for comparison (remove extra whitespace, normalize line breaks)
        def normalize_content(content: str) -> str:
            import re
            # Remove extra whitespace and normalize line breaks
            normalized = re.sub(r'\s+', ' ', content.strip())
            # Remove common formatting markers for comparison
            normalized = re.sub(r'[▸•\-\*]+\s*', '', normalized)
            return normalized.lower()
        
        original_normalized = normalize_content(original_content)
        improved_normalized = normalize_content(improved_content)
        
        # Check for substantial content changes
        content_similarity = self._calculate_content_similarity(original_normalized, improved_normalized)
        
        changes_detected = {
            "has_meaningful_changes": False,
            "similarity_score": content_similarity,
            "change_types": [],
            "specific_changes": [],
            "formatting_only": False
        }
        
        # If content is essentially identical (>95% similar)
        if content_similarity > 0.95:
            changes_detected["has_meaningful_changes"] = False
            changes_detected["formatting_only"] = True
            changes_detected["specific_changes"].append("Minor formatting adjustments only")
        else:
            # Analyze specific types of changes
            changes_detected["has_meaningful_changes"] = True
            
            # Check for structure improvements
            if self._has_structure_improvements(original_content, improved_content):
                changes_detected["change_types"].append("structure")
                changes_detected["specific_changes"].append("Improved content organization and structure")
            
            # Check for categorization improvements
            if self._has_categorization_improvements(original_content, improved_content):
                changes_detected["change_types"].append("categorization")
                changes_detected["specific_changes"].append("Enhanced categorization and grouping")
            
            # Check for formatting improvements
            if self._has_formatting_improvements(original_content, improved_content):
                changes_detected["change_types"].append("formatting")
                changes_detected["specific_changes"].append("Applied professional formatting standards")
            
            # Check for content additions (should be minimal)
            original_words = set(original_normalized.split())
            improved_words = set(improved_normalized.split())
            new_words = improved_words - original_words
            
            if len(new_words) > 3:  # More than 3 new words might indicate fabrication
                changes_detected["change_types"].append("content_addition")
                changes_detected["specific_changes"].append(f"Added content: {', '.join(list(new_words)[:5])}")
        
        return changes_detected
    
    def _calculate_content_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two texts using word overlap."""
        words1 = set(text1.split())
        words2 = set(text2.split())
        
        if not words1 and not words2:
            return 1.0
        if not words1 or not words2:
            return 0.0
        
        intersection = words1 & words2
        union = words1 | words2
        
        return len(intersection) / len(union) if union else 0.0
    
    def _has_structure_improvements(self, original: str, improved: str) -> bool:
        """Check if structure was actually improved."""
        # Check for bullet point additions/improvements
        original_bullets = original.count('•') + original.count('-') + original.count('▸')
        improved_bullets = improved.count('•') + improved.count('-') + improved.count('▸')
        
        # Check for category additions
        original_categories = original.count(':')
        improved_categories = improved.count(':')
        
        return improved_bullets > original_bullets or improved_categories > original_categories
    
    def _has_categorization_improvements(self, original: str, improved: str) -> bool:
        """Check if categorization was actually improved."""
        category_keywords = ['Languages:', 'Framework', 'Database', 'Tools:', 'Cloud', 'Skills:']
        
        original_cats = sum(1 for keyword in category_keywords if keyword.lower() in original.lower())
        improved_cats = sum(1 for keyword in category_keywords if keyword.lower() in improved.lower())
        
        return improved_cats > original_cats
    
    def _has_formatting_improvements(self, original: str, improved: str) -> bool:
        """Check if formatting was actually improved."""
        # Check for consistent line formatting
        original_lines = [line.strip() for line in original.split('\n') if line.strip()]
        improved_lines = [line.strip() for line in improved.split('\n') if line.strip()]
        
        # If line count significantly different, formatting likely changed
        return abs(len(improved_lines) - len(original_lines)) > 1
    
    async def _score_content_quality(self, content: str, section_type: SectionType, job_analysis: JobAnalysis) -> int:
        """
        PRIMARY SCORING SYSTEM: Fast, focused scoring for real-time agent decisions.
        This drives the accept/reject/retry logic and must be fast (< 1 second).
        """
        try:
            prompt = f"""
            Score this {section_type.value} section from 1-100 based on:
            - Professional formatting and structure (25%)
            - Relevance to job requirements (25%)
            - Clarity and conciseness (25%)
            - ATS compatibility (25%)
            
                    Content: {content}
        Job Requirements: {job_analysis.requirements}
            
            Respond with ONLY a number from 1-100.
            """
            
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",  # Fast model for real-time decisions
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=10  # We only need a number
            )
            
            score_text = response.choices[0].message.content.strip()
            score = int(re.search(r'\d+', score_text).group())
            
            return max(1, min(100, score))
            
        except Exception as e:
            logger.error(f"❌ Error in primary scoring: {str(e)}")
            return 50  # Default neutral score for safety

    def _trigger_judgment_evaluation(self, 
                                   original_content: str, 
                                   improved_content: str, 
                                   section_type: SectionType, 
                                   job_analysis: JobAnalysis, 
                                   primary_score: int,
                                   iteration: int):
        """
        JUDGMENT FRAMEWORK: Comprehensive async evaluation that doesn't block agent flow.
        This provides rich insights, pattern detection, and audit trails.
        """
        import asyncio
        
        # Run judgment evaluation asynchronously (non-blocking)
        asyncio.create_task(self._run_comprehensive_evaluation(
            original_content=original_content,
            improved_content=improved_content,
            section_type=section_type,
            job_analysis=job_analysis,
            primary_score=primary_score,
            iteration=iteration
        ))

    async def _run_comprehensive_evaluation(self, 
                                          original_content: str,
                                          improved_content: str, 
                                          section_type: SectionType,
                                          job_analysis: JobAnalysis,
                                          primary_score: int,
                                          iteration: int):
        """
        Comprehensive evaluation using Judgment framework - runs in parallel.
        """
        try:
            # Multi-dimensional quality evaluation
            from .judgment_config import ResumeMetrics
            
            # Structure quality evaluation
            evaluator.evaluate_section_improvement(
                original_content=original_content,
                improved_content=improved_content,
                job_description=str(job_analysis.__dict__),
                section_type=section_type.value,
                metric=ResumeMetrics.STRUCTURE_ACCURACY
            )
            
            # Job relevance evaluation
            evaluator.evaluate_section_improvement(
                original_content=original_content,
                improved_content=improved_content,
                job_description=str(job_analysis.__dict__),
                section_type=section_type.value,
                metric=ResumeMetrics.JOB_RELEVANCE
            )
            
            # Formatting quality evaluation
            evaluator.evaluate_section_improvement(
                original_content=original_content,
                improved_content=improved_content,
                job_description=str(job_analysis.__dict__),
                section_type=section_type.value,
                metric=ResumeMetrics.FORMATTING_QUALITY
            )
            
            # Agent decision evaluation
            evaluator.evaluate_agent_decision(
                decision_context=f"Primary scoring of {section_type.value} section in iteration {iteration}",
                decision_made=f"Score: {primary_score}/100 - {'Accept' if primary_score >= 80 else 'Retry' if primary_score >= 60 else 'Request clarification'}",
                reasoning="Based on structure quality, job relevance, professional format, and ATS compatibility",
                confidence_score=primary_score / 100.0
            )
            
            # Monitor quality trends and patterns
            monitor.log_quality_metrics({
                "section_type": section_type.value,
                "primary_score": primary_score,
                "iteration": iteration,
                "decision": "accept" if primary_score >= 80 else "retry" if primary_score >= 60 else "clarify",
                "timestamp": datetime.now().isoformat()
            })
            
        except Exception as e:
            logger.warning(f"⚠️ Judgment evaluation error (non-critical): {str(e)}")
            # Don't let judgment failures affect the main agent flow
    
    # Continue with other required methods...
    async def _parse_resume_sections(self, resume_text: str) -> Dict[str, Dict[str, Any]]:
        """Parse resume into structured sections."""
        try:
            sections_list = split_resume_sections(resume_text)
            processed_sections = {}
            
            for section_dict in sections_list:
                section_type = section_dict.get("type", "unknown")
                content = section_dict.get("content", "")
                
                if content and content.strip():
                    processed_sections[section_type] = {
                        "type": section_type,
                        "content": content.strip(),
                        "original_type": section_type
                    }
            
            logger.info(f"✅ Parsed {len(processed_sections)} sections: {list(processed_sections.keys())}")
            return processed_sections
            
        except Exception as e:
            logger.error(f"❌ Error parsing resume sections: {str(e)}")
            return {}
    
    async def _analyze_job_description_comprehensive(self, job_description: str) -> JobAnalysis:
        """Perform comprehensive job description analysis."""
        try:
            messages = [
                {
                    "role": "system",
                    "content": """You are an expert talent acquisition specialist performing comprehensive job analysis.

Return ONLY a valid JSON object with these exact keys:
{{
  "keywords": array of strings (15-25 important keywords),
  "requirements": array of strings (8-15 key requirements),
  "experience_level": string (entry/junior/mid/senior/lead/principal),
  "key_technologies": array of strings (10-20 technical skills),
  "priorities": array of strings (top 8-12 critical qualifications),
  "soft_skills": array of strings (5-10 soft skills),
  "hard_skills": array of strings (8-15 technical abilities),
  "industry": string (primary industry),
  "company_size": string (startup/small/medium/large/enterprise),
  "role_type": string (individual_contributor/team_lead/manager/director)
}}"""
                },
                {
                    "role": "user",
                    "content": f"Analyze this job description comprehensively:\n\n{job_description}"
                }
            ]
            
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                temperature=0.0
            )
            
            result = json.loads(response.choices[0].message.content)
            
            return JobAnalysis(
                keywords=result.get("keywords", []),
                requirements=result.get("requirements", []),
                experience_level=result.get("experience_level", "mid"),
                key_technologies=result.get("key_technologies", []),
                priorities=result.get("priorities", []),
                soft_skills=result.get("soft_skills", []),
                hard_skills=result.get("hard_skills", []),
                industry=result.get("industry", "technology"),
                company_size=result.get("company_size", "medium"),
                role_type=result.get("role_type", "individual_contributor")
            )
            
        except Exception as e:
            logger.error(f"❌ Error in job analysis: {str(e)}")
            return JobAnalysis(
                keywords=[], requirements=[], experience_level="mid",
                key_technologies=[], priorities=[], soft_skills=[],
                hard_skills=[], industry="technology", company_size="medium",
                role_type="individual_contributor"
            )
    
    # API compatibility methods
    # @judgment.observe(name="analyze_resume_section", span_type="agent_analysis")  # Removed for cleaner traces  
    async def analyze_resume_section(
        self,
        content: str,
        section_type: SectionType,
        job_description: str,
        user_baseline: Optional[str] = None
    ) -> SectionAnalysis:
        """Analyze a specific section."""
        if session_id not in self.sessions:
            return {"success": False, "error": "Session not found"}
        
        session = self.sessions[session_id]
        section_analysis = session.get("section_analyses", {}).get(section_type)
        
        if not section_analysis:
            return {"success": False, "error": f"No analysis found for section {section_type}"}
        
        return {
            "success": True,
            "analysis": {
                "section_type": section_analysis.section_type.value,
                "original_content": section_analysis.original_content,
                "improved_content": section_analysis.best_content,
                "score": section_analysis.final_score,
                "feedback": section_analysis.improvement_journey,
                "iteration_count": len(section_analysis.iterations),
                "needs_clarification": section_analysis.needs_clarification,
                "clarification_request": {
                    "question": section_analysis.clarification_request.question,
                    "context": section_analysis.clarification_request.context,
                    "reason": section_analysis.clarification_request.reason
                } if section_analysis.clarification_request else None
            }
        }

    def get_session_status(self, session_id: str) -> Dict[str, Any]:
        """Get session status."""
        if session_id not in self.sessions:
            return {"success": False, "error": "Session not found"}
        
        session = self.sessions[session_id]
        return {
            "success": True,
            "session_id": session_id,
            "current_phase": "completed",
            "sections_analyzed": len(session.get("section_analyses", {})),
            "pending_clarifications": 0,
            "created_at": session.get("created_at"),
            "updated_at": session.get("created_at")
        }
    
    async def provide_clarification(self, session_id: str, section_type: str, user_response: str) -> Dict[str, Any]:
        """Handle user clarification."""
        if session_id not in self.sessions:
            return {"success": False, "error": "Session not found"}
        
        return {
            "success": True,
            "analysis": self.sessions[session_id]["section_analyses"].get(section_type, {})
        }
    
    async def accept_section_changes(self, session_id: str, section_type: str, accepted: bool) -> Dict[str, Any]:
        """Accept or reject section changes."""
        if session_id not in self.sessions:
            return {"success": False, "error": "Session not found"}
        
        session = self.sessions[session_id]
        # Always allow updates to change decisions
        session["accepted_changes"][section_type] = accepted
        logger.info(f"✅ Section {section_type} changes {'accepted' if accepted else 'rejected'} in session {session_id}")
        
        return {
            "success": True,
            "message": f"Changes {'accepted' if accepted else 'rejected'} for {section_type}"
        }
    
    async def generate_final_resume(self, session_id: str) -> Dict[str, Any]:
        """Generate final resume based on user's accepted/rejected changes."""
        if session_id not in self.sessions:
            return {"success": False, "error": "Session not found"}
        
        session = self.sessions[session_id]
        sections = []
        accepted_changes = session.get("accepted_changes", {})
        
        logger.info(f"🔄 Generating final resume for session {session_id}")
        logger.info(f"📝 Accepted changes: {accepted_changes}")
        
        for section_type, analysis in session.get("section_analyses", {}).items():
            # Determine which content to use based on user decision
            if section_type in accepted_changes:
                if accepted_changes[section_type]:
                    # User accepted changes - use improved content
                    content = analysis.best_content or analysis.original_content
                    logger.info(f"✅ Using improved content for {section_type}")
                else:
                    # User rejected changes - use original content
                    content = analysis.original_content
                    logger.info(f"⏭️ Using original content for {section_type} (rejected)")
            else:
                # No decision made - default to original content
                content = analysis.original_content
                logger.info(f"🔄 Using original content for {section_type} (no decision)")
            
            # Format section with proper header
            section_title = section_type.upper().replace('_', ' ')
            sections.append(f"=== {section_title} ===\n{content}")
        
        final_resume = "\n\n".join(sections)
        
        logger.info(f"✅ Generated final resume with {len(sections)} sections")
        
        return {
            "success": True,
            "final_resume": final_resume,
            "sections": list(session.get("section_analyses", {}).keys()),
            "session_id": session_id
        } 