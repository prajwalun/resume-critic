"""
Comprehensive tests for PDF Parser utility.
Tests PDF text extraction, cleaning, and section splitting functionality.
"""

import pytest
import io
from unittest.mock import patch, MagicMock, mock_open

from app.utils.pdf_parser import (
    extract_resume_text,
    clean_resume_text, 
    split_resume_sections
)


class TestPDFTextExtraction:
    """Test suite for PDF text extraction functionality."""

    @patch('app.utils.pdf_parser.pdfplumber.open')
    def test_extract_resume_text_pdf_success(self, mock_pdf_open):
        """Test successful PDF text extraction."""
        # Mock PDF structure
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "John Doe\nSoftware Engineer\nExperience: Python, JavaScript"
        
        mock_pdf = MagicMock()
        mock_pdf.pages = [mock_page]
        mock_pdf.__enter__ = MagicMock(return_value=mock_pdf)
        mock_pdf.__exit__ = MagicMock(return_value=None)
        
        mock_pdf_open.return_value = mock_pdf
        
        pdf_content = b"fake pdf content"
        filename = "resume.pdf"
        
        result = extract_resume_text(pdf_content, filename)
        
        assert "John Doe" in result
        assert "Software Engineer" in result
        assert "Experience: Python, JavaScript" in result
        mock_pdf_open.assert_called_once()

    @patch('app.utils.pdf_parser.pdfplumber.open')
    def test_extract_resume_text_pdf_multiple_pages(self, mock_pdf_open):
        """Test PDF text extraction with multiple pages."""
        # Mock multiple pages
        mock_page1 = MagicMock()
        mock_page1.extract_text.return_value = "John Doe\nSoftware Engineer"
        
        mock_page2 = MagicMock()
        mock_page2.extract_text.return_value = "Experience:\n- Python development\n- JavaScript programming"
        
        mock_pdf = MagicMock()
        mock_pdf.pages = [mock_page1, mock_page2]
        mock_pdf.__enter__ = MagicMock(return_value=mock_pdf)
        mock_pdf.__exit__ = MagicMock(return_value=None)
        
        mock_pdf_open.return_value = mock_pdf
        
        pdf_content = b"fake multi-page pdf content"
        filename = "multi_page_resume.pdf"
        
        result = extract_resume_text(pdf_content, filename)
        
        assert "John Doe" in result
        assert "Software Engineer" in result
        assert "Python development" in result
        assert "JavaScript programming" in result

    @patch('app.utils.pdf_parser.pdfplumber.open')
    def test_extract_resume_text_pdf_empty_page(self, mock_pdf_open):
        """Test handling of empty PDF pages."""
        mock_page1 = MagicMock()
        mock_page1.extract_text.return_value = "John Doe"
        
        mock_page2 = MagicMock()
        mock_page2.extract_text.return_value = None  # Empty page
        
        mock_page3 = MagicMock()
        mock_page3.extract_text.return_value = "Software Engineer"
        
        mock_pdf = MagicMock()
        mock_pdf.pages = [mock_page1, mock_page2, mock_page3]
        mock_pdf.__enter__ = MagicMock(return_value=mock_pdf)
        mock_pdf.__exit__ = MagicMock(return_value=None)
        
        mock_pdf_open.return_value = mock_pdf
        
        result = extract_resume_text(b"pdf content", "resume.pdf")
        
        assert "John Doe" in result
        assert "Software Engineer" in result

    def test_extract_resume_text_txt_file(self):
        """Test text extraction from .txt file."""
        text_content = "John Doe\nSoftware Engineer\nPython, JavaScript"
        content_bytes = text_content.encode('utf-8')
        
        result = extract_resume_text(content_bytes, "resume.txt")
        
        assert result == text_content

    def test_extract_resume_text_docx_file(self):
        """Test handling of unsupported .docx file."""
        docx_content = b"fake docx content"
        
        result = extract_resume_text(docx_content, "resume.docx")
        
        assert result == ""

    def test_extract_resume_text_unknown_format(self):
        """Test handling of unknown file format."""
        unknown_content = b"unknown file content"
        
        result = extract_resume_text(unknown_content, "resume.xyz")
        
        assert result == ""

    @patch('app.utils.pdf_parser.pdfplumber.open')
    def test_extract_resume_text_pdf_exception(self, mock_pdf_open):
        """Test handling of PDF parsing exceptions."""
        mock_pdf_open.side_effect = Exception("PDF parsing error")
        
        pdf_content = b"corrupted pdf content"
        
        result = extract_resume_text(pdf_content, "corrupted.pdf")
        
        assert result == ""

    def test_extract_resume_text_txt_encoding_error(self):
        """Test handling of text encoding errors."""
        # Create invalid UTF-8 content
        invalid_content = b'\xff\xfe\x00\x00invalid utf-8'
        
        result = extract_resume_text(invalid_content, "resume.txt")
        
        assert result == ""

    def test_extract_resume_text_empty_content(self):
        """Test handling of empty file content."""
        result = extract_resume_text(b"", "empty.pdf")
        assert result == ""

    def test_extract_resume_text_none_filename(self):
        """Test handling of None filename."""
        result = extract_resume_text(b"content", None)
        assert result == ""

    def test_extract_resume_text_none_content(self):
        """Test handling of None content."""
        result = extract_resume_text(None, "resume.pdf")
        assert result == ""


