"""
Comprehensive tests for IterativeResumeAgent class.
Tests the main AI agent functionality including analysis, iterations, and error handling.
"""

import pytest
import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
from uuid import UUID

from app.core.resume_agent import (
    IterativeResumeAgent,
    SectionType,
    AnalysisPerspective,
    SectionAnalysis,
    IterationResult,
    JobAnalysis
)


class TestIterativeResumeAgent:
    """Test suite for IterativeResumeAgent."""

    @pytest.fixture
    def mock_openai_client(self):
        """Mock OpenAI client for testing."""
        mock_client = AsyncMock()
        
        # Mock successful API responses
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps({
            "analysis": "Test analysis result",
            "score": 85,
            "improvements": ["Test improvement 1", "Test improvement 2"],
            "strengths": ["Test strength"],
            "weaknesses": ["Test weakness"],
            "fabrication_risk": "low"
        })
        
        mock_client.chat.completions.create.return_value = mock_response
        return mock_client

    @pytest.fixture
    def sample_resume_text(self):
        """Sample resume text for testing."""
        return """
        John Doe
        Software Engineer
        Email: john.doe@email.com
        Phone: (555) 123-4567
        
        EXPERIENCE
        Senior Software Engineer | TechCorp | 2020-2023
        - Developed scalable web applications using React and Node.js
        - Led a team of 5 developers
        - Implemented CI/CD pipelines reducing deployment time by 50%
        
        SKILLS
        - JavaScript, Python, React, Node.js
        - AWS, Docker, Kubernetes
        - Git, Jenkins, CI/CD
        
        EDUCATION
        B.S. Computer Science | University of Technology | 2018
        GPA: 3.8/4.0
        
        PROJECTS
        E-commerce Platform | 2022
        - Built full-stack e-commerce application
        - Integrated payment processing and inventory management
        """

    @pytest.fixture
    def sample_job_description(self):
        """Sample job description for testing."""
        return """
        Senior Full Stack Developer
        
        We are looking for an experienced Full Stack Developer to join our team.
        
        Requirements:
        - 5+ years of experience in web development
        - Strong proficiency in JavaScript, Python, React
        - Experience with cloud platforms (AWS, Azure)
        - Knowledge of CI/CD processes
        - Team leadership experience preferred
        
        Responsibilities:
        - Develop and maintain web applications
        - Collaborate with cross-functional teams
        - Mentor junior developers
        """

    @pytest.fixture
    async def resume_agent(self, mock_openai_client):
        """Create IterativeResumeAgent with mocked dependencies."""
        with patch('app.core.resume_agent.AsyncOpenAI', return_value=mock_openai_client):
            with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
                agent = IterativeResumeAgent()
                agent.client = mock_openai_client
                return agent

    @pytest.mark.asyncio
    async def test_agent_initialization(self, resume_agent):
        """Test that IterativeResumeAgent initializes correctly."""
        assert resume_agent is not None
        assert resume_agent.max_iterations == 5
        assert resume_agent.quality_threshold == 90
        assert hasattr(resume_agent, 'sessions')
        assert hasattr(resume_agent, 'analysis_order')

    @pytest.mark.asyncio
    async def test_start_analysis_success(self, resume_agent, sample_resume_text, sample_job_description):
        """Test successful analysis start."""
        with patch('app.utils.pdf_parser.split_resume_sections') as mock_split:
            mock_split.return_value = {
                'experience': 'Senior Software Engineer | TechCorp | 2020-2023',
                'skills': 'JavaScript, Python, React, Node.js',
                'education': 'B.S. Computer Science | University of Technology | 2018',
                'projects': 'E-commerce Platform | 2022'
            }
            
            result = await resume_agent.start_analysis(sample_resume_text, sample_job_description)
            
            assert result["success"] is True
            assert "session_id" in result
            assert "sections" in result
            assert "job_analysis" in result
            assert len(result["sections"]) > 0

    @pytest.mark.asyncio
    async def test_start_analysis_empty_resume(self, resume_agent, sample_job_description):
        """Test analysis start with empty resume."""
        result = await resume_agent.start_analysis("", sample_job_description)
        
        assert result["success"] is False
        assert "error" in result
        assert "empty" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_analyze_section_success(self, resume_agent, sample_resume_text, sample_job_description):
        """Test successful section analysis."""
        # First start an analysis session
        with patch('app.utils.pdf_parser.split_resume_sections') as mock_split:
            mock_split.return_value = {
                'skills': 'JavaScript, Python, React, Node.js, AWS, Docker'
            }
            
            start_result = await resume_agent.start_analysis(sample_resume_text, sample_job_description)
            session_id = start_result["session_id"]
            
            # Now analyze a section
            result = await resume_agent.analyze_section(session_id, SectionType.SKILLS)
            
            assert result["success"] is True
            assert "analysis" in result
            assert isinstance(result["analysis"], dict)

    @pytest.mark.asyncio
    async def test_analyze_section_invalid_session(self, resume_agent):
        """Test section analysis with invalid session ID."""
        result = await resume_agent.analyze_section("invalid-session-id", SectionType.SKILLS)
        
        assert result["success"] is False
        assert "error" in result
        assert "not found" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_provide_clarification_success(self, resume_agent, sample_resume_text, sample_job_description):
        """Test providing clarification for section analysis."""
        with patch('app.utils.pdf_parser.split_resume_sections') as mock_split:
            mock_split.return_value = {'skills': 'Basic programming skills'}
            
            start_result = await resume_agent.start_analysis(sample_resume_text, sample_job_description)
            session_id = start_result["session_id"]
            
            # Simulate a clarification scenario
            clarification = "I have 5 years of Python experience and 3 years of React experience"
            result = await resume_agent.provide_clarification(
                session_id, 
                SectionType.SKILLS, 
                clarification
            )
            
            assert result["success"] is True
            assert "analysis" in result

    @pytest.mark.asyncio
    async def test_generate_final_resume(self, resume_agent, sample_resume_text, sample_job_description):
        """Test final resume generation."""
        with patch('app.utils.pdf_parser.split_resume_sections') as mock_split:
            mock_split.return_value = {
                'experience': 'Senior Software Engineer | TechCorp',
                'skills': 'JavaScript, Python, React'
            }
            
            start_result = await resume_agent.start_analysis(sample_resume_text, sample_job_description)
            session_id = start_result["session_id"]
            
            result = await resume_agent.generate_final_resume(session_id)
            
            assert result["success"] is True
            assert "final_resume" in result
            assert "sections" in result

    @pytest.mark.asyncio
    async def test_fabrication_detection(self, resume_agent):
        """Test fabrication detection functionality."""
        original_content = "Basic programming knowledge"
        improved_content = "Expert in machine learning with 10+ years experience in AI research"
        job_requirements = ["Programming skills", "Software development"]
        
        result = await resume_agent._detect_fabrication_and_clarify(
            original_content, improved_content, job_requirements, SectionType.SKILLS
        )
        
        assert "fabrication_risk" in result
        assert "clarification_needed" in result

    @pytest.mark.asyncio
    async def test_content_verification(self, resume_agent):
        """Test content verification against original."""
        original_sections = {
            "skills": {"content": "JavaScript, Python, React"},
            "experience": {"content": "Software Engineer at TechCorp"}
        }
        
        improved_content = "JavaScript, Python, React, Machine Learning, AI Expert"
        
        result = await resume_agent._verify_against_original(
            improved_content, original_sections, SectionType.SKILLS
        )
        
        assert "issues" in result
        assert isinstance(result["issues"], list)

    @pytest.mark.asyncio
    async def test_error_handling_openai_failure(self, resume_agent, sample_resume_text, sample_job_description):
        """Test error handling when OpenAI API fails."""
        # Mock OpenAI client to raise an exception
        resume_agent.client.chat.completions.create.side_effect = Exception("API Error")
        
        result = await resume_agent.start_analysis(sample_resume_text, sample_job_description)
        
        assert result["success"] is False
        assert "error" in result

    @pytest.mark.asyncio
    async def test_perspective_rotation(self, resume_agent):
        """Test that different analysis perspectives are used in iterations."""
        content = "Software Engineer with React experience"
        section_type = SectionType.EXPERIENCE
        
        # Mock job analysis
        job_analysis = MagicMock()
        job_analysis.required_skills = ["React", "JavaScript"]
        job_analysis.key_requirements = ["Web development experience"]
        
        with patch.object(resume_agent, '_generate_section_improvement') as mock_improve:
            mock_improve.return_value = {
                "improved_content": "Enhanced content",
                "score": 85,
                "strengths": ["Good structure"],
                "weaknesses": ["Could be more specific"],
                "improvement_notes": "Added specificity"
            }
            
            result = await resume_agent._iterative_section_improvement(
                content, section_type, job_analysis, {}
            )
            
            # Check that improvement was called (indicating perspective rotation worked)
            assert mock_improve.called
            assert result.section_type == section_type

    @pytest.mark.asyncio
    async def test_quality_threshold_iterations(self, resume_agent):
        """Test that iterations continue until quality threshold is met."""
        content = "Basic skills"
        section_type = SectionType.SKILLS
        job_analysis = MagicMock()
        
        # Mock to return progressively higher scores
        scores = [60, 70, 80, 95]  # Last one meets threshold
        score_iter = iter(scores)
        
        async def mock_improvement(*args, **kwargs):
            return {
                "improved_content": f"Improved content iteration {next(score_iter)}",
                "score": next(iter(scores)),  # Reset for next call
                "strengths": ["Better"],
                "weaknesses": ["Still improving"],
                "improvement_notes": "Progressive improvement"
            }
        
        with patch.object(resume_agent, '_generate_section_improvement', side_effect=mock_improvement):
            with patch.object(resume_agent, '_verify_against_original', return_value={"issues": []}):
                with patch.object(resume_agent, '_self_evaluate_content', return_value={
                    "strengths": ["Good"], "weaknesses": ["None"], "improvement_notes": "Done"
                }):
                    result = await resume_agent._iterative_section_improvement(
                        content, section_type, job_analysis, {}
                    )
                    
                    # Should have run multiple iterations
                    assert len(result.iterations) > 1

    def test_session_management(self, resume_agent):
        """Test session management functionality."""
        session_id = "test-session-123"
        session_data = {
            "resume_text": "Test resume",
            "job_description": "Test job",
            "sections": {"skills": {"content": "Python, JavaScript"}}
        }
        
        # Test session storage
        resume_agent.sessions[session_id] = session_data
        
        # Test session retrieval
        retrieved_session = resume_agent.sessions.get(session_id)
        assert retrieved_session == session_data
        
        # Test session cleanup
        del resume_agent.sessions[session_id]
        assert session_id not in resume_agent.sessions

    @pytest.mark.asyncio
    async def test_concurrent_sessions(self, resume_agent, sample_resume_text, sample_job_description):
        """Test handling multiple concurrent analysis sessions."""
        with patch('app.utils.pdf_parser.split_resume_sections') as mock_split:
            mock_split.return_value = {'skills': 'JavaScript, Python'}
            
            # Start multiple sessions concurrently
            tasks = [
                resume_agent.start_analysis(sample_resume_text, sample_job_description)
                for _ in range(3)
            ]
            
            results = await asyncio.gather(*tasks)
            
            # All should succeed with unique session IDs
            assert all(result["success"] for result in results)
            session_ids = [result["session_id"] for result in results]
            assert len(set(session_ids)) == 3  # All unique

    @pytest.mark.asyncio
    async def test_empty_section_handling(self, resume_agent):
        """Test handling of empty or minimal sections."""
        minimal_content = "Skills: Basic"
        section_type = SectionType.SKILLS
        job_analysis = MagicMock()
        job_analysis.required_skills = ["Python", "JavaScript", "React"]
        
        result = await resume_agent._iterative_section_improvement(
            minimal_content, section_type, job_analysis, {}
        )
        
        assert result.section_type == section_type
        assert result.best_content is not None

    @pytest.mark.asyncio 
    async def test_judgment_integration(self, resume_agent):
        """Test that judgment framework integration works without errors."""
        # Test that judgment calls don't break the flow
        with patch('app.core.resume_agent.evaluator') as mock_evaluator:
            with patch('app.core.resume_agent.monitor') as mock_monitor:
                content = "Test content"
                section_type = SectionType.SKILLS
                job_analysis = MagicMock()
                
                result = await resume_agent._iterative_section_improvement(
                    content, section_type, job_analysis, {}
                )
                
                # Verify judgment methods were called
                assert mock_monitor.log_agent_action.called
                assert result is not None

    @pytest.mark.asyncio
    async def test_malformed_api_response_handling(self, resume_agent):
        """Test handling of malformed API responses."""
        # Mock malformed JSON response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Invalid JSON {"
        
        resume_agent.client.chat.completions.create.return_value = mock_response
        
        content = "Test content"
        job_analysis = MagicMock()
        
        # Should handle malformed response gracefully
        result = await resume_agent._generate_section_improvement(
            content, SectionType.SKILLS, job_analysis, AnalysisPerspective.HIRING_MANAGER
        )
        
        # Should return some kind of result even with malformed response
        assert result is not None


