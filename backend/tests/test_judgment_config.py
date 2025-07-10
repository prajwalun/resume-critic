"""
Comprehensive tests for Judgment Framework Configuration.
Tests the judgment tracer, evaluator, and monitor components.
"""

import pytest
import os
from unittest.mock import MagicMock, patch, Mock
from datetime import datetime

from app.core.judgment_config import (
    get_judgment_tracer,
    get_judgment_evaluator,
    get_judgment_monitor,
    JudgmentEvaluator,
    JudgmentMonitor,
    ResumeMetrics,
    setup_judgment_environment
)


class TestJudgmentConfig:
    """Test suite for judgment configuration components."""

    def test_judgment_tracer_getter(self):
        """Test get_judgment_tracer function."""
        tracer = get_judgment_tracer()
        # Should return None or tracer instance depending on availability
        assert tracer is None or hasattr(tracer, 'trace')

    def test_judgment_evaluator_getter(self):
        """Test get_judgment_evaluator function."""
        evaluator = get_judgment_evaluator()
        assert isinstance(evaluator, JudgmentEvaluator)
        assert hasattr(evaluator, 'evaluate_section_improvement')
        assert hasattr(evaluator, 'evaluate_agent_decision')

    def test_judgment_monitor_getter(self):
        """Test get_judgment_monitor function."""
        monitor = get_judgment_monitor()
        assert isinstance(monitor, JudgmentMonitor)
        assert hasattr(monitor, 'log_agent_action')
        assert hasattr(monitor, 'log_user_clarification')

    def test_resume_metrics_enum(self):
        """Test ResumeMetrics enum values."""
        expected_metrics = [
            "structure_accuracy",
            "formatting_quality", 
            "job_description_relevance",
            "clarity_conciseness",
            "content_faithfulness",
            "improvement_quality"
        ]
        
        for metric in ResumeMetrics:
            assert metric.value in expected_metrics

    @patch.dict(os.environ, {'JUDGMENT_API_KEY': 'test-key', 'JUDGMENT_ORG_ID': 'test-org'})
    def test_setup_judgment_environment_with_keys(self):
        """Test judgment environment setup with API keys."""
        result = setup_judgment_environment()
        assert result is True

    @patch.dict(os.environ, {}, clear=True)
    def test_setup_judgment_environment_without_keys(self):
        """Test judgment environment setup without API keys."""
        result = setup_judgment_environment()
        assert result is True  # Should still return True but log warnings


class TestJudgmentEvaluator:
    """Test suite for JudgmentEvaluator class."""

    @pytest.fixture
    def evaluator(self):
        """Create JudgmentEvaluator instance for testing."""
        return JudgmentEvaluator()

    def test_evaluator_initialization(self, evaluator):
        """Test JudgmentEvaluator initialization."""
        assert hasattr(evaluator, 'scorers')
        assert isinstance(evaluator.scorers, dict)

    def test_evaluate_section_improvement_without_judgment(self, evaluator):
        """Test section improvement evaluation when judgment is not available."""
        original_content = "Basic Python skills"
        improved_content = "Advanced Python programming with 3+ years experience in web development"
        job_description = "Python developer position requiring 2+ years experience"
        section_type = "skills"
        
        result = evaluator.evaluate_section_improvement(
            original_content=original_content,
            improved_content=improved_content,
            job_description=job_description,
            section_type=section_type,
            metric=ResumeMetrics.IMPROVEMENT_QUALITY
        )
        
        assert isinstance(result, dict)
        assert "metric" in result
        assert "original_length" in result
        assert "improved_length" in result
        assert "section_type" in result
        assert "evaluation_submitted" in result
        assert result["metric"] == ResumeMetrics.IMPROVEMENT_QUALITY.value
        assert result["section_type"] == section_type

    @patch('app.core.judgment_config.JUDGMENT_AVAILABLE', True)
    @patch('app.core.judgment_config.judgment')
    def test_evaluate_section_improvement_with_judgment(self, mock_judgment, evaluator):
        """Test section improvement evaluation with judgment available."""
        mock_judgment.async_evaluate = MagicMock()
        
        original_content = "Basic skills"
        improved_content = "Advanced skills with experience"
        job_description = "Job requiring advanced skills"
        section_type = "skills"
        
        result = evaluator.evaluate_section_improvement(
            original_content=original_content,
            improved_content=improved_content,
            job_description=job_description,
            section_type=section_type
        )
        
        assert result["evaluation_submitted"] is True
        mock_judgment.async_evaluate.assert_called_once()

    def test_evaluate_agent_decision_without_judgment(self, evaluator):
        """Test agent decision evaluation without judgment framework."""
        decision_context = "Section analysis for skills section"
        decision_made = "Accept improvements"
        reasoning = "Quality score above threshold"
        confidence_score = 0.85
        
        result = evaluator.evaluate_agent_decision(
            decision_context=decision_context,
            decision_made=decision_made,
            reasoning=reasoning,
            confidence_score=confidence_score
        )
        
        assert isinstance(result, dict)
        assert "decision_evaluated" in result
        assert "confidence_score" in result
        assert result["confidence_score"] == confidence_score
        assert result["decision_evaluated"] is False

    @patch('app.core.judgment_config.JUDGMENT_AVAILABLE', True)
    @patch('app.core.judgment_config.judgment')
    def test_evaluate_agent_decision_with_judgment(self, mock_judgment, evaluator):
        """Test agent decision evaluation with judgment available."""
        mock_judgment.async_evaluate = MagicMock()
        
        result = evaluator.evaluate_agent_decision(
            decision_context="Test context",
            decision_made="Test decision",
            reasoning="Test reasoning",
            confidence_score=0.9
        )
        
        assert result["decision_evaluated"] is True
        mock_judgment.async_evaluate.assert_called_once()

    def test_all_resume_metrics_coverage(self, evaluator):
        """Test that evaluator can handle all resume metrics."""
        for metric in ResumeMetrics:
            result = evaluator.evaluate_section_improvement(
                original_content="test",
                improved_content="improved test",
                job_description="test job",
                section_type="test_section",
                metric=metric
            )
            assert result["metric"] == metric.value


