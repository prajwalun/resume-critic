"""
Judgment Framework Configuration for Resume Agent
Provides comprehensive tracing, evaluation, and monitoring capabilities.
"""

import os
import logging
from typing import Dict, Any, List, Optional
from enum import Enum
from datetime import datetime

# Load environment variables first, before accessing them
from dotenv import load_dotenv

# Load .env file with proper path
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(os.path.dirname(current_dir))
env_path = os.path.join(backend_dir, ".env")
load_dotenv(dotenv_path=env_path)

# Configure logging
logger = logging.getLogger(__name__)

# Try to import judgment framework components
try:
    from judgeval.common.tracer import Tracer
    from judgeval.scorers import (
        AnswerRelevancyScorer,
        FaithfulnessScorer,
        AnswerCorrectnessScorer,
        HallucinationScorer
    )
    from judgeval.data import Example
    from judgeval import JudgmentClient
    JUDGMENT_IMPORTS_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Judgment framework imports not available: {e}")
    # Create dummy classes to prevent import errors
    Tracer = None
    AnswerRelevancyScorer = None
    FaithfulnessScorer = None
    AnswerCorrectnessScorer = None
    HallucinationScorer = None
    Example = None
    JudgmentClient = None
    JUDGMENT_IMPORTS_AVAILABLE = False


# Initialize Judgment components
try:
    judgment_api_key = os.getenv("JUDGMENT_API_KEY")
    if judgment_api_key and JUDGMENT_IMPORTS_AVAILABLE and Tracer is not None:
        judgment = Tracer(
            api_key=judgment_api_key,
            project_name="resume-critic-ai",
            enable_monitoring=True,
            deep_tracing=True
        )
        judgment_client = JudgmentClient()
        JUDGMENT_AVAILABLE = True
        logger.info("Judgment framework initialized successfully")
    else:
        # Fallback when no API key is available or imports failed
        judgment = None
        judgment_client = None
        JUDGMENT_AVAILABLE = False
        if not JUDGMENT_IMPORTS_AVAILABLE:
            logger.warning("Judgment framework not available - imports failed")
        else:
            logger.warning("JUDGMENT_API_KEY not set - using fallback mode")
except Exception as e:
    # Fallback for any judgment initialization errors
    JUDGMENT_AVAILABLE = False
    logger.warning(f"Judgment initialization failed: {str(e)} - using fallback mode")


class ResumeMetrics(Enum):
    """Resume-specific evaluation metrics"""
    STRUCTURE_ACCURACY = "structure_accuracy"
    FORMATTING_QUALITY = "formatting_quality" 
    JOB_RELEVANCE = "job_description_relevance"
    CLARITY_CONCISENESS = "clarity_conciseness"
    CONTENT_FAITHFULNESS = "content_faithfulness"
    IMPROVEMENT_QUALITY = "improvement_quality"


