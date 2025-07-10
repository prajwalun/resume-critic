"""
Comprehensive tests for fabrication detection and prevention system.
Tests ensure no misleading metrics or achievements are added to resumes.
"""

import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch
from app.core.resume_agent import IterativeResumeAgent, SectionType


class TestFabricationDetection:
    """Test suite for fabrication detection and prevention."""

    @pytest.fixture
    def agent(self):
        """Create agent instance for testing."""
        with patch('app.core.resume_agent.AsyncOpenAI'):
            agent = IterativeResumeAgent()
            agent.client = AsyncMock()
            return agent

    @pytest.fixture
    def sample_experience_original(self):
        """Original experience content without metrics."""
        return """
        ReKindle | Mobile App Developer | Jun 2025 - Jun 2025
        - Developed a mobile app for personalized networking follow-ups
        - Collaborated with team of designers and developers  
        - Designed privacy-first architecture with local storage
        - Enhanced usability by adding support for dark mode
        """

    @pytest.fixture
    def fabricated_experience_suggestion(self):
        """Suggestion with fabricated metrics - should be REJECTED."""
        return """
        ReKindle | Mobile App Developer | Jun 2025 - Jun 2025
        - Developed a mobile app for personalized networking follow-ups, achieving a 50% increase in follow-up efficiency for users
        - Collaborated with team of designers and developers, resulting in a 35% increase in user satisfaction ratings
        - Designed privacy-first architecture with local storage, enhancing productivity and achieving a 20% increase in task completion rates
        - Enhanced usability by adding support for dark mode, leading to a 30% increase in app retention rates
        """

    @pytest.fixture
    def safe_experience_suggestion(self):
        """Safe suggestion with no fabricated metrics - should be ACCEPTED."""
        return """
        **ReKindle** | Mobile App Developer | Jun 2025 - Jun 2025
        - Developed a cross-platform mobile application enabling personalized networking follow-ups
        - Collaborated with multidisciplinary team of designers and developers to implement features
        - Designed privacy-first architecture utilizing local storage and offline support  
        - Enhanced user experience by implementing dark mode support and streamlined interface
        """

    def test_detect_fabricated_metrics(self, agent, sample_experience_original, fabricated_experience_suggestion):
        """Test detection of fabricated percentage metrics."""
        fabricated_metrics = agent._detect_fabricated_metrics(
            sample_experience_original, 
            fabricated_experience_suggestion
        )
        
        # Should detect all the fabricated percentages
        expected_metrics = ['50%', '35%', '20%', '30%']
        assert all(metric in str(fabricated_metrics) for metric in expected_metrics)
        assert len(fabricated_metrics) >= 4

    def test_detect_fabricated_achievements(self, agent, sample_experience_original, fabricated_experience_suggestion):
        """Test detection of fabricated achievement claims."""
        fabricated_achievements = agent._detect_fabricated_achievements(
            sample_experience_original,
            fabricated_experience_suggestion
        )
        
        # Should detect achievement claims with metrics
        assert len(fabricated_achievements) > 0
        # Check for achievement indicators with metrics
        achievement_text = ' '.join(fabricated_achievements).lower()
        assert any(word in achievement_text for word in ['increase', 'efficiency', 'satisfaction', 'retention'])

    def test_safe_improvements_not_flagged(self, agent, sample_experience_original, safe_experience_suggestion):
        """Test that safe improvements without fabrication are not flagged."""
        fabricated_metrics = agent._detect_fabricated_metrics(
            sample_experience_original,
            safe_experience_suggestion
        )
        
        fabricated_achievements = agent._detect_fabricated_achievements(
            sample_experience_original,
            safe_experience_suggestion
        )
        
        # Safe improvements should not be flagged as fabrication
        assert len(fabricated_metrics) == 0
        assert len(fabricated_achievements) == 0

    @pytest.mark.asyncio
    async def test_verification_rejects_fabricated_content(self, agent, sample_experience_original, fabricated_experience_suggestion):
        """Test that verification system rejects fabricated content."""
        verification_result = await agent._verify_suggestion_quality(
            sample_experience_original,
            fabricated_experience_suggestion,
            SectionType.EXPERIENCE
        )
        
        # Should reject due to fabricated metrics
        assert not verification_result["is_valid"]
        assert verification_result["recommendation"] == "reject"
        
        # Should have critical fabrication issues
        critical_issues = [issue for issue in verification_result["issues"] if issue["severity"] == "critical"]
        assert len(critical_issues) > 0
        
        # Should specifically flag fabricated metrics
        fabrication_issues = [issue for issue in verification_result["issues"] if "fabricated" in issue["issue"]]
        assert len(fabrication_issues) > 0

    @pytest.mark.asyncio
    async def test_verification_accepts_safe_content(self, agent, sample_experience_original, safe_experience_suggestion):
        """Test that verification system accepts safe improvements."""
        verification_result = await agent._verify_suggestion_quality(
            sample_experience_original,
            safe_experience_suggestion,
            SectionType.EXPERIENCE
        )
        
        # Should accept safe improvements
        assert verification_result["is_valid"]
        assert verification_result["recommendation"] != "reject"

    @pytest.mark.asyncio 
    async def test_fabrication_detection_triggers_clarification(self, agent):
        """Test that fabrication detection triggers clarification requests."""
        # Mock the fabrication detection to return high risks
        mock_fabrication_response = {
            "fabrication_risks": [
                {
                    "item": "50% increase in efficiency",
                    "risk_level": "high",
                    "reason": "Percentage metric not in original content",
                    "clarification_question": "What specific efficiency improvements did you achieve?"
                }
            ],
            "safe_enhancements": ["formatting improvements"],
            "needs_user_input": [
                {
                    "category": "metrics",
                    "question": "Please provide specific metrics for your achievements",
                    "context": "Job requires quantified results but original lacks specific numbers"
                }
            ]
        }
        
        # Mock the OpenAI response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps(mock_fabrication_response)
        agent.client.chat.completions.create.return_value = mock_response
        
        result = await agent._detect_fabrication_and_clarify(
            SectionType.EXPERIENCE,
            "Basic job responsibilities without metrics",
            "Job requires proven track record of efficiency improvements"
        )
        
        # Should detect fabrication risks
        assert len(result["fabrication_risks"]) > 0
        assert result["fabrication_risks"][0]["risk_level"] == "high"
        assert "efficiency" in result["fabrication_risks"][0]["item"]

    def test_detect_various_metric_patterns(self, agent):
        """Test detection of various fabricated metric patterns."""
        original = "Worked on database optimization and user interface improvements."
        
        suggestions_with_metrics = [
            "Worked on database optimization, improving performance by 40%",
            "Enhanced user interface, resulting in 2x better user engagement", 
            "Optimized database queries, reducing response time by 500ms",
            "Improved system efficiency, saving $50,000 annually",
            "Enhanced application performance, supporting 10,000 concurrent users"
        ]
        
        for suggestion in suggestions_with_metrics:
            fabricated_metrics = agent._detect_fabricated_metrics(original, suggestion)
            assert len(fabricated_metrics) > 0, f"Failed to detect metrics in: {suggestion}"

    def test_edge_cases_not_over_flagged(self, agent):
        """Test that edge cases are not over-flagged as fabrication."""
        original = "Worked on the project for 6 months using Python and React."
        safe_suggestion = "Developed the project over 6 months utilizing Python and React technologies."
        
        # Should not flag existing timeframes and technologies as fabrication
        fabricated_metrics = agent._detect_fabricated_metrics(original, safe_suggestion)
        assert len(fabricated_metrics) == 0

    @pytest.mark.asyncio
    async def test_comprehensive_anti_fabrication_workflow(self, agent):
        """Test complete anti-fabrication workflow from detection to clarification."""
        # Simulate a realistic fabrication scenario
        original_content = """
        Software Developer | TechCorp | 2023-2024
        - Built web applications using React and Node.js
        - Worked with database systems and APIs
        - Participated in code reviews and team meetings
        """
        
        # Mock OpenAI response for fabrication detection
        fabrication_response = {
            "fabrication_risks": [
                {
                    "item": "performance improvements with metrics",
                    "risk_level": "high", 
                    "reason": "Job requires quantified results but original lacks metrics",
                    "clarification_question": "What specific performance improvements did you achieve?"
                }
            ],
            "safe_enhancements": ["professional language enhancement", "action verb improvements"],
            "needs_user_input": [
                {
                    "category": "achievements",
                    "question": "Please provide specific metrics for your accomplishments",
                    "context": "Prevents fabrication of performance claims"
                }
            ]
        }
        
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps(fabrication_response)
        agent.client.chat.completions.create.return_value = mock_response
        
        # Test fabrication detection
        result = await agent._detect_fabrication_and_clarify(
            SectionType.EXPERIENCE,
            original_content,
            "Seeking candidates with proven track record of performance optimization and efficiency improvements"
        )
        
        # Should properly detect risks and request clarification
        assert len(result["fabrication_risks"]) > 0
        assert result["fabrication_risks"][0]["risk_level"] == "high"
        assert len(result["needs_user_input"]) > 0
        assert "metrics" in result["needs_user_input"][0]["question"].lower()

    def test_memory_compliance(self, agent):
        """Test that the system respects user's anti-fabrication preference."""
        # This test ensures the system follows user's documented preference
        # against misleading information, as stored in memory ID 2693499
        
        original = "Developed mobile app features"
        fabricated_suggestion = "Developed mobile app features, achieving 85% user satisfaction and 40% engagement boost"
        
        # System should detect and prevent this fabrication
        fabricated_metrics = agent._detect_fabricated_metrics(original, fabricated_suggestion)
        assert len(fabricated_metrics) >= 2  # Should catch both "85%" and "40%"
        
        # Should specifically detect percentage claims
        metrics_text = ' '.join(fabricated_metrics)
        assert "85%" in metrics_text or "40%" in metrics_text


if __name__ == "__main__":
    pytest.main([__file__]) 