class TestTextCleaning:
    """Test suite for text cleaning functionality."""

    def test_clean_resume_text_basic(self):
        """Test basic text cleaning."""
        raw_text = "  John Doe  \n\n  Software Engineer  \n\n\n  Python, JavaScript  "
        
        result = clean_resume_text(raw_text)
        
        assert "John Doe" in result
        assert "Software Engineer" in result
        assert "Python, JavaScript" in result
        # Should remove extra whitespace
        assert "  John Doe  " not in result

    def test_clean_resume_text_excessive_newlines(self):
        """Test cleaning excessive newlines."""
        raw_text = "John Doe\n\n\n\n\nSoftware Engineer\n\n\nExperience:\n\n\nPython"
        
        result = clean_resume_text(raw_text)
        
        # Should not have more than 2 consecutive newlines
        assert "\n\n\n" not in result
        assert "John Doe" in result
        assert "Software Engineer" in result

    def test_clean_resume_text_weird_characters(self):
        """Test cleaning weird characters and artifacts."""
        raw_text = "John Doe\x00\x01Software Engineer\t\t\tPython"
        
        result = clean_resume_text(raw_text)
        
        assert "\x00" not in result
        assert "\x01" not in result
        assert "John Doe" in result
        assert "Software Engineer" in result
        assert "Python" in result

    def test_clean_resume_text_unicode_normalization(self):
        """Test Unicode normalization in text cleaning."""
        raw_text = "Résumé for José with café experience"
        
        result = clean_resume_text(raw_text)
        
        assert "Résumé" in result
        assert "José" in result
        assert "café" in result

    def test_clean_resume_text_empty_input(self):
        """Test cleaning empty input."""
        result = clean_resume_text("")
        assert result == ""

    def test_clean_resume_text_none_input(self):
        """Test cleaning None input."""
        result = clean_resume_text(None)
        assert result == ""

    def test_clean_resume_text_whitespace_only(self):
        """Test cleaning whitespace-only input."""
        result = clean_resume_text("   \n\n\t\t   ")
        assert result == ""

    def test_clean_resume_text_preserve_structure(self):
        """Test that cleaning preserves important structure."""
        raw_text = """
        EXPERIENCE
        
        Software Engineer | TechCorp | 2020-2023
        - Developed web applications
        - Led team of 5 developers
        
        EDUCATION
        
        B.S. Computer Science | University | 2020
        """
        
        result = clean_resume_text(raw_text)
        
        assert "EXPERIENCE" in result
        assert "EDUCATION" in result
        assert "Software Engineer" in result
        assert "TechCorp" in result
        assert "2020-2023" in result
        assert "B.S. Computer Science" in result

    def test_clean_resume_text_special_formatting(self):
        """Test handling of special formatting characters."""
        raw_text = "• Bullet point\n→ Arrow point\n★ Star point"
        
        result = clean_resume_text(raw_text)
        
        assert "•" in result or "Bullet point" in result
        assert "→" in result or "Arrow point" in result
        assert "★" in result or "Star point" in result


