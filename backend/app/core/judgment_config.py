"""
Judgment Framework Configuration for Resume Agent
Provides comprehensive tracing, evaluation, and monitoring capabilities.
"""

import os
import logging
from typing import Dict, Any, List, Optional
from enum import Enum
from datetime import datetime

from judgeval.common.tracer import Tracer
from judgeval.scorers import (
    AnswerRelevancyScorer,
    FaithfulnessScorer,
    AnswerCorrectnessScorer,
    HallucinationScorer
)
from judgeval.data import Example
from judgeval import JudgmentClient

# Configure logging
logger = logging.getLogger(__name__)

# Initialize Judgment components
judgment = Tracer(
    api_key=os.getenv("JUDGMENT_API_KEY"),
    project_name="resume-critic-ai",
    enable_monitoring=True,
    deep_tracing=True
)

judgment_client = JudgmentClient()


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
        self.scorers = {
            ResumeMetrics.STRUCTURE_ACCURACY: AnswerCorrectnessScorer(threshold=0.8),
            ResumeMetrics.FORMATTING_QUALITY: AnswerRelevancyScorer(threshold=0.7),
            ResumeMetrics.JOB_RELEVANCE: AnswerRelevancyScorer(threshold=0.6),
            ResumeMetrics.CLARITY_CONCISENESS: AnswerRelevancyScorer(threshold=0.7),
            ResumeMetrics.CONTENT_FAITHFULNESS: FaithfulnessScorer(threshold=0.9),
            ResumeMetrics.IMPROVEMENT_QUALITY: HallucinationScorer(threshold=0.1)
        }
    
    def evaluate_section_improvement(
        self,
        original_content: str,
        improved_content: str,
        job_description: str,
        section_type: str,
        metric: ResumeMetrics = ResumeMetrics.IMPROVEMENT_QUALITY
    ) -> Dict[str, Any]:
        """Evaluate the quality of section improvements."""
        
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


class JudgmentMonitor:
    """
    Monitoring system for Resume Agent operations and error patterns.
    """
    
    def __init__(self):
        self.error_count = 0
        self.clarification_count = 0
        self.iteration_count = 0
        self.failed_suggestions = {"skills": 0, "experience": 0, "education": 0, "projects": 0}
        
    def log_agent_action(self, action_type: str, details: Dict[str, Any]):
        """Log agent actions for monitoring."""
        
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
    
    def log_error(self, error_type: str, error_details: Dict[str, Any]):
        """Log agent errors."""
        
        self.error_count += 1
        
        self.log_agent_action("error", {
            "error_type": error_type,
            "error_count": self.error_count,
            **error_details
        })
        
        logger.error(f"Agent error: {error_type} - {error_details}")
    
    def alert_unusual_pattern(self, pattern_description: str):
        """Alert on unusual patterns (can be extended to send actual alerts)."""
        
        self.log_agent_action("unusual_pattern_detected", {
            "pattern": pattern_description,
            "alert_level": "warning"
        })
        
        logger.warning(f"Unusual pattern detected: {pattern_description}")
    
    def log_quality_metrics(self, metrics: Dict[str, Any]):
        """Log quality metrics for trend analysis."""
        
        self.log_agent_action("quality_metrics", {
            "metrics": metrics,
            "timestamp": metrics.get("timestamp", datetime.now().isoformat())
        })
    
    def get_monitoring_summary(self) -> Dict[str, Any]:
        """Get comprehensive monitoring summary."""
        
        return {
            "total_errors": self.error_count,
            "total_clarifications": self.clarification_count,
            "total_iterations": self.iteration_count,
            "failed_suggestions_by_section": self.failed_suggestions,
            "monitoring_active": True
        }


# Global instances
evaluator = JudgmentEvaluator()
monitor = JudgmentMonitor()


def get_judgment_tracer() -> Tracer:
    """Get the global judgment tracer instance."""
    return judgment


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