class TestJudgmentMonitor:
    """Test suite for JudgmentMonitor class."""

    @pytest.fixture
    def monitor(self):
        """Create JudgmentMonitor instance for testing."""
        return JudgmentMonitor()

    def test_monitor_initialization(self, monitor):
        """Test JudgmentMonitor initialization."""
        assert monitor.error_count == 0
        assert monitor.clarification_count == 0
        assert monitor.iteration_count == 0
        assert isinstance(monitor.failed_suggestions, dict)
        assert "skills" in monitor.failed_suggestions
        assert "experience" in monitor.failed_suggestions

    def test_log_agent_action_without_judgment(self, monitor):
        """Test logging agent action without judgment framework."""
        action_type = "test_action"
        details = {
            "timestamp": datetime.now().isoformat(),
            "section": "skills",
            "success": True
        }
        
        # Should not raise any exceptions
        monitor.log_agent_action(action_type, details)

    @patch('app.core.judgment_config.JUDGMENT_AVAILABLE', True)
    @patch('app.core.judgment_config.judgment')
    def test_log_agent_action_with_judgment(self, mock_judgment, monitor):
        """Test logging agent action with judgment framework."""
        mock_trace = MagicMock()
        mock_judgment.trace.return_value.__enter__ = Mock(return_value=mock_trace)
        mock_judgment.trace.return_value.__exit__ = Mock(return_value=None)
        
        action_type = "test_action"
        details = {"test": "data"}
        
        monitor.log_agent_action(action_type, details)
        
        mock_judgment.trace.assert_called_once_with(f"agent_action_{action_type}")

    def test_log_user_clarification(self, monitor):
        """Test logging user clarification requests."""
        section = "skills"
        clarification_request = "Please provide more details about your Python experience"
        
        initial_count = monitor.clarification_count
        monitor.log_user_clarification(section, clarification_request)
        
        assert monitor.clarification_count == initial_count + 1

    def test_log_iteration_attempt_success(self, monitor):
        """Test logging successful iteration attempt."""
        section = "experience"
        iteration_number = 1
        success = True
        
        initial_iteration_count = monitor.iteration_count
        initial_failed_count = monitor.failed_suggestions[section]
        
        monitor.log_iteration_attempt(section, iteration_number, success)
        
        assert monitor.iteration_count == initial_iteration_count + 1
        assert monitor.failed_suggestions[section] == initial_failed_count

    def test_log_iteration_attempt_failure(self, monitor):
        """Test logging failed iteration attempt."""
        section = "projects"
        iteration_number = 2
        success = False
        
        initial_failed_count = monitor.failed_suggestions[section]
        
        monitor.log_iteration_attempt(section, iteration_number, success)
        
        assert monitor.failed_suggestions[section] == initial_failed_count + 1

    def test_alert_unusual_pattern_trigger(self, monitor):
        """Test that unusual patterns trigger alerts."""
        section = "skills"
        
        # Simulate 5 failed attempts to trigger alert
        for i in range(5):
            monitor.log_iteration_attempt(section, i+1, success=False)
        
        # The 5th failure should trigger an alert
        assert monitor.failed_suggestions[section] == 5

    def test_log_error(self, monitor):
        """Test error logging functionality."""
        error_type = "api_error"
        error_details = {
            "message": "OpenAI API timeout",
            "endpoint": "/chat/completions"
        }
        
        initial_error_count = monitor.error_count
        monitor.log_error(error_type, error_details)
        
        assert monitor.error_count == initial_error_count + 1

    def test_log_quality_metrics(self, monitor):
        """Test quality metrics logging."""
        metrics = {
            "section_type": "skills",
            "primary_score": 85,
            "iteration": 2,
            "decision": "accept"
        }
        
        # Should not raise any exceptions
        monitor.log_quality_metrics(metrics)

    def test_get_monitoring_summary(self, monitor):
        """Test getting comprehensive monitoring summary."""
        # Add some test data
        monitor.error_count = 2
        monitor.clarification_count = 3
        monitor.iteration_count = 10
        monitor.failed_suggestions["skills"] = 1
        
        summary = monitor.get_monitoring_summary()
        
        assert isinstance(summary, dict)
        assert "total_errors" in summary
        assert "total_clarifications" in summary
        assert "total_iterations" in summary
        assert "failed_suggestions_by_section" in summary
        assert "monitoring_active" in summary
        assert "judgment_available" in summary
        
        assert summary["total_errors"] == 2
        assert summary["total_clarifications"] == 3
        assert summary["total_iterations"] == 10
        assert summary["monitoring_active"] is True

    def test_monitoring_state_persistence(self, monitor):
        """Test that monitoring state persists across multiple operations."""
        # Perform various operations
        monitor.log_error("test_error", {"details": "test"})
        monitor.log_user_clarification("skills", "test clarification")
        monitor.log_iteration_attempt("experience", 1, True)
        monitor.log_iteration_attempt("skills", 1, False)
        
        # Check final state
        summary = monitor.get_monitoring_summary()
        assert summary["total_errors"] == 1
        assert summary["total_clarifications"] == 1
        assert summary["total_iterations"] == 2
        assert summary["failed_suggestions_by_section"]["skills"] == 1
        assert summary["failed_suggestions_by_section"]["experience"] == 0