class JudgmentEvaluator:
    """
    Comprehensive evaluation system for Resume Agent decisions and outputs.
    """
    
    def __init__(self):
        if JUDGMENT_AVAILABLE and JUDGMENT_IMPORTS_AVAILABLE:
            self.scorers = {
                ResumeMetrics.STRUCTURE_ACCURACY: AnswerCorrectnessScorer(threshold=0.8) if AnswerCorrectnessScorer else None,
                ResumeMetrics.FORMATTING_QUALITY: AnswerRelevancyScorer(threshold=0.7) if AnswerRelevancyScorer else None,
                ResumeMetrics.JOB_RELEVANCE: AnswerRelevancyScorer(threshold=0.6) if AnswerRelevancyScorer else None,
                ResumeMetrics.CLARITY_CONCISENESS: AnswerRelevancyScorer(threshold=0.7) if AnswerRelevancyScorer else None,
                ResumeMetrics.CONTENT_FAITHFULNESS: FaithfulnessScorer(threshold=0.9) if FaithfulnessScorer else None,
                ResumeMetrics.IMPROVEMENT_QUALITY: HallucinationScorer(threshold=0.1) if HallucinationScorer else None
            }
        else:
            self.scorers = {}
    
    def evaluate_section_improvement(
        self,
        original_content: str,
        improved_content: str,
        job_description: str,
        section_type: str,
        metric: ResumeMetrics = ResumeMetrics.IMPROVEMENT_QUALITY
    ) -> Dict[str, Any]:
        """Evaluate the quality of section improvements."""
        
        if not JUDGMENT_AVAILABLE or not judgment:
            return {
                "metric": metric.value,
                "original_length": len(original_content),
                "improved_length": len(improved_content),
                "section_type": section_type,
                "evaluation_submitted": False,
                "reason": "Judgment framework not available"
            }
        
        example = Example(
            input=f"Original {section_type}: {original_content}\nJob Description: {job_description}",
            actual_output=improved_content,
            expected_output=original_content,  # Use original as baseline
            retrieval_context=[job_description, original_content]
        )
        
        # Run evaluation asynchronously
        judgment.async_evaluate(
            scorers=[self.scorers[metric]],
            example=example,
            model="gpt-4o-mini"
        )
        
        return {
            "metric": metric.value,
            "original_length": len(original_content),
            "improved_length": len(improved_content),
            "section_type": section_type,
            "evaluation_submitted": True
        }
    
    def evaluate_agent_decision(
        self,
        decision_context: str,
        decision_made: str,
        reasoning: str,
        confidence_score: float
    ) -> Dict[str, Any]:
        """Evaluate agent decision-making quality."""
        
        if not JUDGMENT_AVAILABLE or not judgment:
            return {
                "decision_evaluated": False,
                "confidence_score": confidence_score,
                "reason": "Judgment framework not available"
            }
        
        example = Example(
            input=decision_context,
            actual_output=f"Decision: {decision_made}\nReasoning: {reasoning}",
            metadata={
                "confidence_score": confidence_score,
                "decision_type": "agent_decision"
            }
        )
        
        judgment.async_evaluate(
            scorers=[AnswerRelevancyScorer(threshold=0.8)],
            example=example,
            model="gpt-4o-mini"
        )
        
        return {
            "decision_evaluated": True,
            "confidence_score": confidence_score
        }
    
    def evaluate_final_resume_quality(
        self,
        original_resume: str,
        final_resume: str,
        job_description: str,
        user_decisions: Dict[str, bool],
        session_metrics: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Evaluate the final resume quality and user satisfaction."""
        
        if not JUDGMENT_AVAILABLE or not judgment:
            return {
                "evaluation_completed": False,
                "reason": "Judgment framework not available"
            }
        
        try:
            # Comprehensive final resume evaluation
            example = Example(
                input=f"Original Resume:\n{original_resume}\n\nJob Description:\n{job_description}",
                actual_output=final_resume,
                metadata={
                    "user_decisions": user_decisions,
                    "session_metrics": session_metrics,
                    "evaluation_type": "final_resume"
                }
            )
            
            # Multi-metric evaluation
            if JUDGMENT_IMPORTS_AVAILABLE:
                judgment.async_evaluate(
                    scorers=[
                        AnswerRelevancyScorer(threshold=0.8),
                        AnswerCorrectnessScorer(threshold=0.7),
                        FaithfulnessScorer(threshold=0.9)
                    ],
                    example=example,
                    model="gpt-4o-mini"
                )
            
            logger.info(f"Final resume evaluation initiated with {len(user_decisions)} user decisions")
            
            return {
                "evaluation_completed": True,
                "session_metrics": session_metrics
            }
            
        except Exception as e:
            logger.warning(f"Final resume evaluation error: {str(e)}")
            return {
                "evaluation_completed": False,
                "error": str(e)
            }


class JudgmentMonitor:
    """
    Monitoring system for Resume Agent operations and error patterns.
    """
    
    def __init__(self):
        self.error_count = 0
        self.clarification_count = 0
        self.iteration_count = 0
        self.failed_suggestions = {"skills": 0, "experience": 0, "education": 0, "projects": 0}
        self.session_metrics = {}  # Track per-session metrics
        
    def log_agent_action(self, action_type: str, details: Dict[str, Any]):
        """Log agent actions for monitoring."""
        
        if JUDGMENT_AVAILABLE and judgment:
            # Use judgment's observe decorator to track actions
            with judgment.trace(f"agent_action_{action_type}") as trace:
                trace.metadata = {
                    "action_type": action_type,
                    "timestamp": details.get("timestamp"),
                    "section": details.get("section"),
                    "success": details.get("success", True),
                    "details": details
                }
        
        logger.info(f"Agent action logged: {action_type} - {details}")
    
    def log_user_clarification(self, section: str, clarification_request: str):
        """Log when agent requests user clarification."""
        
        self.clarification_count += 1
        
        self.log_agent_action("user_clarification_requested", {
            "section": section,
            "clarification_request": clarification_request,
            "clarification_number": self.clarification_count
        })
    
    def log_iteration_attempt(self, section: str, iteration_number: int, success: bool):
        """Log agent iteration attempts."""
        
        self.iteration_count += 1
        
        if not success:
            self.failed_suggestions[section] = self.failed_suggestions.get(section, 0) + 1
        
        self.log_agent_action("iteration_attempt", {
            "section": section,
            "iteration_number": iteration_number,
            "success": success,
            "total_iterations": self.iteration_count,
            "failed_suggestions_count": self.failed_suggestions[section]
        })
        
        # Alert on unusual patterns
        if self.failed_suggestions[section] >= 5:
            self.alert_unusual_pattern(f"5+ failed {section} suggestions in a row")
    
    def log_error(self, error_type: str, details: Dict[str, Any]):
        """Log errors for pattern analysis."""
        
        self.error_count += 1
        section = details.get("section_type", "unknown")
        
        if section in self.failed_suggestions:
            self.failed_suggestions[section] += 1
        
        if JUDGMENT_AVAILABLE and judgment:
            with judgment.trace(f"error_{error_type}") as trace:
                trace.metadata = {
                    "error_type": error_type,
                    "error_count": self.error_count,
                    "section": section,
                    "timestamp": datetime.now().isoformat(),
                    "details": details
                }
        
        logger.error(f"Error logged: {error_type} - {details}")
    
    def alert_unusual_pattern(self, pattern_description: str):
        """Alert on unusual patterns (can be extended to send actual alerts)."""
        
        self.log_agent_action("unusual_pattern_detected", {
            "pattern": pattern_description,
            "alert_level": "warning"
        })
        
        logger.warning(f"Unusual pattern detected: {pattern_description}")
    
    def log_quality_metrics(self, metrics: Dict[str, Any]):
        """Log quality metrics for trend analysis."""
        
        if JUDGMENT_AVAILABLE and judgment:
            with judgment.trace("quality_metrics") as trace:
                trace.metadata = metrics
        
        logger.info(f"Quality metrics: {metrics}")
    
    def log_session_completion(self, session_id: str, session_data: Dict[str, Any]):
        """Log complete session metrics for comprehensive evaluation."""
        
        session_metrics = {
            "session_id": session_id,
            "sections_analyzed": len(session_data.get("section_analyses", {})),
            "clarifications_requested": len(session_data.get("pending_clarifications", {})),
            "accepted_changes": len([v for v in session_data.get("accepted_changes", {}).values() if v]),
            "rejected_changes": len([v for v in session_data.get("accepted_changes", {}).values() if not v]),
            "completion_timestamp": datetime.now().isoformat()
        }
        
        self.session_metrics[session_id] = session_metrics
        
        if JUDGMENT_AVAILABLE and judgment:
            with judgment.trace("session_completion") as trace:
                trace.metadata = session_metrics
        
        logger.info(f"Session completed: {session_metrics}")
        
        return session_metrics
    
    def get_monitoring_summary(self) -> Dict[str, Any]:
        """Get comprehensive monitoring summary."""
        
        return {
            "total_errors": self.error_count,
            "total_clarifications": self.clarification_count,
            "total_iterations": self.iteration_count,
            "failed_suggestions_by_section": self.failed_suggestions,
            "monitoring_active": True,
            "judgment_available": JUDGMENT_AVAILABLE
        }


# Global instances
evaluator = JudgmentEvaluator()
monitor = JudgmentMonitor()


def get_judgment_tracer():
    """Get the global judgment tracer instance."""
    if JUDGMENT_AVAILABLE and judgment:
        return judgment
    return None


def get_judgment_evaluator() -> JudgmentEvaluator:
    """Get the global judgment evaluator instance."""
    return evaluator


def get_judgment_monitor() -> JudgmentMonitor:
    """Get the global judgment monitor instance."""
    return monitor


def setup_judgment_environment():
    """Setup judgment environment variables and configuration."""
    
    if not os.getenv("JUDGMENT_API_KEY"):
        logger.warning("JUDGMENT_API_KEY not set - judgment tracing may not work")
    
    if not os.getenv("JUDGMENT_ORG_ID"):
        logger.warning("JUDGMENT_ORG_ID not set - judgment tracing may not work")
    
    logger.info("Judgment framework initialized for Resume Agent")
    return True 