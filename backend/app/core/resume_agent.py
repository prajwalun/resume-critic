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

# Import clean logging
from .logging_config import get_clean_logger

# Setup clean logger
logger = get_clean_logger(__name__)

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
            logger.error("OPENAI_API_KEY environment variable is not set!")
            raise ValueError("OpenAI API key is required. Please set OPENAI_API_KEY in your .env file.")
        
        try:
            from judgeval.common.tracer import wrap
            self.client = wrap(AsyncOpenAI(
                api_key=api_key,
                timeout=60.0,  # Longer timeout for iterative analysis
                max_retries=3
            ))
            logger.info("ResumeWise initialized with Judgment observability")
        except ImportError:
            # Fallback if wrap is not available
            self.client = AsyncOpenAI(
                api_key=api_key,
                timeout=60.0,  # Longer timeout for iterative analysis
                max_retries=3
            )
            logger.info("ResumeWise initialized")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {str(e)}")
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
        
        # Store original job description to prevent false positive clarification triggers
        self.original_job_description: str = ""
        
        # Common formatting rules
        self.base_formatting_rules = """
CRITICAL RESUME FORMATTING RULES:
NEVER FABRICATE - Only use information that exists in the original content
NEVER ADD FAKE SKILLS - Don't mention technologies not in the original
NEVER INVENT ACHIEVEMENTS - Don't create metrics that weren't provided
NEVER HALLUCINATE EXPERIENCES - Don't add roles, projects, or accomplishments
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
NEVER FABRICATE - Only use information that exists in the original content
NEVER ADD FAKE SKILLS - Don't mention technologies not in the original
NEVER INVENT ACHIEVEMENTS - Don't create metrics that weren't provided
NEVER HALLUCINATE EXPERIENCES - Don't add roles, projects, or accomplishments

CRITICAL SKILLS FORMATTING RULES - MUST FOLLOW EXACTLY:

ABSOLUTELY FORBIDDEN:
- Converting structured skills to paragraph format
- Using phrases like "Proficient in", "Skilled in", "Experienced in"
- Creating sentences about skills: "Strong programming skills in..."
- Bullet points with explanations: "• JavaScript - for building applications"

MANDATORY STRUCTURE PRESERVATION:
If original uses categories like:
▸ Languages: Python, HTML, CSS3, JavaScript, TypeScript
▸ Framework and Libraries: React Native, Django, Node.js

THEN OUTPUT MUST MAINTAIN EXACT SAME STRUCTURE:
▸ Languages: Python, HTML, CSS3, JavaScript, TypeScript  
▸ Framework and Libraries: React Native, Django, Node.js

SKILLS SECTION FORMATTING REQUIREMENTS:
PRESERVE original categorization markers (▸, bullets, colons)
MAINTAIN comma-separated lists within categories
KEEP same category names from original
ONLY reorganize existing skills - NEVER add new ones
Fix minor formatting inconsistencies (spacing, capitalization)

EXAMPLE - CORRECT TRANSFORMATION:
ORIGINAL:
Languages: Python, HTML, CSS3, JavaScript, TypeScript,
Framework and Libraries: React Native, Django, Node.js, NestJS, Langchain, MCP

IMPROVED:
▸ Languages: Python, HTML, CSS3, JavaScript, TypeScript
▸ Framework and Libraries: React Native, Django, Node.js, NestJS, Langchain, MCP

EXAMPLE - FORBIDDEN TRANSFORMATION:
NEVER DO THIS:
"• Proficient in programming languages including Python, JavaScript, and TypeScript, with experience in web development frameworks such as React and Django."

STRUCTURE PRESERVATION PROTOCOL:
1. Identify the exact formatting pattern in original (bullets, categories, lists)
2. PRESERVE that exact pattern in improved version
3. Only clean up spacing, fix typos, improve organization within existing structure
4. NEVER convert lists to paragraphs or sentences

{self.conservative_rules}

OUTPUT: Return ONLY the improved skills content maintaining the EXACT structural format of the original. No explanations or descriptions.
""",
            SectionType.EXPERIENCE: f"""
{self.base_formatting_rules}

CRITICAL EXPERIENCE FORMATTING RULES - MUST FOLLOW EXACTLY:

ABSOLUTELY FORBIDDEN IN EXPERIENCE SECTION:
- Adding percentage improvements not mentioned in original (e.g., "50% increase", "30% reduction")
- Creating specific metrics not provided by user (e.g., "reduced latency by 10%", "improved efficiency by 25%")
- Inventing business outcomes not stated (e.g., "increased revenue", "saved costs")
- Adding achievements with numbers not in original content
- Creating impact statements without user's data (e.g., "resulting in better performance")

EXPERIENCE ENHANCEMENT REQUIREMENTS:
- Only improve wording of existing bullet points - never add new ones
- Do NOT invent technologies, tools, or responsibilities not mentioned in original
- Use stronger action verbs for existing content only
- Do NOT add metrics, percentages, or specific achievements not provided by user
- Format: Company | Role | Dates, then enhanced existing bullet points only

SAFE EXPERIENCE IMPROVEMENTS:
- Better action verbs for existing responsibilities (e.g., "worked on" → "developed")
- Professional language for existing achievements
- Clearer structure and formatting of existing content
- Remove redundancy and improve clarity of existing points

{self.conservative_rules}

OUTPUT: Return ONLY the improved {SectionType.EXPERIENCE.value} content. No explanations or descriptions.
""",
            SectionType.EDUCATION: f"""
{self.base_formatting_rules}

CRITICAL EDUCATION FORMATTING RULES - MUST FOLLOW EXACTLY:

ABSOLUTELY FORBIDDEN:
- Converting course names into "project" descriptions
- Fabricating project titles from coursework listings
- Adding achievements not mentioned in original education
- Creating experience bullets from educational content
- Turning "Data Structures" coursework into "Data Structures Project"

EDUCATION SECTION REQUIREMENTS:
- Institution name, degree, graduation date/timeline
- GPA if provided in original
- Relevant coursework AS COURSEWORK (not projects)
- Honors/awards if mentioned in original
- Clean, professional educational formatting

STRUCTURE PRESERVATION FOR EDUCATION:
If original shows:
California State University, Dominguez Hill Aug 2023 – Dec 2025 (Expected)
Master of Science in Computer Science, GPA: 3.8 California, US
Coursework: Data Structures, Algorithm Analysis, Object Oriented Analysis

THEN OUTPUT MUST MAINTAIN EDUCATIONAL FORMAT:
**California State University, Dominguez Hills**
Master of Science in Computer Science, Aug 2023 – Dec 2025 (Expected), GPA: 3.8
- Relevant Coursework: Data Structures, Algorithm Analysis, Object Oriented Analysis

NEVER CONVERT TO PROJECT FORMAT:
"- Collaborative Project: Led a team of 4 in a Software Project course..."
"- Data Science Project: Analyzed real-world datasets..."

PROPER EDUCATION ENHANCEMENT:
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

PROJECTS Section: Project name, brief description, technologies used
   - Only work with projects explicitly mentioned in original
   - Do NOT add fake projects even if they match job requirements
   - Format: Project Name | Brief Description | Technologies Used
   - Focus on impact and outcomes when mentioned in original

{self.conservative_rules}

OUTPUT: Return ONLY the improved {SectionType.PROJECTS.value} content. No explanations or descriptions.
"""
        }
    
    async def start_analysis(self, resume_text: str, job_description: str) -> Dict[str, Any]:
        """
        Start iterative resume analysis session with human-in-the-loop workflow.
        Now properly stops when clarification is needed instead of processing everything.
        """
        session_id = str(uuid4())
        
        # Store original job description to prevent false positive clarification triggers
        self.original_job_description = job_description
        
        try:
            # Parse resume sections
            parsed_sections = await self._parse_resume_sections(resume_text)
            if not parsed_sections:
                return {"success": False, "error": "Failed to parse resume sections"}
            
            # Analyze job description  
            job_analysis = await self._analyze_job_description_comprehensive(job_description)
            
            # Initialize session with pending analysis
            self.sessions[session_id] = {
                "resume_text": resume_text,
                "job_description": job_description,
                "sections": parsed_sections,
                "job_analysis": job_analysis,
                "section_analyses": {},
                "accepted_changes": {},
                "current_section_index": 0,  # Track progress
                "needs_clarification": False,
                "pending_clarification": None,
                "created_at": datetime.now().isoformat()
            }
            
            logger.info(f"Iterative analysis session {session_id[:8]} started - {len(parsed_sections)} sections identified")
            
            # HUMAN-IN-THE-LOOP: Process sections one by one, stopping for clarification
            analysis_results = await self._process_sections_with_clarification_support(
                session_id, 
                parsed_sections, 
                job_analysis
            )
            
            return {
                "success": True,
                "session_id": session_id,
                "sections": parsed_sections,
                "job_analysis": job_analysis.__dict__,
                "analysis_order": [section.value for section in self.analysis_order],
                "section_analyses": analysis_results["completed_analyses"],
                "needs_clarification": analysis_results["needs_clarification"],
                "pending_clarifications": analysis_results.get("pending_clarifications", {}),
                "sections_needing_clarification": analysis_results.get("sections_needing_clarification", []),
                "current_section": analysis_results["current_section"],
                "progress": analysis_results["progress"]
            }
            
        except Exception as e:
            logger.error(f"Error starting iterative analysis: {str(e)}")
            
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
    
    async def _process_sections_with_clarification_support(
        self, 
        session_id: str, 
        parsed_sections: Dict[str, Dict[str, Any]], 
        job_analysis: JobAnalysis
    ) -> Dict[str, Any]:
        """
        Process ALL sections with proper human-in-the-loop support.
        CONTINUES analyzing all sections even when clarification is needed.
        """
        completed_analyses = {}
        pending_clarifications = {}
        session = self.sessions[session_id]
        sections_needing_clarification = []
        
        # Process ALL sections, collecting clarifications as needed
        for i, section_type in enumerate(self.analysis_order):
            section_key = section_type.value
            session["current_section_index"] = i
            
            if section_key in parsed_sections and parsed_sections[section_key]["content"].strip():
                logger.info(f"Processing {section_key} section (step {i+1}/{len(self.analysis_order)})")
                
                try:
                    analysis = await self._iterative_section_improvement(
                        parsed_sections[section_key]["content"],
                        section_type,
                        job_analysis,
                        parsed_sections
                    )
                
                    # Check if this section needs clarification (but DON'T stop!)
                    if analysis.needs_clarification and analysis.clarification_request:
                        logger.warning(f"Clarification needed for {section_key} - continuing with other sections")
                        
                        # Store clarification request for this section
                        pending_clarifications[section_key] = {
                            "section_type": section_key,
                            "question": analysis.clarification_request.question,
                            "context": analysis.clarification_request.context,
                            "reason": analysis.clarification_request.reason,
                            "original_content": analysis.clarification_request.original_content
                        }
                        sections_needing_clarification.append(section_key)
                        
                        # CRITICAL FIX: Store analysis in BOTH places to ensure it appears in final resume
                        session["section_analyses"][section_key] = analysis  # Store SectionAnalysis object
                        completed_analyses[section_key] = {  # Store dict representation for API
                            "section_type": analysis.section_type.value,
                            "original_content": analysis.original_content,
                            "improved_content": analysis.best_content,  # Safe improvements only
                            "score": analysis.final_score,
                            "feedback": analysis.improvement_journey,
                            "iteration_count": len(analysis.iterations),
                            "needs_clarification": True,
                            "clarification_request": {
                                "question": analysis.clarification_request.question,
                                "context": analysis.clarification_request.context,
                                "reason": analysis.clarification_request.reason
                            }
                        }
                        
                        # Log clarification request
                        monitor.log_user_clarification(section_key, analysis.clarification_request.question)
                    
                    else:
                        # No clarification needed, save analysis and continue
                        session["section_analyses"][section_key] = analysis
                        completed_analyses[section_key] = {
                            "section_type": analysis.section_type.value,
                            "original_content": analysis.original_content,
                            "improved_content": analysis.best_content,
                            "score": analysis.final_score,
                            "feedback": analysis.improvement_journey,
                            "iteration_count": len(analysis.iterations),
                            "needs_clarification": False,
                            "clarification_request": None
                        }
                        
                        logger.info(f"Completed {section_key}: {len(analysis.iterations)} iterations, score: {analysis.final_score}")
            
                except Exception as e:
                    logger.error(f"Error processing {section_key}: {str(e)}")
                    # Create fallback analysis and continue - ENSURE both storages are updated
                    fallback_analysis = SectionAnalysis(
                        section_type=section_type,
                        original_content=parsed_sections[section_key]["content"],
                        best_content=parsed_sections[section_key]["content"],  # Use original as fallback
                        iterations=[],
                        final_score=50,
                        improvement_journey=f"Analysis temporarily unavailable: {str(e)}",
                        needs_clarification=False,
                        clarification_request=None
                    )
                    
                    # Store in BOTH places
                    session["section_analyses"][section_key] = fallback_analysis
                    completed_analyses[section_key] = {
                        "section_type": section_type.value,
                        "original_content": parsed_sections[section_key]["content"],
                        "improved_content": parsed_sections[section_key]["content"],  # Use original as fallback
                        "score": 50,
                        "feedback": f"Analysis temporarily unavailable: {str(e)}",
                        "iteration_count": 0,
                        "needs_clarification": False,
                        "clarification_request": None
                    }
        
        # Update session state
        has_clarifications = len(pending_clarifications) > 0
        session["needs_clarification"] = has_clarifications
        session["pending_clarifications"] = pending_clarifications  # Store multiple clarifications
        session["current_section_index"] = len(self.analysis_order)  # Mark as completed
        
        if has_clarifications:
            logger.info(f"Analysis completed - {len(sections_needing_clarification)} sections need clarification: {', '.join(sections_needing_clarification)}")
            progress_msg = f"Analysis complete - {len(sections_needing_clarification)} section(s) need clarification"
        else:
            logger.info("Analysis completed - no clarifications needed")
            progress_msg = f"{len(self.analysis_order)}/{len(self.analysis_order)} - All sections completed"
            
        return {
            "completed_analyses": completed_analyses,
            "needs_clarification": has_clarifications,
            "pending_clarifications": pending_clarifications,  # Multiple clarifications
            "sections_needing_clarification": sections_needing_clarification,
            "current_section": "completed",
            "progress": progress_msg
        }
    
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
        
        logger.info(f"Starting iterative improvement for {section_type.value}")
        
        # CRITICAL: FABRICATION DETECTION FIRST - Before any LLM improvements
        logger.info(f"Running fabrication detection for {section_type.value}")
        try:
            # FIXED: Use ORIGINAL job description instead of expanded analysis
            # This prevents false positive clarification triggers from inferred requirements
            
            fabrication_analysis = await self._detect_fabrication_and_clarify(
                section_type, content, self.original_job_description
            )
            
            # Analyze fabrication risks more intelligently
            fabrication_risks = fabrication_analysis.get("fabrication_risks", [])
            needs_user_input = fabrication_analysis.get("needs_user_input", [])
            safe_enhancements = fabrication_analysis.get("safe_enhancements", [])
            
            # Count critical vs manageable risks
            critical_risks = [item for item in fabrication_risks if item.get("risk_level") == "high"]
            manageable_risks = [item for item in fabrication_risks if item.get("risk_level") in ["medium", "low"]]
            
            logger.info(f"Fabrication analysis for {section_type.value}: {len(critical_risks)} critical, {len(manageable_risks)} manageable, {len(safe_enhancements)} safe")
            
            # ENHANCED CLARIFICATION TRIGGER: Check if clarification is needed
            # Simply check if we have high-risk fabrication items
            fabrication_detected = len(critical_risks) > 0
            
            # TRIGGER CLARIFICATION: If fabrication risks detected
            if fabrication_detected:
                logger.warning(f"Clarification needed for {section_type.value}: Fabrication risks detected")
                
                # INTELLIGENT GAP ANALYSIS - Generate specific, targeted clarification questions
                clarification_item = await self._generate_intelligent_clarification(
                    section_type, content, job_analysis, self.original_job_description
                )
                
                clarification_request = ClarificationRequest(
                    section_type=section_type,
                    question=clarification_item["question"],
                    context=clarification_item["context"],
                    original_content=content,
                    reason="Fabrication prevention - user input needed for accurate enhancement",
                    timestamp=datetime.now()
                )
                
                logger.info(f"Clarification required for {section_type.value}: {clarification_request.question[:100]}...")
                
                # Apply only safe formatting improvements while waiting for clarification
                safe_improved_content = await self._ensure_proper_formatting(content, section_type)
                
                # Detect what specific improvements were made
                changes_detected = self._detect_actual_changes(content, safe_improved_content)
                
                # Generate specific feedback based on what was actually improved
                if changes_detected["has_meaningful_changes"]:
                    improvement_details = ", ".join(changes_detected["specific_changes"])
                    section_specific_feedback = f"Applied safe improvements: {improvement_details}. "
                else:
                    section_specific_feedback = "Content reviewed for formatting. "
                
                # Add section-specific clarification guidance
                section_guidance = {
                    SectionType.SKILLS: "To enhance this section, please specify additional technical skills, frameworks, or tools you've used.",
                    SectionType.EXPERIENCE: "To enhance this section, please provide specific achievements, metrics, team sizes, or technologies used in your roles.",
                    SectionType.PROJECTS: "To enhance this section, please share project outcomes, technologies used, team collaboration details, or measurable results.",
                    SectionType.EDUCATION: "To enhance this section, please mention relevant coursework, projects, achievements, or additional certifications."
                }.get(section_type, "To enhance this section, please provide additional relevant details.")
                
                full_feedback = section_specific_feedback + section_guidance
                
                return SectionAnalysis(
                    section_type=section_type,
                    original_content=content,
                    best_content=safe_improved_content,  # Apply safe improvements
                    iterations=[],
                    final_score=60,  # Moderate score with safe improvements
                    improvement_journey=full_feedback,
                    needs_clarification=True,
                    clarification_request=clarification_request
                )
            
            # If only manageable risks or safe enhancements, proceed with conservative improvements
            if manageable_risks or safe_enhancements:
                logger.info(f"Manageable risks detected for {section_type.value} - proceeding with conservative improvements")
                # Continue with normal flow but be more conservative in content generation
            
            logger.info(f"Fabrication check passed for {section_type.value} - proceeding with improvements")
            
        except Exception as e:
            logger.error(f"Fabrication detection failed for {section_type.value}: {str(e)}")
            # Fail safely - apply conservative approach
            conservative_content = await self._ensure_proper_formatting(content, section_type)
            return SectionAnalysis(
                section_type=section_type,
                original_content=content,
                best_content=conservative_content,
                iterations=[],
                final_score=70,
                improvement_journey="Applied conservative improvements due to fabrication detection error.",
                needs_clarification=False,
                clarification_request=None
            )
        
        # ITERATION LOOP: Keep improving until we reach excellence (only if fabrication check passed)
        for iteration in range(self.max_iterations):
            perspective = self.perspective_rotation[iteration % len(self.perspective_rotation)]
            
            # Clean iteration logging - only show important progress
            
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
                    logger.warning(f"Content rejected - verification issues:")
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
                        logger.info("Applying format-preserving cleanup instead")
                        improved_content = await self._ensure_proper_formatting(content, section_type)
                        
                        # Re-verify the cleanup
                        cleanup_verification = await self._verify_suggestion_quality(content, improved_content, section_type)
                        if not cleanup_verification["is_valid"]:
                            logger.warning("Even format cleanup failed verification - keeping original")
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
                    logger.info(f"Applied verification penalty: -{penalty} points (final score: {quality_score})")
                
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
                    logger.info(f"New best version! Score: {best_score} (with verification)")
                
                # STEP 9: Check if we've reached excellence (with verification)
                if quality_score >= self.quality_threshold:
                    logger.info(f"Excellence achieved! Score: {quality_score} >= {self.quality_threshold}")
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
                logger.error(f"Analysis error: {str(e)}")
                break
        
        # Generate improvement journey narrative with accurate change detection
        improvement_journey = await self._generate_improvement_narrative(iterations, section_type, content)
        
        # Check if we need format-first improvements regardless of JD requirements
        if best_score < 80 or not iterations:  # If quality is low or no iterations ran
            logger.info(f"Applying format-first improvements for {section_type.value}")
            format_improved = await self._ensure_proper_formatting(content, section_type)
            
            # Check if format improvement actually made changes
            format_changes = self._detect_actual_changes(content, format_improved)
            if format_changes["has_meaningful_changes"]:
                best_content = format_improved
                improvement_journey = ". ".join(format_changes["specific_changes"]) + "."
                logger.info(f"Format-first improvements applied: {improvement_journey}")
        
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
NEVER FABRICATE - Only use information that exists in the original content
NEVER ADD FAKE SKILLS - Don't mention technologies not in the original
NEVER INVENT ACHIEVEMENTS - Don't create metrics that weren't provided
NEVER HALLUCINATE EXPERIENCES - Don't add roles, projects, or accomplishments