class TestJudgmentIntegration:
    """Integration tests for judgment framework components."""

    def test_all_components_work_together(self):
        """Test that all judgment components work together without errors."""
        tracer = get_judgment_tracer()
        evaluator = get_judgment_evaluator()
        monitor = get_judgment_monitor()
        
        # Test basic functionality
        result = evaluator.evaluate_section_improvement(
            original_content="test",
            improved_content="improved test",
            job_description="test job",
            section_type="test_section"
        )
        assert isinstance(result, dict)
        
        monitor.log_agent_action("test_action", {"test": "data"})
        
        summary = monitor.get_monitoring_summary()
        assert isinstance(summary, dict)

    @patch.dict(os.environ, {}, clear=True)
    def test_graceful_degradation_without_env_vars(self):
        """Test that system works gracefully without environment variables."""
        # Import should work even without env vars
        from app.core.judgment_config import (
            get_judgment_tracer,
            get_judgment_evaluator,
            get_judgment_monitor
        )
        
        tracer = get_judgment_tracer()
        evaluator = get_judgment_evaluator()
        monitor = get_judgment_monitor()
        
        # Should not be None even in fallback mode
        assert evaluator is not None
        assert monitor is not None

    def test_error_handling_in_judgment_operations(self):
        """Test error handling in judgment framework operations."""
        evaluator = get_judgment_evaluator()
        monitor = get_judgment_monitor()
        
        # Test with various invalid inputs
        result = evaluator.evaluate_section_improvement(
            original_content="",
            improved_content="",
            job_description="",
            section_type=""
        )
        assert isinstance(result, dict)
        
        # Monitor should handle empty details
        monitor.log_agent_action("test", {})
        
        # Should not raise exceptions
        monitor.log_error("", {})

    @patch('app.core.judgment_config.logger')
    def test_logging_integration(self, mock_logger):
        """Test that judgment config integrates properly with logging."""
        setup_judgment_environment()
        
        # Should have logged some messages
        assert mock_logger.info.called or mock_logger.warning.called


@pytest.mark.asyncio
async def test_judgment_config_in_agent_context():
    """Test judgment configuration in the context of the resume agent."""
    from app.core.judgment_config import (
        get_judgment_tracer,
        get_judgment_evaluator,
        get_judgment_monitor
    )
    
    # Simulate agent usage
    tracer = get_judgment_tracer()
    evaluator = get_judgment_evaluator()
    monitor = get_judgment_monitor()
    
    # Test workflow similar to what agent would do
    monitor.log_agent_action("start_analysis", {
        "timestamp": datetime.now().isoformat(),
        "session_id": "test-session"
    })
    
    evaluation_result = evaluator.evaluate_section_improvement(
        original_content="Python programming",
        improved_content="Advanced Python programming with 5+ years experience",
        job_description="Python developer role requiring 3+ years experience",
        section_type="skills"
    )
    
    monitor.log_quality_metrics({
        "section_type": "skills",
        "score": 85,
        "evaluation_result": evaluation_result
    })
    
    summary = monitor.get_monitoring_summary()
    
    # All operations should complete successfully
    assert evaluation_result is not None
    assert summary["monitoring_active"] is True 