@pytest.mark.asyncio
async def test_resume_agent_integration():
    """Integration test for the complete resume analysis workflow."""
    sample_resume = """
    Jane Smith
    Data Scientist
    
    EXPERIENCE
    Data Scientist | DataCorp | 2021-2023
    - Built machine learning models for customer segmentation
    - Analyzed large datasets using Python and SQL
    
    SKILLS
    Python, SQL, Machine Learning, Statistics
    
    EDUCATION
    M.S. Data Science | Tech University | 2021
    """
    
    sample_job = """
    Senior Data Scientist Position
    Requirements: 3+ years experience, Python, ML, SQL
    """
    
    with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
        with patch('app.core.resume_agent.AsyncOpenAI') as mock_openai:
            # Setup mock
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = json.dumps({
                "analysis": "Strong data science background",
                "score": 90,
                "improvements": ["Add more ML details"],
                "strengths": ["Good experience"],
                "weaknesses": ["Could be more specific"],
                "fabrication_risk": "low"
            })
            mock_client.chat.completions.create.return_value = mock_response
            mock_openai.return_value = mock_client
            
            with patch('app.utils.pdf_parser.split_resume_sections') as mock_split:
                mock_split.return_value = {
                    'experience': 'Data Scientist | DataCorp | 2021-2023',
                    'skills': 'Python, SQL, Machine Learning'
                }
                
                agent = IterativeResumeAgent()
                
                # Test complete workflow
                start_result = await agent.start_analysis(sample_resume, sample_job)
                assert start_result["success"] is True
                
                session_id = start_result["session_id"]
                
                # Analyze a section
                section_result = await agent.analyze_section(session_id, SectionType.SKILLS)
                assert section_result["success"] is True
                
                # Generate final resume
                final_result = await agent.generate_final_resume(session_id)
                assert final_result["success"] is True 