SECTION-SPECIFIC FORMATTING STANDARDS:
SKILLS Section: Keep as bullet points or comma-separated lists, NOT paragraphs
   - Only list technologies/tools that are explicitly mentioned in original
   - Do NOT add skills based on job description requirements
   - Do NOT write explanatory sentences about proficiency levels
   - Format: "• Python, JavaScript, React, Node.js" or "Python • JavaScript • React"

EDUCATION Section: Institution, degree, dates, relevant coursework only
   - Do NOT add fake projects or achievements not mentioned in original
   - Do NOT fabricate coursework that wasn't listed
   - Do NOT add technologies or skills under education unless they were coursework
   - Format: Institution, Degree, Date, GPA (if provided), Listed Coursework

EXPERIENCE Section: Company, role, dates, bullet points of achievements
   - Only enhance existing bullet points, never add new fake ones
   - Do NOT invent technologies or responsibilities not mentioned

PROJECTS Section: Project name, brief description, technologies used
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
7. NEVER ADD METRICS - Do not add percentages, numbers, or achievement claims not in original content

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
        
        logger.info(f"Content needs formatting improvements: {', '.join(needs_formatting)}")
        
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
    
    async def _generate_intelligent_clarification(
        self, 
        section_type: SectionType, 
        resume_content: str, 
        job_analysis: JobAnalysis, 
        job_description: str
    ) -> dict:
        """
        Generate intelligent, gap-aware clarification questions based on analysis of
        what's missing between resume content and job requirements.
        """
        
        # Create section-specific gap analysis prompt
        system_prompt = f"""
You are an expert resume analyst. Analyze the gap between the resume content and job requirements for the {section_type.value} section.

RESUME {section_type.value.upper()} CONTENT:
{resume_content}

JOB DESCRIPTION:
{job_description}

JOB ANALYSIS:
- Key Technologies: {', '.join(job_analysis.key_technologies[:10])}
- Requirements: {', '.join(job_analysis.requirements[:5])}
- Hard Skills: {', '.join(job_analysis.hard_skills[:10])}

TASK: Identify specific gaps and generate 1-3 targeted clarification questions.

SECTION-SPECIFIC ANALYSIS:
"""

        if section_type == SectionType.SKILLS:
            system_prompt += """
For SKILLS section:
1. Compare resume technologies with job requirements
2. Identify missing but relevant technologies, frameworks, tools
3. Look for skill categories that could be enhanced
4. Ask specific questions about missing technologies the user might have

Example good questions:
- "The job emphasizes React and Node.js, but I only see basic JavaScript listed. Do you have experience with React or Node.js that we should include?"
- "The role requires cloud platforms (AWS/Azure). Have you worked with any cloud services in your projects?"

AVOID generic questions like "do you have any other skills?"
"""
        elif section_type == SectionType.EXPERIENCE:
            system_prompt += """
For EXPERIENCE section:
1. Look for missing metrics, achievements, or quantifiable results
2. Check if technologies mentioned in job are reflected in experience
3. Identify roles that could be enhanced with specific outcomes
4. Ask about missing technologies used in projects

Example good questions:
- "In your Software Engineer role, you mention building applications but don't specify the impact. Can you provide metrics like user growth, performance improvements, or team size?"
- "The job requires Docker and CI/CD experience. Did you use these technologies in any of your roles?"

AVOID generic questions like "tell us about your achievements"
"""
        elif section_type == SectionType.PROJECTS:
            system_prompt += """
For PROJECTS section:
1. Look for missing outcomes, results, or impact metrics
2. Check if project technologies align with job requirements
3. Identify projects lacking technical depth
4. Ask about specific results or technologies used

Example good questions:
- "Your e-commerce project sounds impressive, but what were the specific results? (e.g., reduced load time by X%, supported Y users, etc.)"
- "The job requires experience with databases. Which database technologies did you use in your projects?"

AVOID generic questions like "tell us more about your projects"
"""
        elif section_type == SectionType.EDUCATION:
            system_prompt += """
For EDUCATION section:
1. Look for missing relevant coursework related to job requirements
2. Check for missing projects, achievements, or certifications
3. Identify opportunities to highlight relevant academic work

Example good questions:
- "The job emphasizes operating systems and networking. Did you take any relevant courses or complete projects in these areas during your studies?"
- "Did you complete any notable projects, research, or achieve academic recognition that would strengthen your candidacy?"

AVOID generic questions like "tell us about your education"
"""

        system_prompt += """

OUTPUT FORMAT:
Return a JSON object with:
{
  "category": "gap_analysis",
  "question": "Specific, actionable question(s) based on identified gaps",
  "context": "Brief explanation of why this information is needed",
  "specific_gaps": ["list", "of", "specific", "missing", "items"]
}

Make questions specific, helpful, and focused on real gaps between resume and job requirements.
"""

        try:
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Analyze the {section_type.value} section and generate specific clarification questions based on gaps with job requirements."}
                ],
                temperature=0.3,
                max_tokens=800
            )
            
            content = response.choices[0].message.content.strip()
            
            # Clean the response to extract JSON - remove common prefixes
            cleaned_content = content
            if content.lower().startswith('json'):
                cleaned_content = content[4:].strip()
            if cleaned_content.startswith('```json'):
                cleaned_content = cleaned_content[7:]
            if cleaned_content.endswith('```'):
                cleaned_content = cleaned_content[:-3]
            cleaned_content = cleaned_content.strip()
            
            # Try to parse JSON response
            try:
                import json
                clarification_data = json.loads(cleaned_content)
                logger.info(f"Generated intelligent clarification for {section_type.value}: {clarification_data['question'][:100]}...")
                return clarification_data
            except json.JSONDecodeError as e:
                # Enhanced fallback - try to extract question from malformed JSON
                logger.warning(f"Failed to parse clarification JSON for {section_type.value}: {str(e)}")
                logger.warning(f"Raw content: {content[:200]}...")
                
                # Try to extract a reasonable question from the content
                if '"question":' in content:
                    try:
                        # Extract the question value from the malformed JSON
                        question_start = content.find('"question":') + 11
                        question_content = content[question_start:].strip()
                        if question_content.startswith('"'):
                            question_end = question_content.find('"', 1)
                            if question_end > 0:
                                extracted_question = question_content[1:question_end]
                                return {
                                    "category": "gap_analysis",
                                    "question": extracted_question,
                                    "context": f"Analysis suggests gaps between your {section_type.value} and job requirements.",
                                    "specific_gaps": []
                                }
                    except Exception:
                        pass
                
                # Final fallback to section-specific questions
                fallback_questions = {
                    SectionType.SKILLS: "The job description mentions specific technologies that aren't clearly reflected in your skills section. Could you clarify which of these technologies you have experience with?",
                    SectionType.EXPERIENCE: "Your experience section could be strengthened with specific achievements or metrics. Can you provide quantifiable results from your roles?",
                    SectionType.PROJECTS: "Your projects would benefit from specific outcomes or technical details. Can you share results, technologies used, or measurable impact?",
                    SectionType.EDUCATION: "Are there relevant courses, projects, or achievements from your education that align with this job's requirements?"
                }
                
                return {
                    "category": "gap_analysis",
                    "question": fallback_questions.get(section_type, f"Could you provide additional details about your {section_type.value} that might be relevant to this position?"),
                    "context": f"Analysis suggests gaps between your {section_type.value} and job requirements.",
                    "specific_gaps": []
                }
                
        except Exception as e:
            logger.error(f"Error generating intelligent clarification for {section_type.value}: {str(e)}")
            # Fallback to section-specific defaults
            fallback_questions = {
                SectionType.SKILLS: {
                    "question": "The job description mentions specific technologies that aren't clearly reflected in your skills section. Could you clarify which of these technologies you have experience with?",
                    "context": "Ensuring accurate representation of your technical capabilities"
                },
                SectionType.EXPERIENCE: {
                    "question": "Your experience section could be strengthened with specific achievements or metrics. Can you provide quantifiable results from your roles?",
                    "context": "Adding measurable impact to demonstrate your contributions"
                },
                SectionType.PROJECTS: {
                    "question": "Your projects would benefit from specific outcomes or technical details. Can you share results, technologies used, or measurable impact?",
                    "context": "Highlighting the technical depth and impact of your work"
                },
                SectionType.EDUCATION: {
                    "question": "Are there relevant courses, projects, or achievements from your education that align with this job's requirements?",
                    "context": "Showcasing relevant academic background for the role"
                }
            }
            
            default = fallback_questions.get(section_type, {
                "question": f"Could you provide additional details about your {section_type.value} that might be relevant to this position?",
                "context": "Gathering additional relevant information"
            })
            
            return {
                "category": "gap_analysis",
                "question": default["question"],
                "context": default["context"],
                "specific_gaps": []
            }
    
    async def _detect_fabrication_and_clarify(self, section_type: SectionType, original_content: str, job_description: str) -> dict:
        """
        Detect potential fabrication opportunities and generate clarification questions
        instead of allowing the agent to hallucinate content.
        """
        
        fabrication_detection_prompt = f"""
CRITICAL FABRICATION DETECTION SYSTEM

You are a strict resume enhancement system that prevents misleading information from being added.

ORIGINAL {section_type.value.upper()} CONTENT:
{original_content}

JOB DESCRIPTION REQUIREMENTS:
{job_description}

FABRICATION DETECTION PRIORITIES:
1. CRITICAL FABRICATION RISKS (ALWAYS requires clarification):
   - Any percentage claims not in original (e.g., "50% increase", "30% improvement")
   - Specific numeric achievements not mentioned (e.g., "reduced latency by 10%")
   - Impact metrics not provided by user (e.g., "increased efficiency", "improved performance")
   - Technologies/skills completely absent from original content
   - Projects, roles, or experiences not mentioned
   - Specific company achievements or business outcomes not stated

2. SAFE IMPROVEMENTS (always allowed):
   - Formatting and organization improvements
   - Better wording of existing content (without adding claims)
   - Restructuring existing information
   - Professional language enhancement
   - Grammar and clarity improvements

3. MEDIUM RISK (proceed with extreme caution):
   - Minor context that doesn't add claims or metrics
   - Industry-standard terminology for clearly existing concepts

SPECIFIC METRIC FABRICATION DETECTION:
- Look for: percentages (%), numbers with impact claims, business metrics, performance improvements
- If ANY metric, percentage, or specific achievement number appears in job requirements but NOT in original content → HIGH RISK
- If user didn't provide specific outcomes, don't invent them

CONSERVATIVE ANALYSIS REQUIRED:
- If job description asks for "improved performance" but original doesn't mention specific improvements → CLARIFICATION NEEDED
- If job mentions "reduced costs" but original has no cost reduction claims → CLARIFICATION NEEDED  
- If job wants "increased efficiency" but original lacks efficiency metrics → CLARIFICATION NEEDED

OUTPUT FORMAT (JSON):
{{
    "fabrication_risks": [
        {{
            "item": "specific metric/achievement/detail that would be fabricated",
            "risk_level": "high|medium|low",
            "reason": "why this is fabrication risk (be specific about metrics/percentages)",
            "clarification_question": "ask user for specific details needed"
        }}
    ],
    "safe_enhancements": [
        "specific formatting/wording improvements that add NO new claims"
    ],
    "needs_user_input": [
        {{
            "category": "metrics|achievements|skills|experience|education|projects",
            "question": "specific clarification question about missing details",
            "context": "why this clarification prevents fabrication"
        }}
    ]
}}

BE EXTREMELY CONSERVATIVE about metrics and achievements. When in doubt, ask for clarification rather than risk fabrication.
"""

        try:
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "system", "content": fabrication_detection_prompt}],
                temperature=0.1,  # Lower temperature for more conservative detection
                max_tokens=1200
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
        
        # CRITICAL: Check for fabricated metrics and achievements across ALL sections
        fabricated_metrics = self._detect_fabricated_metrics(original_content, suggested_content)
        if fabricated_metrics:
            verification_issues.append({
                "severity": "critical",
                "issue": "fabricated_metrics",
                "description": f"Suggestion adds metrics/achievements not in original: {fabricated_metrics}",
                "action": "remove_fabricated_metrics"
            })
        
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
        
        # Experience section specific checks (NEW - this was missing!)
        elif section_type == SectionType.EXPERIENCE:
            # Check for fabricated achievements and responsibilities
            fabricated_achievements = self._detect_fabricated_achievements(original_content, suggested_content)
            if fabricated_achievements:
                verification_issues.append({
                    "severity": "critical",
                    "issue": "fabricated_achievements",
                    "description": f"Suggestion adds achievements not in original: {fabricated_achievements}",
                    "action": "remove_fabricated_content"
                })
            
            # Check for added responsibilities not mentioned in original
            fabricated_responsibilities = self._detect_fabricated_responsibilities(original_content, suggested_content)
            if fabricated_responsibilities:
                verification_issues.append({
                    "severity": "high",
                    "issue": "fabricated_responsibilities",
                    "description": f"Suggestion adds responsibilities not in original: {fabricated_responsibilities}",
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
        
        # Projects section specific checks (NEW)
        elif section_type == SectionType.PROJECTS:
            # Check for fabricated project details
            fabricated_project_details = self._detect_fabricated_project_details(original_content, suggested_content)
            if fabricated_project_details:
                verification_issues.append({
                    "severity": "critical",
                    "issue": "fabricated_project_details",
                    "description": f"Suggestion adds project details not in original: {fabricated_project_details}",
                    "action": "remove_fabricated_content"
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
    
    def _detect_fabricated_metrics(self, original_content: str, suggested_content: str) -> list:
        """Detect fabricated metrics, percentages, and numeric achievements."""
        import re
        
        # Extract metrics from both contents
        metric_patterns = [
            r'\d+%',  # Percentages like 50%
            r'\d+x',  # Multipliers like 2x
            r'\d+\s*(?:times|fold)',  # "3 times", "5-fold"
            r'(?:increased?|improved?|reduced?|decreased?|enhanced?|optimized?)\s+(?:by\s+)?\d+',  # "increased by 50"
            r'\d+\s*(?:seconds?|minutes?|hours?|days?|weeks?|months?|years?)',  # Time metrics
            r'\$\d+',  # Money amounts
            r'\d+(?:,\d{3})*\s*(?:users?|customers?|clients?|records?|entries?|items?|files?)',  # Count metrics
        ]
        
        fabricated_metrics = []
        
        for pattern in metric_patterns:
            original_metrics = set(re.findall(pattern, original_content, re.IGNORECASE))
            suggested_metrics = set(re.findall(pattern, suggested_content, re.IGNORECASE))
            
            # Find metrics in suggestion that weren't in original
            new_metrics = suggested_metrics - original_metrics
            fabricated_metrics.extend(new_metrics)
        
        return fabricated_metrics
    
    def _detect_fabricated_achievements(self, original_content: str, suggested_content: str) -> list:
        """Detect fabricated achievements and accomplishments."""
        import re
        
        # Common achievement indicators that shouldn't be fabricated
        achievement_patterns = [
            r'(?:led|managed|directed|coordinated|spearheaded|initiated)\s+[^.]+',
            r'(?:achieved|accomplished|delivered|completed)\s+[^.]+',
            r'(?:resulting in|leading to|causing|enabling)\s+[^.]+',
            r'(?:improved|enhanced|optimized|streamlined|automated)\s+[^.]+',
            r'(?:reduced|decreased|minimized|eliminated)\s+[^.]+',
            r'(?:increased|boosted|maximized|elevated)\s+[^.]+',
        ]
        
        fabricated_achievements = []
        
        for pattern in achievement_patterns:
            original_achievements = set(re.findall(pattern, original_content, re.IGNORECASE))
            suggested_achievements = set(re.findall(pattern, suggested_content, re.IGNORECASE))
            
            # Find achievements in suggestion that weren't in original
            new_achievements = suggested_achievements - original_achievements
            # Only flag if they contain specific metrics or claims
            for achievement in new_achievements:
                if any(indicator in achievement.lower() for indicator in ['%', 'increase', 'decrease', 'improve', 'reduce', 'efficiency', 'performance']):
                    fabricated_achievements.append(achievement[:100] + "..." if len(achievement) > 100 else achievement)
        
        return fabricated_achievements
    
    def _detect_fabricated_responsibilities(self, original_content: str, suggested_content: str) -> list:
        """Detect fabricated responsibilities and duties."""
        # Extract bullet points and major responsibilities
        original_bullets = [line.strip() for line in original_content.split('\n') if line.strip().startswith(('•', '-', '*'))]
        suggested_bullets = [line.strip() for line in suggested_content.split('\n') if line.strip().startswith(('•', '-', '*'))]
        
        # Find responsibilities that are completely new
        fabricated_responsibilities = []
        for suggested_bullet in suggested_bullets:
            # Check if this responsibility has any similarity to original content
            if not any(self._calculate_bullet_similarity(suggested_bullet, original_bullet) > 0.6 
                      for original_bullet in original_bullets):
                # This might be a completely fabricated responsibility
                fabricated_responsibilities.append(suggested_bullet[:100] + "..." if len(suggested_bullet) > 100 else suggested_bullet)
        
        return fabricated_responsibilities[:3]  # Limit to prevent overwhelming output
    
    def _detect_fabricated_project_details(self, original_content: str, suggested_content: str) -> list:
        """Detect fabricated project details and technologies."""
        original_technologies = set(self._extract_skills_from_text(original_content))
        suggested_technologies = set(self._extract_skills_from_text(suggested_content))
        
        # Find technologies in projects that weren't mentioned in original
        fabricated_techs = suggested_technologies - original_technologies
        
        return list(fabricated_techs)[:5]  # Limit output
    
    def _calculate_bullet_similarity(self, bullet1: str, bullet2: str) -> float:
        """Calculate similarity between two bullet points."""
        words1 = set(bullet1.lower().split())
        words2 = set(bullet2.lower().split())
        
        if not words1 and not words2:
            return 1.0
        if not words1 or not words2:
            return 0.0
        
        intersection = words1 & words2
        union = words1 | words2
        
        return len(intersection) / len(union) if union else 0.0
    
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
            logger.error(f"Error in primary scoring: {str(e)}")
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
            logger.warning(f"Judgment evaluation error (non-critical): {str(e)}")
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
            
            logger.info(f"Parsed {len(processed_sections)} sections: {list(processed_sections.keys())}")
            return processed_sections
            
        except Exception as e:
            logger.error(f"Error parsing resume sections: {str(e)}")
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
            logger.error(f"Error in job analysis: {str(e)}")
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
        """
        Handle user clarification and re-analyze specific section.
        Now works with the improved flow that processes all sections.
        """
        if session_id not in self.sessions:
            return {"success": False, "error": "Session not found"}
        
        session = self.sessions[session_id]
        
        # Check if this section has a pending clarification
        pending_clarifications = session.get("pending_clarifications", {})
        if section_type not in pending_clarifications:
            return {"success": False, "error": f"No pending clarification for section {section_type}"}
        
        logger.info(f"Processing clarification for {section_type} in session {session_id[:8]}")
        logger.info(f"User provided: {user_response[:100]}...")
        
        try:
            # Get the original content and job analysis
            parsed_sections = session["sections"]
            job_analysis = session["job_analysis"]
            pending_clarification = pending_clarifications[section_type]
            original_content = pending_clarification["original_content"]
            
            # Create enhanced content by incorporating user clarification
            enhanced_content = f"""
{original_content}

ADDITIONAL CONTEXT PROVIDED BY USER:
{user_response}
"""
            
            # Re-run analysis with user's additional context
            section_type_enum = next(
                (st for st in SectionType if st.value == section_type), 
                SectionType.EXPERIENCE  # fallback
            )
            
            # Run analysis again with enhanced context
            logger.info(f"Re-analyzing {section_type} with user clarification")
            analysis = await self._iterative_section_improvement_with_clarification(
                enhanced_content,
                original_content,  # Keep original separate
                section_type_enum,
                job_analysis,
                parsed_sections,
                user_response
            )
            
            # Store the updated analysis
            session["section_analyses"][section_type] = analysis
            
            # Remove this clarification from pending list
            del pending_clarifications[section_type]
            session["pending_clarifications"] = pending_clarifications
            
            # Update session state - only mark as no clarification if no more pending
            session["needs_clarification"] = len(pending_clarifications) > 0
            
                        # Log successful clarification
            monitor.log_agent_action("clarification_processed", {
                "session_id": session_id,
                "section_type": section_type,
                "user_response_length": len(user_response),
                "final_score": analysis.final_score,
                "remaining_clarifications": len(pending_clarifications)
            })
            
            return {
                "success": True,
                "analysis": {
                    "section_type": analysis.section_type.value,
                    "original_content": analysis.original_content,
                    "improved_content": analysis.best_content,
                    "score": analysis.final_score,
                    "feedback": analysis.improvement_journey,
                    "iteration_count": len(analysis.iterations),
                    "needs_clarification": False,
                    "clarification_request": None
                },
                "session_updated": True,
                "remaining_clarifications": list(pending_clarifications.keys()),
                "needs_more_clarification": len(pending_clarifications) > 0,
                "clarifications_completed": len(pending_clarifications) == 0
            }
        
        except Exception as e:
            logger.error(f"Error processing clarification for {section_type}: {str(e)}")
            return {
                "success": False,
                "error": f"Failed to process clarification: {str(e)}"
            }
    
    async def _iterative_section_improvement_with_clarification(
        self,
        enhanced_content: str,
        original_content: str,
        section_type: SectionType,
        job_analysis: JobAnalysis,
        all_sections: Dict[str, Dict[str, Any]],
        user_clarification: str
    ) -> SectionAnalysis:
        """
        Enhanced section improvement that incorporates user clarification.
        This bypasses fabrication detection since user provided the details.
        """
        logger.info(f"Re-analyzing {section_type.value} with user clarification")
        
        iterations = []
        current_content = original_content  # Start with original for comparison
        best_content = original_content
        best_score = 0
        
        # Initialize monitoring for this clarified section
        monitor.log_agent_action("clarified_section_analysis_started", {
            "section_type": section_type.value,
            "original_length": len(original_content),
            "clarification_length": len(user_clarification),
            "timestamp": datetime.now().isoformat()
        })
        
        # ITERATION LOOP: Improve with user's additional context
        for iteration in range(self.max_iterations):
            perspective = self.perspective_rotation[iteration % len(self.perspective_rotation)]
            
            try:
                # Generate improvement using both original content and user clarification
                improved_content = await self._generate_content_with_clarification(
                    original_content, 
                    user_clarification,
                    section_type, 
                    job_analysis, 
                    perspective, 
                    iteration + 1
                )
                
                # Score the improved content
                primary_score = await self._score_content_quality(
                    content=improved_content,
                    section_type=section_type,
                    job_analysis=job_analysis
                )
                
                # Get detailed evaluation
                evaluation = await self._self_evaluate_content(
                    improved_content, section_type, job_analysis, perspective
                )
                
                # Create iteration result
                iteration_result = IterationResult(
                    version=iteration + 1,
                    content=improved_content,
                    perspective=perspective,
                    quality_score=primary_score,
                    strengths=evaluation["strengths"],
                    weaknesses=evaluation["weaknesses"],
                    improvement_notes=evaluation["improvement_notes"],
                    timestamp=datetime.now()
                )
                
                iterations.append(iteration_result)
                
                # Track best version
                if primary_score > best_score:
                    best_content = improved_content
                    best_score = primary_score
                    logger.info(f"New best version! Score: {best_score}")
                
                # Check if we've reached excellence
                if primary_score >= self.quality_threshold:
                    logger.info(f"Excellence achieved with clarification! Score: {primary_score}")
                    break
                
                # Small delay to avoid rate limiting
                await asyncio.sleep(0.5)
                
            except Exception as e:
                logger.error(f"Analysis error with clarification: {str(e)}")
                break
        
        # Generate improvement journey narrative
        improvement_journey = f"Enhanced with user clarification: {user_clarification[:100]}..." if user_clarification else "Analysis completed with clarification."
        
        if iterations:
            best_iteration = max(iterations, key=lambda x: x.quality_score)
            improvement_journey = f"Applied user clarification and achieved {len(iterations)} iterations. {best_iteration.improvement_notes}"
        
        return SectionAnalysis(
            section_type=section_type,
            original_content=original_content,
            best_content=best_content,
            iterations=iterations,
            final_score=best_score,
            improvement_journey=improvement_journey,
            needs_clarification=False,  # Clarification has been provided
            clarification_request=None
        )
    
    async def _continue_analysis_after_clarification(
        self,
        session_id: str,
        parsed_sections: Dict[str, Dict[str, Any]],
        job_analysis: JobAnalysis
    ) -> Dict[str, Any]:
        """
        Continue processing remaining sections after clarification is provided.
        """
        session = self.sessions[session_id]
        current_index = session.get("current_section_index", 0)
        remaining_sections = []
        
        # Continue from where we left off
        for i, section_type in enumerate(self.analysis_order[current_index + 1:], current_index + 1):
            section_key = section_type.value
            session["current_section_index"] = i
            
            if section_key in parsed_sections and parsed_sections[section_key]["content"].strip():
                logger.info(f"Continuing with {section_key} section")
                
                try:
                    analysis = await self._iterative_section_improvement(
                        parsed_sections[section_key]["content"],
                        section_type,
                        job_analysis,
                        parsed_sections
                    )
                    
                    # Check if this section also needs clarification
                    if analysis.needs_clarification and analysis.clarification_request:
                        logger.warning(f"Another clarification needed: {section_key}")
                        
                        # Update session for next clarification
                        session["needs_clarification"] = True
                        session["pending_clarification"] = {
                            "section_type": section_key,
                            "question": analysis.clarification_request.question,
                            "context": analysis.clarification_request.context,
                            "reason": analysis.clarification_request.reason,
                            "original_content": analysis.clarification_request.original_content
                        }
                        
                        return {
                            "remaining_sections": remaining_sections,
                            "needs_clarification": True,
                            "pending_clarification": session["pending_clarification"]
                        }
                    
                    # No clarification needed, save and continue
                    session["section_analyses"][section_key] = analysis
                    remaining_sections.append({
                        "section_type": section_key,
                        "status": "completed",
                        "score": analysis.final_score
                    })
                    
                except Exception as e:
                    logger.error(f"Error continuing analysis for {section_key}: {str(e)}")
                    remaining_sections.append({
                        "section_type": section_key,
                        "status": "error",
                        "error": str(e)
                    })
        
        # All remaining sections completed
        return {
            "remaining_sections": remaining_sections,
            "needs_clarification": False,
            "pending_clarification": None
        }
    
    async def accept_section_changes(self, session_id: str, section_type: str, accepted: bool) -> Dict[str, Any]:
        """Accept or reject section changes and continue analysis if needed."""
        if session_id not in self.sessions:
            return {"success": False, "error": "Session not found"}
        
        session = self.sessions[session_id]
        # Always allow updates to change decisions
        session["accepted_changes"][section_type] = accepted
        logger.info(f"Section {section_type} changes {'accepted' if accepted else 'rejected'} in session {session_id}")
        
        # Check if this section exists in section_analyses (new system)
        section_analyses = session.get("section_analyses", {})
        if section_type in section_analyses:
            analysis = section_analyses[section_type]
            
            # If section needs clarification and user accepted, clear the clarification flag
            if analysis.needs_clarification and accepted:
                logger.info(f"User accepted safe changes for {section_type}, clearing clarification requirement")
                # Update the analysis to remove clarification requirement
                analysis.needs_clarification = False
                analysis.clarification_request = None
                
                # Remove from any pending clarifications collections
                pending_clarifications = session.get("pending_clarifications", {})
                if section_type in pending_clarifications:
                    del pending_clarifications[section_type]
                    session["pending_clarifications"] = pending_clarifications
                
                # Update session state
                session["section_analyses"][section_type] = analysis
        
        return {
            "success": True,
                    "message": f"Safe changes accepted for {section_type}",
                    "analysis_continued": False,  # No need to continue, just mark as accepted
                    "clarification_cleared": True
                }
        
        # LEGACY: Handle old pending_clarification system
        pending_clarification = session.get("pending_clarification")
        if pending_clarification and pending_clarification["section_type"] == section_type:
            logger.info(f"Continuing analysis after accepting {section_type} changes (legacy system)")
            
            # Clear the pending clarification since user accepted the safe improvements
            session["needs_clarification"] = False
            session["pending_clarification"] = None
            
            try:
                # Continue processing remaining sections
                parsed_sections = session["sections"]
                job_analysis = session["job_analysis"]
                
                remaining_sections_result = await self._continue_analysis_after_clarification(
                    session_id, parsed_sections, job_analysis
                )
                
                return {
                    "success": True,
                    "message": f"Changes {'accepted' if accepted else 'rejected'} for {section_type}",
                    "analysis_continued": True,
                    "remaining_sections": remaining_sections_result["remaining_sections"],
                    "needs_more_clarification": remaining_sections_result["needs_clarification"],
                    "pending_clarification": remaining_sections_result.get("pending_clarification")
                }
                
            except Exception as e:
                logger.error(f"Error continuing analysis after accepting {section_type}: {str(e)}")
                return {
                    "success": True,
                    "message": f"Changes {'accepted' if accepted else 'rejected'} for {section_type}",
                    "analysis_continued": False,
                    "error": f"Failed to continue analysis: {str(e)}"
                }
        
        return {
            "success": True,
            "message": f"Changes {'accepted' if accepted else 'rejected'} for {section_type}",
            "analysis_continued": False
        }
    
    async def generate_final_resume(self, session_id: str) -> Dict[str, Any]:
        """Generate final resume based on user's accepted/rejected changes."""
        if session_id not in self.sessions:
            logger.error(f"Session {session_id} not found in sessions: {list(self.sessions.keys())}")
            return {"success": False, "error": "Session not found"}
        
        session = self.sessions[session_id]
        sections = []
        accepted_changes = session.get("accepted_changes", {})
        section_analyses = session.get("section_analyses", {})
        
        logger.info(f"=== GENERATING FINAL RESUME FOR SESSION {session_id} ===")
        logger.info(f"Session keys: {list(session.keys())}")
        logger.info(f"Accepted changes: {accepted_changes}")
        logger.info(f"Available section analyses: {list(section_analyses.keys())}")
        
        # ENHANCED DEBUG: Also check parsed sections to see what was originally found
        parsed_sections = session.get("sections", {})
        logger.info(f"Originally parsed sections: {list(parsed_sections.keys())}")
        
        # ENHANCED DEBUG: Check for any missing sections
        analysis_order = [st.value for st in self.analysis_order]
        # missing_sections = [section for section in analysis_order if section in parsed_sections but section not in section_analyses]
        # if missing_sections:
        # logger.warning(f"❌ MISSING SECTIONS in section_analyses: {missing_sections}")
        # else:
        # logger.info(f"✅ All expected sections found in section_analyses")
        
        for section_type, analysis in section_analyses.items():
            logger.info(f"\n--- Processing section: {section_type} ---")
            logger.info(f"Analysis type: {type(analysis)}")
            logger.info(f"Has best_content: {hasattr(analysis, 'best_content')}")
            logger.info(f"Has original_content: {hasattr(analysis, 'original_content')}")
            
            if hasattr(analysis, 'best_content'):
                best_content_length = len(analysis.best_content) if analysis.best_content else 0
                original_content_length = len(analysis.original_content) if analysis.original_content else 0
                logger.info(f"Best content length: {best_content_length}")
                logger.info(f"Original content length: {original_content_length}")
                
                if analysis.best_content:
                    logger.info(f"Best content preview: {analysis.best_content[:100]}...")
                if analysis.original_content:
                    logger.info(f"Original content preview: {analysis.original_content[:100]}...")
            
            # Determine which content to use based on user decision
            if section_type in accepted_changes:
                if accepted_changes[section_type]:
                    # User accepted changes - use improved content if available, fallback to original
                    if analysis.best_content and analysis.best_content.strip():
                        content = analysis.best_content
                        logger.info(f"✅ ACCEPTED: Using improved content for {section_type} (length: {len(content)})")
                    else:
                        content = analysis.original_content
                        logger.info(f"✅ ACCEPTED: No improved content available, using original for {section_type} (length: {len(content) if content else 0})")
                else:
                    # User rejected changes - use original content
                    content = analysis.original_content
                    logger.info(f"❌ REJECTED: Using original content for {section_type} (length: {len(content) if content else 0})")
            else:
                # No decision made - default to improved content if available (safe improvements), otherwise original
                if analysis.best_content and analysis.best_content.strip() and not analysis.needs_clarification:
                    content = analysis.best_content
                    logger.info(f"⚪ NO DECISION: Using safe improved content for {section_type} (length: {len(content)})")
                else:
                    content = analysis.original_content
                    logger.info(f"⚪ NO DECISION: Using original content for {section_type} (length: {len(content) if content else 0})")
            
            if not content:
                logger.warning(f"⚠️ WARNING: No content found for {section_type}, skipping section")
                continue
            
            # Format section with proper header
            section_title = section_type.upper().replace('_', ' ')
            formatted_section = f"=== {section_title} ===\n{content}"
            sections.append(formatted_section)
            logger.info(f"✅ Added section {section_type} (formatted length: {len(formatted_section)})")
        
        final_resume = "\n\n".join(sections)
        
        logger.info(f"=== FINAL RESUME GENERATION COMPLETE ===")
        logger.info(f"Total sections included: {len(sections)}")
        logger.info(f"Final resume length: {len(final_resume)}")
        logger.info(f"Final resume preview: {final_resume[:200]}...")
        
        return {
            "success": True,
            "final_resume": final_resume,
            "sections": list(section_analyses.keys()),
            "session_id": session_id
        } 

    async def _generate_content_with_clarification(
        self,
        original_content: str,
        user_clarification: str,
        section_type: SectionType,
        job_analysis: JobAnalysis,
        perspective: AnalysisPerspective,
        iteration: int
    ) -> str:
        """
        Generate improved content incorporating user's clarification.
        This bypasses fabrication detection since user provided the details.
        """
        
        # Get section-specific formatting rules
        formatting_prompt = self.section_prompts.get(section_type, self.base_formatting_rules)
        
        system_prompt = f"""
ENHANCED CONTENT GENERATION WITH USER CLARIFICATION

You are enhancing resume content with additional context provided by the user.
Since the user provided clarification, you can now safely incorporate details that match job requirements.

ORIGINAL CONTENT:
{original_content}

USER'S ADDITIONAL CLARIFICATION:
{user_clarification}

JOB REQUIREMENTS ANALYSIS:
{job_analysis.requirements[:3]}

PERSPECTIVE: {perspective.value}
ITERATION: {iteration}

ENHANCED IMPROVEMENT RULES (with user clarification):
1. INCORPORATE USER DETAILS - Use the clarification to add specific, accurate information
2. MAINTAIN AUTHENTICITY - Only use details the user explicitly provided
3. PROFESSIONAL ENHANCEMENT - Improve presentation while staying truthful
4. KEYWORD INTEGRATION - Naturally incorporate relevant job keywords where appropriate
5. QUANTIFICATION ALLOWED - If user provided metrics/numbers, use them appropriately
6. SKILLS ENHANCEMENT - Add skills/technologies user mentioned in clarification
7. ACHIEVEMENT HIGHLIGHTING - Emphasize accomplishments user clarified

{formatting_prompt}

CLARIFICATION-ENHANCED APPROACH:
- Merge original content with user's additional details
- Create a cohesive, enhanced narrative
- Maintain professional tone and formatting
- Ensure all additions are based on user input
- Prioritize impact and relevance to target role

OUTPUT: Return ONLY the enhanced {section_type.value} content. No explanations.
"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Please enhance the {section_type.value} section using the user's clarification to create accurate, impactful content that aligns with the job requirements."}
        ]

        try:
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                temperature=0.3,  # Lower temperature for more consistent output
                max_tokens=1000
            )
            
            improved_content = response.choices[0].message.content.strip()
            
            # Log successful enhancement with clarification
            logger.info(f"Enhanced {section_type.value} with user clarification: {len(improved_content)} chars")
            
            return improved_content
            
        except Exception as e:
            logger.error(f"Error generating content with clarification: {str(e)}")
            # Fallback: return original content with user details appended
            return f"{original_content}\n\nAdditional Details: {user_clarification}"

    async def analyze_section(self, session_id: str, section_type: str) -> Dict[str, Any]:
        """
        Analyze a specific section - used by the API endpoint.
        This method handles both new analysis and returning existing results.
        """
        if session_id not in self.sessions:
            return {"success": False, "error": "Session not found"}
        
        session = self.sessions[session_id]
        
        # Check if this section already has analysis results
        if section_type in session.get("section_analyses", {}):
            analysis = session["section_analyses"][section_type]
            return {
                "success": True,
                "analysis": {
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
                }
            }
        
        # Check if there's a pending clarification for this section
        pending_clarification = session.get("pending_clarification")
        if pending_clarification and pending_clarification["section_type"] == section_type:
            return {
                "success": True,
                "analysis": {
                    "section_type": section_type,
                    "original_content": pending_clarification["original_content"],
                    "improved_content": None,
                    "score": 0,
                    "feedback": "Waiting for user clarification",
                    "iteration_count": 0,
                    "needs_clarification": True,
                    "clarification_request": {
                        "question": pending_clarification["question"],
                        "context": pending_clarification["context"],
                        "reason": pending_clarification["reason"]
                    }
                }
            }
        
        # Section not yet analyzed - this shouldn't happen in the human-in-the-loop flow
        # since start_analysis processes sections sequentially
        return {
            "success": False, 
            "error": f"Section {section_type} not yet reached in analysis pipeline"
        }