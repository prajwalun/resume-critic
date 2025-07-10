"""
Comprehensive tests for IterativeResumeAgent class.
Tests the main AI agent functionality including analysis, iterations, error handling,
human-in-the-loop workflow, and judgment integration.
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
    JobAnalysis,
    ClarificationRequest
)


class TestIterativeResumeAgent:
    """Test suite for IterativeResumeAgent."""

    @pytest.fixture
    def mock_openai_client(self):
        """Mock OpenAI client for testing."""
        mock_client = AsyncMock()
        
        # Mock successful API responses with structured content
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Improved resume content with better formatting and keywords"
        
        mock_client.chat.completions.create.return_value = mock_response
        return mock_client

    @pytest.fixture
    def mock_judgment_components(self):
        """Mock judgment components for testing."""
        mock_judgment = MagicMock()
        mock_monitor = MagicMock()
        mock_evaluator = MagicMock()
        
        # Set up common mock behaviors
        mock_monitor.log_agent_action = MagicMock()
        mock_evaluator.evaluate_agent_decision = MagicMock()
        mock_evaluator.evaluate_final_resume_quality = MagicMock()
        
        return {
            'judgment': mock_judgment,
            'monitor': mock_monitor,
            'evaluator': mock_evaluator
        }

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
    async def resume_agent(self, mock_openai_client, mock_judgment_components):
        """Create IterativeResumeAgent with mocked dependencies."""
        with patch('app.core.resume_agent.AsyncOpenAI', return_value=mock_openai_client):
            with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
                # Mock the judgment wrapper to return the mock client directly
                with patch('judgeval.common.tracer.wrap', return_value=mock_openai_client):
                    # Mock judgment imports at the module level (as globals)
                    with patch('app.core.resume_agent.judgment', mock_judgment_components['judgment']):
                        with patch('app.core.resume_agent.evaluator', mock_judgment_components['evaluator']):
                            with patch('app.core.resume_agent.monitor', mock_judgment_components['monitor']):
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
        assert len(resume_agent.analysis_order) == 4  # Skills, Education, Experience, Projects

    @pytest.mark.asyncio
    async def test_start_analysis_success(self, resume_agent, sample_resume_text, sample_job_description):
        """Test successful analysis start with human-in-the-loop workflow."""
        with patch('app.utils.pdf_parser.split_resume_sections') as mock_split:
            mock_split.return_value = {
                'experience': {'content': 'Senior Software Engineer | TechCorp | 2020-2023'},
                'skills': {'content': 'JavaScript, Python, React, Node.js'},
                'education': {'content': 'B.S. Computer Science | University of Technology | 2018'},
                'projects': {'content': 'E-commerce Platform | 2022'}
            }
            
            # Mock the job analysis method to avoid JSON parsing issues
            with patch.object(resume_agent, '_analyze_job_description_comprehensive') as mock_job_analysis:
                mock_job_analysis.return_value = JobAnalysis(
                    keywords=["python", "react", "javascript"],
                    requirements=["5+ years experience"],
                    experience_level="senior",
                    key_technologies=["Python", "React", "JavaScript"],
                    priorities=["technical leadership"],
                    soft_skills=["communication"],
                    hard_skills=["programming"],
                    industry="technology",
                    company_size="medium",
                    role_type="full_stack"
                )
                
                # Mock the _iterative_section_improvement to avoid complex LLM calls
                with patch.object(resume_agent, '_iterative_section_improvement') as mock_improvement:
                    mock_analysis = SectionAnalysis(
                        section_type=SectionType.SKILLS,
                        original_content="JavaScript, Python, React",
                        best_content="• JavaScript, Python, React, Node.js\n• AWS, Docker, Kubernetes",
                        iterations=[],
                        final_score=85,
                        improvement_journey="Enhanced formatting and added missing technologies",
                        needs_clarification=False,
                        clarification_request=None
                    )
                    mock_improvement.return_value = mock_analysis
                    
                    result = await resume_agent.start_analysis(sample_resume_text, sample_job_description)
                    
                    assert result["success"] is True
                    assert "session_id" in result
                    assert "sections" in result
                    assert "job_analysis" in result
                    assert "section_analyses" in result
                    assert len(result["sections"]) >= 4  # May include contact_info and other sections

    @pytest.mark.asyncio
    async def test_start_analysis_with_clarifications(self, resume_agent, sample_resume_text, sample_job_description):
        """Test analysis that triggers clarification requests."""
        with patch('app.utils.pdf_parser.split_resume_sections') as mock_split:
            mock_split.return_value = {
                'skills': {'content': 'Basic programming skills'}
            }
            
            # Mock clarification scenario
            with patch.object(resume_agent, '_iterative_section_improvement') as mock_improvement:
                clarification_request = ClarificationRequest(
                    section_type=SectionType.SKILLS,
                    question="What specific programming languages and frameworks do you have experience with?",
                    context="Your skills section mentions 'basic programming skills' but lacks specific technologies",
                    original_content="Basic programming skills",
                    reason="Insufficient detail for job matching",
                    timestamp=datetime.now()
                )
                
                mock_analysis = SectionAnalysis(
                    section_type=SectionType.SKILLS,
                    original_content="Basic programming skills",
                    best_content="Basic programming skills",  # Safe formatting only
                    iterations=[],
                    final_score=60,
                    improvement_journey="Safe formatting applied. More details needed.",
                    needs_clarification=True,
                    clarification_request=clarification_request
                )
                mock_improvement.return_value = mock_analysis
                
                result = await resume_agent.start_analysis(sample_resume_text, sample_job_description)
                
                assert result["success"] is True
                assert result["needs_clarification"] is True
                assert "pending_clarifications" in result
                assert "skills" in result["pending_clarifications"]
                assert len(result["sections_needing_clarification"]) == 1

    @pytest.mark.asyncio
    async def test_provide_clarification_success(self, resume_agent, sample_resume_text, sample_job_description):
        """Test providing clarification for section analysis."""
        # First start an analysis that needs clarification
        with patch('app.utils.pdf_parser.split_resume_sections') as mock_split:
            mock_split.return_value = {'skills': {'content': 'Basic skills'}}
            
            # Mock initial analysis with clarification needed
            with patch.object(resume_agent, '_iterative_section_improvement') as mock_improvement:
                clarification_request = ClarificationRequest(
                    section_type=SectionType.SKILLS,
                    question="What technologies do you know?",
                    context="Skills section needs more detail",
                    original_content="Basic skills",
                    reason="Insufficient detail",
                    timestamp=datetime.now()
                )
                
                initial_analysis = SectionAnalysis(
                    section_type=SectionType.SKILLS,
                    original_content="Basic skills",
                    best_content="Basic skills",
                    iterations=[],
                    final_score=60,
                    improvement_journey="Needs clarification",
                    needs_clarification=True,
                    clarification_request=clarification_request
                )
                mock_improvement.return_value = initial_analysis
                
                start_result = await resume_agent.start_analysis(sample_resume_text, sample_job_description)
                session_id = start_result["session_id"]
                
                # Mock clarification processing
                with patch.object(resume_agent, '_iterative_section_improvement_with_clarification') as mock_clarification:
                    enhanced_analysis = SectionAnalysis(
                        section_type=SectionType.SKILLS,
                        original_content="Basic skills",
                        best_content="• Python (5 years), JavaScript (3 years)\n• React, Node.js, Django",
                        iterations=[],
                        final_score=90,
                        improvement_journey="Enhanced with user-provided details",
                        needs_clarification=False,
                        clarification_request=None
                    )
                    mock_clarification.return_value = enhanced_analysis
                    
                    # Provide clarification
                    clarification = "I have 5 years of Python experience and 3 years of JavaScript/React"
                    result = await resume_agent.provide_clarification(
                        session_id, 
                        "skills", 
                        clarification
                    )
                    
                    assert result["success"] is True
                    assert "analysis" in result
                    assert result["analysis"]["score"] == 90
                    assert result["clarifications_completed"] is True

    @pytest.mark.asyncio
    async def test_accept_section_changes(self, resume_agent, sample_resume_text, sample_job_description):
        """Test accepting and rejecting section changes."""
        # Setup a completed analysis session
        with patch('app.utils.pdf_parser.split_resume_sections') as mock_split:
            mock_split.return_value = {
                'skills': {'content': 'JavaScript, Python'},
                'experience': {'content': 'Software Engineer at TechCorp'}
            }
            
            with patch.object(resume_agent, '_iterative_section_improvement') as mock_improvement:
                mock_analysis = SectionAnalysis(
                    section_type=SectionType.SKILLS,
                    original_content="JavaScript, Python",
                    best_content="• JavaScript (Expert)\n• Python (Advanced)",
                    iterations=[],
                    final_score=85,
                    improvement_journey="Enhanced with proficiency levels",
                    needs_clarification=False,
                    clarification_request=None
                )
                mock_improvement.return_value = mock_analysis
                
                start_result = await resume_agent.start_analysis(sample_resume_text, sample_job_description)
                session_id = start_result["session_id"]
                
                # Test accepting changes
                accept_result = await resume_agent.accept_section_changes(session_id, "skills", True)
                assert accept_result["success"] is True
                assert "accepted" in accept_result["message"]
                
                # Test rejecting changes
                reject_result = await resume_agent.accept_section_changes(session_id, "experience", False)
                assert reject_result["success"] is True
                assert "rejected" in reject_result["message"]

    @pytest.mark.asyncio
    async def test_generate_final_resume(self, resume_agent, sample_resume_text, sample_job_description):
        """Test final resume generation with user decisions."""
        # Setup a session with completed analyses and user decisions
        session_id = "test-session-123"
        
        # Create mock section analyses
        skills_analysis = SectionAnalysis(
            section_type=SectionType.SKILLS,
            original_content="JavaScript, Python",
            best_content="• JavaScript (Expert)\n• Python (Advanced)\n• React, Node.js",
            iterations=[],
            final_score=88,
            improvement_journey="Enhanced with additional technologies",
            needs_clarification=False,
            clarification_request=None
        )
        
        experience_analysis = SectionAnalysis(
            section_type=SectionType.EXPERIENCE,
            original_content="Software Engineer at TechCorp",
            best_content="Senior Software Engineer | TechCorp | 2020-2023\n• Led development team\n• Implemented scalable solutions",
            iterations=[],
            final_score=92,
            improvement_journey="Enhanced with leadership details",
            needs_clarification=False,
            clarification_request=None
        )
        
        # Setup session data
        resume_agent.sessions[session_id] = {
            "resume_text": sample_resume_text,
            "job_description": sample_job_description,
            "section_analyses": {
                "skills": skills_analysis,
                "experience": experience_analysis
            },
            "accepted_changes": {
                "skills": True,  # User accepted skills changes
                "experience": False  # User rejected experience changes
            }
        }
        
        # Mock monitor.log_session_completion to return metrics
        with patch('app.core.resume_agent.monitor') as mock_monitor:
            mock_monitor.log_session_completion.return_value = {"sections_analyzed": 2}
            
            result = await resume_agent.generate_final_resume(session_id)
            
            assert result["success"] is True
            assert "final_resume" in result
            assert "SKILLS" in result["final_resume"]  # Should contain accepted improved skills
            assert "EXPERIENCE" in result["final_resume"]  # Should contain original experience (rejected)
            assert len(result["sections"]) == 2
            
            # Verify session completion was logged
            mock_monitor.log_session_completion.assert_called_once()

    @pytest.mark.asyncio
    async def test_dual_storage_system(self, resume_agent, sample_resume_text, sample_job_description):
        """Test that sections are stored in both session['section_analyses'] and completed_analyses."""
        with patch('app.utils.pdf_parser.split_resume_sections') as mock_split:
            mock_split.return_value = {
                'skills': {'content': 'JavaScript, Python'},
            }
            
            with patch.object(resume_agent, '_iterative_section_improvement') as mock_improvement:
                mock_analysis = SectionAnalysis(
                    section_type=SectionType.SKILLS,
                    original_content="JavaScript, Python",
                    best_content="• JavaScript\n• Python\n• React",
                    iterations=[],
                    final_score=85,
                    improvement_journey="Added React framework",
                    needs_clarification=False,
                    clarification_request=None
                )
                mock_improvement.return_value = mock_analysis
                
                result = await resume_agent.start_analysis(sample_resume_text, sample_job_description)
                session_id = result["session_id"]
                
                # Verify dual storage
                session = resume_agent.sessions[session_id]
                assert "skills" in session["section_analyses"]  # Stored for final resume generation
                assert "skills" in result["section_analyses"]  # Returned in API response
                
                # Both should have the same analysis
                stored_analysis = session["section_analyses"]["skills"]
                returned_analysis = result["section_analyses"]["skills"]
                
                assert stored_analysis.section_type == SectionType.SKILLS
                assert returned_analysis["section_type"] == "skills"
                assert stored_analysis.final_score == returned_analysis["score"]

    @pytest.mark.asyncio
    async def test_judgment_integration(self, resume_agent, mock_judgment_components):
        """Test judgment framework integration throughout the workflow."""
        
        # Test that judgment components are properly integrated
        assert hasattr(resume_agent, 'client')
        
        # Verify that the judgment framework is available and integrated
        # The presence of trace warnings in the output confirms integration
        
        # Test that the basic monitoring and evaluation methods exist
        from app.core.judgment_config import get_judgment_monitor, get_judgment_evaluator
        monitor = get_judgment_monitor()
        evaluator = get_judgment_evaluator()
        
        assert monitor is not None
        assert evaluator is not None
        assert hasattr(monitor, 'log_agent_action')
        assert hasattr(evaluator, 'evaluate_agent_decision')
        
        # Test a simple operation that should trigger judgment logging
        # The monitor calls happen inside the main analysis flow
        with patch.object(resume_agent, '_score_content_quality', return_value=85):
            # Mock complex operations to avoid OpenAI calls
            job_analysis = JobAnalysis(
                keywords=["python", "react"],
                requirements=["5+ years experience"],
                experience_level="senior",
                key_technologies=["Python", "React"],
                priorities=["technical leadership"],
                soft_skills=["communication"],
                hard_skills=["programming"],
                industry="technology",
                company_size="medium",
                role_type="full_stack"
            )
            
            # Test that the judgment framework doesn't break the flow
            # Real monitoring calls happen in the full analysis pipeline
            try:
                monitor.log_agent_action("test_action", {
                    "section_type": "skills",
                    "test": True
                })
                # If we get here, judgment integration is working
                judgment_working = True
            except Exception as e:
                judgment_working = False
                
            assert judgment_working, "Judgment framework integration failed"
            
            # Test evaluator integration
            try:
                evaluator.evaluate_agent_decision(
                    "Test decision context",
                    "Test decision made", 
                    "Test reasoning",
                    0.85
                )
                evaluator_working = True
            except Exception as e:
                evaluator_working = False
                
            assert evaluator_working, "Judgment evaluator integration failed"

    @pytest.mark.asyncio
    async def test_error_handling_and_fallbacks(self, resume_agent, sample_resume_text, sample_job_description):
        """Test error handling and fallback mechanisms."""
        with patch('app.utils.pdf_parser.split_resume_sections') as mock_split:
            mock_split.return_value = {
                'skills': {'content': 'JavaScript, Python'}
            }
            
            # Test OpenAI API failure handling
            with patch.object(resume_agent, '_iterative_section_improvement') as mock_improvement:
                # Simulate API failure
                mock_improvement.side_effect = Exception("OpenAI API error")
                
                # Should still return a result with error handling
                result = await resume_agent.start_analysis(sample_resume_text, sample_job_description)
                
                # The error should be handled gracefully
                assert result["success"] is True  # Analysis continues with fallbacks
                assert "section_analyses" in result

    @pytest.mark.asyncio
    async def test_multiple_clarifications_workflow(self, resume_agent, sample_resume_text, sample_job_description):
        """Test handling multiple clarifications in one session."""
        with patch('app.utils.pdf_parser.split_resume_sections') as mock_split:
            mock_split.return_value = {
                'skills': {'content': 'Programming'},
                'experience': {'content': 'Software work'}
            }
            
            # Mock both sections needing clarification
            with patch.object(resume_agent, '_iterative_section_improvement') as mock_improvement:
                def mock_analysis_with_clarification(content, section_type, *args):
                    return SectionAnalysis(
                        section_type=section_type,
                        original_content=content,
                        best_content=content,
                        iterations=[],
                        final_score=60,
                        improvement_journey="Needs more details",
                        needs_clarification=True,
                        clarification_request=ClarificationRequest(
                            section_type=section_type,
                            question=f"Please provide more details about your {section_type.value}",
                            context=f"The {section_type.value} section needs enhancement",
                            original_content=content,
                            reason="Insufficient detail",
                            timestamp=datetime.now()
                        )
                    )
                
                mock_improvement.side_effect = mock_analysis_with_clarification
                
                result = await resume_agent.start_analysis(sample_resume_text, sample_job_description)
                
                assert result["success"] is True
                assert result["needs_clarification"] is True
                assert len(result["sections_needing_clarification"]) == 2
                assert "skills" in result["pending_clarifications"]
                assert "experience" in result["pending_clarifications"]

    @pytest.mark.asyncio
    async def test_session_status_tracking(self, resume_agent):
        """Test session status and progress tracking."""
        # Create a session
        session_id = "test-session-456"
        resume_agent.sessions[session_id] = {
            "created_at": datetime.now().isoformat(),
            "section_analyses": {"skills": "mock_analysis"},
            "pending_clarifications": {}
        }
        
        status = resume_agent.get_session_status(session_id)
        
        assert status["success"] is True
        assert status["session_id"] == session_id
        assert status["sections_analyzed"] == 1
        assert status["pending_clarifications"] == 0

    @pytest.mark.asyncio
    async def test_invalid_session_handling(self, resume_agent):
        """Test handling of invalid session IDs."""
        
        # Test analyze_section with invalid session
        result = await resume_agent.analyze_section("invalid-session", "skills")
        assert result["success"] is False
        assert "not found" in result["error"]
        
        # Test provide_clarification with invalid session
        result = await resume_agent.provide_clarification("invalid-session", "skills", "test")
        assert result["success"] is False
        assert "not found" in result["error"]
        
        # Test generate_final_resume with invalid session
        result = await resume_agent.generate_final_resume("invalid-session")
        assert result["success"] is False
        assert "not found" in result["error"]


@pytest.mark.asyncio
async def test_resume_agent_integration():
    """Integration test for complete resume analysis workflow."""
    
    # This test verifies the entire workflow from start to finish
    sample_resume = """
    John Smith
    Full Stack Developer
    
    SKILLS
    JavaScript, Python, HTML, CSS
    
    EXPERIENCE
    Software Developer | ABC Corp | 2021-2023
    - Built web applications
    
    EDUCATION
    Computer Science Degree | XYZ University | 2021
    """
    
    sample_job = """
    Senior Full Stack Developer position requiring:
    - JavaScript, Python, React expertise
    - 3+ years experience
    - Team collaboration skills
    """
    
    with patch('app.core.resume_agent.AsyncOpenAI'):
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            with patch('app.utils.pdf_parser.split_resume_sections') as mock_split:
                mock_split.return_value = {
                    'skills': {'content': 'JavaScript, Python, HTML, CSS'},
                    'experience': {'content': 'Software Developer | ABC Corp | 2021-2023'},
                    'education': {'content': 'Computer Science Degree | XYZ University | 2021'}
                }
                
                agent = IterativeResumeAgent()
                
                # Mock the improvement method to avoid actual API calls
                with patch.object(agent, '_iterative_section_improvement') as mock_improvement:
                    mock_improvement.return_value = SectionAnalysis(
                        section_type=SectionType.SKILLS,
                        original_content="JavaScript, Python, HTML, CSS",
                        best_content="• JavaScript (Advanced)\n• Python (Intermediate)\n• HTML5, CSS3",
                        iterations=[],
                        final_score=85,
                        improvement_journey="Enhanced with proficiency levels",
                        needs_clarification=False,
                        clarification_request=None
                    )
                    
                    # Test complete workflow
                    start_result = await agent.start_analysis(sample_resume, sample_job)
                    assert start_result["success"] is True
                    
                    session_id = start_result["session_id"]
                    
                    # Accept some changes
                    await agent.accept_section_changes(session_id, "skills", True)
                    
                    # Generate final resume
                    final_result = await agent.generate_final_resume(session_id)
                    assert final_result["success"] is True
                    assert "final_resume" in final_result 