class TestSectionSplitting:
    """Test suite for resume section splitting functionality."""

    def test_split_resume_sections_basic(self):
        """Test basic section splitting."""
        resume_text = """
        John Doe
        Software Engineer
        
        EXPERIENCE
        Software Engineer at TechCorp
        Developed applications using Python
        
        SKILLS
        Python, JavaScript, React
        AWS, Docker, Kubernetes
        
        EDUCATION
        B.S. Computer Science
        University of Technology
        """
        
        sections = split_resume_sections(resume_text)
        
        assert isinstance(sections, dict)
        assert "experience" in sections
        assert "skills" in sections
        assert "education" in sections
        
        assert "TechCorp" in sections["experience"]
        assert "Python" in sections["skills"]
        assert "Computer Science" in sections["education"]

    def test_split_resume_sections_various_headings(self):
        """Test section splitting with various heading formats."""
        resume_text = """
        WORK EXPERIENCE
        Senior Developer at ABC Corp
        
        Technical Skills:
        Python, Java, C++
        
        EDUCATION:
        Master of Science in Computer Science
        
        Projects
        Built e-commerce platform
        """
        
        sections = split_resume_sections(resume_text)
        
        # Should handle various heading formats
        assert "experience" in sections
        assert "skills" in sections
        assert "education" in sections
        assert "projects" in sections

    def test_split_resume_sections_case_insensitive(self):
        """Test case-insensitive section detection."""
        resume_text = """
        work experience
        Software Developer
        
        technical skills
        Python, JavaScript
        
        education
        B.S. Computer Science
        """
        
        sections = split_resume_sections(resume_text)
        
        assert "experience" in sections
        assert "skills" in sections
        assert "education" in sections

    def test_split_resume_sections_with_contact_info(self):
        """Test section splitting with contact information."""
        resume_text = """
        John Doe
        john.doe@email.com
        (555) 123-4567
        LinkedIn: linkedin.com/in/johndoe
        
        EXPERIENCE
        Software Engineer
        """
        
        sections = split_resume_sections(resume_text)
        
        if "contact_info" in sections:
            assert "john.doe@email.com" in sections["contact_info"]
            assert "(555) 123-4567" in sections["contact_info"]
        
        assert "experience" in sections

    def test_split_resume_sections_overlapping_keywords(self):
        """Test handling of overlapping keywords in content."""
        resume_text = """
        EXPERIENCE
        Software Engineer with experience in education technology
        
        EDUCATION
        Studied computer science with focus on software engineering
        
        SKILLS
        Educational software development
        """
        
        sections = split_resume_sections(resume_text)
        
        # Should correctly assign content to sections despite keyword overlap
        assert "experience" in sections
        assert "education" in sections
        assert "skills" in sections
        
        assert "Software Engineer" in sections["experience"]
        assert "computer science" in sections["education"]
        assert "Educational software" in sections["skills"]

    def test_split_resume_sections_no_clear_sections(self):
        """Test handling of resume without clear section headers."""
        resume_text = """
        John Doe is a software engineer with 5 years of experience.
        He has worked with Python, JavaScript, and React.
        John graduated from University of Technology with a CS degree.
        """
        
        sections = split_resume_sections(resume_text)
        
        # Should return some structure even without clear headers
        assert isinstance(sections, dict)
        # Might put everything in a general section or try to infer sections

    def test_split_resume_sections_empty_input(self):
        """Test section splitting with empty input."""
        sections = split_resume_sections("")
        
        assert isinstance(sections, dict)
        assert len(sections) == 0

    def test_split_resume_sections_none_input(self):
        """Test section splitting with None input."""
        sections = split_resume_sections(None)
        
        assert isinstance(sections, dict)
        assert len(sections) == 0

    def test_split_resume_sections_malformed_headers(self):
        """Test handling of malformed section headers."""
        resume_text = """
        EXPERIENCE!!!
        Software Engineer
        
        ===SKILLS===
        Python, JavaScript
        
        ---EDUCATION---
        B.S. Computer Science
        """
        
        sections = split_resume_sections(resume_text)
        
        # Should handle malformed headers gracefully
        assert "experience" in sections or len(sections) > 0
        assert "skills" in sections or len(sections) > 0
        assert "education" in sections or len(sections) > 0

    def test_split_resume_sections_multiple_similar_sections(self):
        """Test handling of multiple similar sections."""
        resume_text = """
        WORK EXPERIENCE
        Current job details
        
        PREVIOUS EXPERIENCE  
        Former job details
        
        RELEVANT EXPERIENCE
        Other experience details
        """
        
        sections = split_resume_sections(resume_text)
        
        # Should combine similar sections or handle them appropriately
        assert "experience" in sections
        assert len(sections) > 0

    def test_split_resume_sections_special_characters_in_headers(self):
        """Test handling of special characters in section headers."""
        resume_text = """
        § EXPERIENCE §
        Software Engineer
        
        ★ SKILLS ★
        Python, JavaScript
        
        ▶ EDUCATION ◀
        B.S. Computer Science
        """
        
        sections = split_resume_sections(resume_text)
        
        # Should handle special characters in headers
        assert isinstance(sections, dict)
        assert len(sections) > 0


