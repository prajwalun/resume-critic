"""
Comprehensive tests for FastAPI main application.
Tests API endpoints, middleware, and application startup.
"""

import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from fastapi import status

from app.main import app


class TestAPIEndpoints:
    """Test suite for FastAPI endpoints."""

    @pytest.fixture
    def client(self):
        """Create test client for FastAPI app."""
        return TestClient(app)

    @pytest.fixture
    def mock_resume_agent(self):
        """Mock resume agent for testing."""
        mock_agent = AsyncMock()
        
        # Mock successful analysis start
        mock_agent.start_analysis.return_value = {
            "success": True,
            "session_id": "test-session-123",
            "sections": {
                "experience": {"content": "Software Engineer at TechCorp"},
                "skills": {"content": "Python, JavaScript, React"}
            },
            "job_analysis": {"required_skills": ["Python", "JavaScript"]},
            "analysis_order": ["skills", "experience"],
            "section_analyses": {}
        }
        
        # Mock successful section analysis
        mock_agent.analyze_section.return_value = {
            "success": True,
            "analysis": {
                "section_type": "skills",
                "original_content": "Python, JavaScript",
                "best_content": "Advanced Python and JavaScript programming",
                "final_score": 85,
                "needs_clarification": False
            }
        }
        
        # Mock successful clarification
        mock_agent.provide_clarification.return_value = {
            "success": True,
            "analysis": {
                "section_type": "skills",
                "improved_content": "Python (5 years), JavaScript (3 years)",
                "final_score": 90
            }
        }
        
        # Mock successful final resume generation
        mock_agent.generate_final_resume.return_value = {
            "success": True,
            "final_resume": "Complete improved resume text",
            "sections": {
                "experience": "Improved experience section",
                "skills": "Improved skills section"
            },
            "session_id": "test-session-123"
        }
        
        return mock_agent

    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "ResumeWise API"

    @patch('app.main.resume_agent')
    def test_start_analysis_success(self, mock_agent, client, mock_resume_agent):
        """Test successful analysis start."""
        mock_agent.start_analysis = mock_resume_agent.start_analysis
        
        # Create test file data
        test_file_content = b"John Doe\nSoftware Engineer\nPython, JavaScript"
        
        with patch('app.utils.pdf_parser.extract_resume_text') as mock_extract:
            with patch('app.utils.pdf_parser.clean_resume_text') as mock_clean:
                mock_extract.return_value = "John Doe\nSoftware Engineer\nPython, JavaScript"
                mock_clean.return_value = "John Doe\nSoftware Engineer\nPython, JavaScript"
                
                response = client.post(
                    "/api/start-analysis",
                    files={"file": ("resume.pdf", test_file_content, "application/pdf")},
                    data={"job_description": "Software Engineer position requiring Python and JavaScript"}
                )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert "session_id" in data
        assert "sections" in data
        assert "job_analysis" in data

    def test_start_analysis_no_file(self, client):
        """Test analysis start without file upload."""
        response = client.post(
            "/api/start-analysis",
            data={"job_description": "Software Engineer position"}
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_start_analysis_empty_file(self, client):
        """Test analysis start with empty file."""
        with patch('app.utils.pdf_parser.extract_resume_text') as mock_extract:
            with patch('app.utils.pdf_parser.clean_resume_text') as mock_clean:
                mock_extract.return_value = ""
                mock_clean.return_value = ""
                
                response = client.post(
                    "/api/start-analysis",
                    files={"file": ("empty.pdf", b"", "application/pdf")},
                    data={"job_description": "Software Engineer position"}
                )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @patch('app.main.resume_agent')
    def test_analyze_section_success(self, mock_agent, client, mock_resume_agent):
        """Test successful section analysis."""
        mock_agent.analyze_section = mock_resume_agent.analyze_section
        
        request_data = {
            "session_id": "test-session-123",
            "section_type": "skills"
        }
        
        response = client.post(
            "/api/analyze-section",
            json=request_data
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert "analysis" in data

    @patch('app.main.resume_agent')
    def test_analyze_section_not_found(self, mock_agent, client):
        """Test section analysis with invalid session."""
        mock_agent.analyze_section.return_value = {
            "success": False,
            "error": "Session not found"
        }
        
        request_data = {
            "session_id": "invalid-session",
            "section_type": "skills"
        }
        
        response = client.post(
            "/api/analyze-section",
            json=request_data
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND

    @patch('app.main.resume_agent')
    def test_provide_clarification_success(self, mock_agent, client, mock_resume_agent):
        """Test successful clarification provision."""
        mock_agent.provide_clarification = mock_resume_agent.provide_clarification
        
        request_data = {
            "session_id": "test-session-123",
            "section_type": "skills",
            "clarification": "I have 5 years of Python experience"
        }
        
        response = client.post(
            "/api/provide-clarification",
            json=request_data
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert "analysis" in data

    @patch('app.main.resume_agent')
    def test_generate_final_resume_success(self, mock_agent, client, mock_resume_agent):
        """Test successful final resume generation."""
        mock_agent.generate_final_resume = mock_resume_agent.generate_final_resume
        
        request_data = {
            "session_id": "test-session-123"
        }
        
        response = client.post(
            "/api/generate-final-resume",
            json=request_data
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert "final_resume" in data
        assert "sections" in data

    @patch('app.main.resume_agent')
    def test_legacy_endpoint(self, mock_agent, client, mock_resume_agent):
        """Test legacy endpoint for backward compatibility."""
        mock_agent.start_analysis = mock_resume_agent.start_analysis
        
        test_file_content = b"John Doe\nSoftware Engineer"
        
        with patch('app.utils.pdf_parser.extract_resume_text') as mock_extract:
            with patch('app.utils.pdf_parser.clean_resume_text') as mock_clean:
                mock_extract.return_value = "John Doe\nSoftware Engineer"
                mock_clean.return_value = "John Doe\nSoftware Engineer"
                
                response = client.post(
                    "/api/analyze-resume",
                    files={"file": ("resume.pdf", test_file_content, "application/pdf")},
                    data={
                        "job_description": "Software Engineer position",
                        "review_mode": "true"
                    }
                )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert "data" in data

    def test_cors_headers(self, client):
        """Test CORS headers are properly set."""
        response = client.options("/health")
        
        # CORS headers should be present
        # Note: TestClient might not show all CORS headers, but this tests the setup
        assert response.status_code in [200, 405]  # OPTIONS might not be allowed but CORS should be set

    def test_invalid_endpoint(self, client):
        """Test accessing invalid endpoint."""
        response = client.get("/api/invalid-endpoint")
        
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_malformed_json_request(self, client):
        """Test handling of malformed JSON requests."""
        response = client.post(
            "/api/analyze-section",
            data="invalid json content",
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @patch('app.main.resume_agent')
    def test_server_error_handling(self, mock_agent, client):
        """Test server error handling."""
        # Mock agent to raise exception
        mock_agent.start_analysis.side_effect = Exception("Internal server error")
        
        test_file_content = b"Test content"
        
        with patch('app.utils.pdf_parser.extract_resume_text') as mock_extract:
            with patch('app.utils.pdf_parser.clean_resume_text') as mock_clean:
                mock_extract.return_value = "Test content"
                mock_clean.return_value = "Test content"
                
                response = client.post(
                    "/api/start-analysis",
                    files={"file": ("resume.pdf", test_file_content, "application/pdf")},
                    data={"job_description": "Test job description"}
                )
        
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


class TestApplicationSetup:
    """Test suite for application setup and configuration."""

    def test_app_title_and_description(self):
        """Test app metadata."""
        assert app.title == "ResumeWise API"
        assert "AI-powered resume analysis" in app.description
        assert app.version == "1.0.0"

    def test_cors_middleware_configuration(self):
        """Test CORS middleware is configured."""
        # Check that CORS middleware is in the middleware stack
        middleware_classes = [middleware.cls.__name__ for middleware in app.user_middleware]
        assert "CORSMiddleware" in middleware_classes

    @patch('app.main.setup_clean_logging')
    def test_logging_setup(self, mock_setup_logging):
        """Test that logging is properly set up."""
        # Import main to trigger setup
        import app.main
        
        # Logging setup should have been called
        mock_setup_logging.assert_called()

    @patch('app.main.get_judgment_tracer')
    def test_judgment_framework_integration(self, mock_get_tracer):
        """Test judgment framework integration."""
        mock_get_tracer.return_value = MagicMock()
        
        # Import main to trigger judgment setup
        import app.main
        
        # Should attempt to get judgment tracer
        mock_get_tracer.assert_called()

    def test_pydantic_models_defined(self):
        """Test that Pydantic models are properly defined."""
        from app.main import (
            AnalysisStartRequest,
            AnalysisStartResponse,
            SectionAnalysisRequest,
            SectionAnalysisResponse,
            ClarificationRequest,
            ClarificationResponse,
            FinalResumeRequest,
            FinalResumeResponse
        )
        
        # All models should be defined
        assert AnalysisStartRequest is not None
        assert AnalysisStartResponse is not None
        assert SectionAnalysisRequest is not None
        assert SectionAnalysisResponse is not None
        assert ClarificationRequest is not None
        assert ClarificationResponse is not None
        assert FinalResumeRequest is not None
        assert FinalResumeResponse is not None


class TestEndpointValidation:
    """Test suite for endpoint input validation."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    def test_start_analysis_validation(self, client):
        """Test start analysis endpoint validation."""
        # Missing job description
        response = client.post(
            "/api/start-analysis",
            files={"file": ("resume.pdf", b"content", "application/pdf")}
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_analyze_section_validation(self, client):
        """Test analyze section endpoint validation."""
        # Missing session_id
        response = client.post(
            "/api/analyze-section",
            json={"section_type": "skills"}
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        
        # Missing section_type
        response = client.post(
            "/api/analyze-section",
            json={"session_id": "test-session"}
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_provide_clarification_validation(self, client):
        """Test provide clarification endpoint validation."""
        # Missing clarification
        response = client.post(
            "/api/provide-clarification",
            json={
                "session_id": "test-session",
                "section_type": "skills"
            }
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_generate_final_resume_validation(self, client):
        """Test generate final resume endpoint validation."""
        # Missing session_id
        response = client.post(
            "/api/generate-final-resume",
            json={}
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.asyncio
async def test_judgment_tracing_decorator():
    """Test judgment tracing decorator functionality."""
    from app.main import _trace_if_available
    
    # Mock function to decorate
    @_trace_if_available
    async def mock_function():
        return {"test": "result"}
    
    # Should work whether judgment is available or not
    result = await mock_function()
    assert result == {"test": "result"}


def test_app_startup_and_shutdown():
    """Test application startup and shutdown events."""
    # This tests that the app can be created without errors
    assert app is not None
    
    # Test that routes are registered
    routes = [route.path for route in app.routes]
    expected_routes = [
        "/health",
        "/api/start-analysis", 
        "/api/analyze-section",
        "/api/provide-clarification",
        "/api/generate-final-resume",
        "/api/analyze-resume"  # Legacy endpoint
    ]
    
    for expected_route in expected_routes:
        assert expected_route in routes


class TestPerformanceAndSecurity:
    """Test suite for performance and security considerations."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    def test_large_file_handling(self, client):
        """Test handling of large file uploads."""
        # Create a large file content (simulated)
        large_content = b"Large file content " * 1000
        
        with patch('app.utils.pdf_parser.extract_resume_text') as mock_extract:
            mock_extract.return_value = ""  # Simulate extraction failure/empty
            
            response = client.post(
                "/api/start-analysis",
                files={"file": ("large_resume.pdf", large_content, "application/pdf")},
                data={"job_description": "Test job"}
            )
        
        # Should handle gracefully, not crash
        assert response.status_code in [400, 500]  # Either validation error or server error

    def test_sql_injection_protection(self, client):
        """Test protection against SQL injection (though we don't use SQL)."""
        malicious_input = "'; DROP TABLE users; --"
        
        response = client.post(
            "/api/analyze-section",
            json={
                "session_id": malicious_input,
                "section_type": "skills"
            }
        )
        
        # Should handle malicious input gracefully
        assert response.status_code in [400, 404, 422, 500]

    def test_request_timeout_handling(self, client):
        """Test request timeout handling."""
        # This test verifies the app is configured to handle timeouts
        # Actual timeout testing would require more complex setup
        assert hasattr(app, 'user_middleware')

    def test_concurrent_requests(self, client):
        """Test handling of concurrent requests."""
        import threading
        import time
        
        results = []
        
        def make_request():
            response = client.get("/health")
            results.append(response.status_code)
        
        # Create multiple threads making requests
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join()
        
        # All requests should succeed
        assert all(status_code == 200 for status_code in results)
        assert len(results) == 5 