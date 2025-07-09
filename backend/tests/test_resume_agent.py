"""Tests for the ResumeAgent class."""
import pytest
from app.core.resume_agent import ResumeAgent

@pytest.fixture
def resume_agent():
    """Create a ResumeAgent instance for testing."""
    return ResumeAgent()

def test_resume_agent_initialization(resume_agent):
    """Test that ResumeAgent initializes correctly."""
    assert resume_agent is not None
    assert resume_agent.graph is not None

@pytest.mark.asyncio
async def test_analyze_basic_resume(resume_agent):
    """Test basic resume analysis."""
    resume_text = """
    John Doe
    Software Engineer
    
    Experience:
    - Developed web applications using React and Node.js
    - Implemented CI/CD pipelines
    """
    
    result = await resume_agent.analyze(resume_text)
    assert result is not None
    assert "sections" in result 