class TestPDFParserIntegration:
    """Integration tests for PDF parser components."""

    @patch('app.utils.pdf_parser.pdfplumber.open')
    def test_full_pdf_processing_workflow(self, mock_pdf_open):
        """Test complete PDF processing workflow."""
        # Mock a realistic resume PDF
        mock_page = MagicMock()
        mock_page.extract_text.return_value = """
        JOHN DOE
        Software Engineer
        john.doe@email.com | (555) 123-4567
        
        EXPERIENCE
        Senior Software Engineer | TechCorp | 2020-2023
        • Developed scalable web applications using Python and React
        • Led team of 5 developers in agile environment
        • Reduced deployment time by 50% through CI/CD implementation
        
        SKILLS
        Programming: Python, JavaScript, TypeScript, Java
        Frameworks: React, Django, Flask, Node.js
        Cloud: AWS, Docker, Kubernetes
        
        EDUCATION
        B.S. Computer Science | University of Technology | 2020
        GPA: 3.8/4.0
        Relevant Coursework: Data Structures, Algorithms, Software Engineering
        """
        
        mock_pdf = MagicMock()
        mock_pdf.pages = [mock_page]
        mock_pdf.__enter__ = MagicMock(return_value=mock_pdf)
        mock_pdf.__exit__ = MagicMock(return_value=None)
        
        mock_pdf_open.return_value = mock_pdf
        
        # Test complete workflow
        pdf_content = b"fake resume pdf content"
        filename = "john_doe_resume.pdf"
        
        # Step 1: Extract text
        raw_text = extract_resume_text(pdf_content, filename)
        assert "JOHN DOE" in raw_text
        assert "TechCorp" in raw_text
        
        # Step 2: Clean text
        cleaned_text = clean_resume_text(raw_text)
        assert "JOHN DOE" in cleaned_text
        assert "TechCorp" in cleaned_text
        
        # Step 3: Split into sections
        sections = split_resume_sections(cleaned_text)
        
        assert "experience" in sections
        assert "skills" in sections
        assert "education" in sections
        
        assert "TechCorp" in sections["experience"]
        assert "Python" in sections["skills"]
        assert "Computer Science" in sections["education"]

    def test_error_recovery_in_workflow(self):
        """Test error recovery throughout the workflow."""
        # Test with problematic content that might cause issues
        problematic_content = b"corrupted or problematic content"
        
        # Should not raise exceptions
        raw_text = extract_resume_text(problematic_content, "problematic.pdf")
        cleaned_text = clean_resume_text(raw_text)
        sections = split_resume_sections(cleaned_text)
        
        # Should return empty or minimal results, not crash
        assert isinstance(raw_text, str)
        assert isinstance(cleaned_text, str)
        assert isinstance(sections, dict)

    def test_various_file_formats_workflow(self):
        """Test workflow with various file formats."""
        test_content = "John Doe\nSoftware Engineer\nPython, JavaScript"
        
        # Test different file extensions
        formats = ["resume.pdf", "resume.txt", "resume.docx", "resume.unknown"]
        
        for filename in formats:
            content_bytes = test_content.encode('utf-8')
            
            # Should handle all formats gracefully
            raw_text = extract_resume_text(content_bytes, filename)
            cleaned_text = clean_resume_text(raw_text)
            sections = split_resume_sections(cleaned_text)
            
            assert isinstance(raw_text, str)
            assert isinstance(cleaned_text, str)
            assert isinstance(sections, dict) 