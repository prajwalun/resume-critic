import PyPDF2
import io
from typing import Optional
import logging
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def extract_text_from_pdf(pdf_content: bytes) -> str:
    """
    Extract text content from a PDF file.
    
    Args:
        pdf_content: PDF file content as bytes
    
    Returns:
        Extracted text as string
    """
    try:
        # Create a PDF reader object from the bytes
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_content))
        
        # Extract text from all pages
        text_content = ""
        for page_num in range(len(pdf_reader.pages)):
            try:
                page = pdf_reader.pages[page_num]
                page_text = page.extract_text()
                if page_text:
                    text_content += page_text + "\n"
            except Exception as e:
                logger.warning(f"Error extracting text from page {page_num}: {e}")
                continue
        
        return text_content.strip()
    except Exception as e:
        logger.error(f"Error reading PDF: {e}")
        raise ValueError(f"Failed to extract text from PDF: {e}")

def extract_text_from_docx(docx_content: bytes) -> str:
    """
    Extract text content from a DOCX file.
    
    Args:
        docx_content: DOCX file content as bytes
    
    Returns:
        Extracted text as string
    """
    try:
        from docx import Document
        doc = Document(io.BytesIO(docx_content))
        text_content = ""
        for paragraph in doc.paragraphs:
            text_content += paragraph.text + "\n"
        return text_content.strip()
    except Exception as e:
        logger.error(f"Error reading DOCX: {e}")
        raise ValueError(f"Failed to extract text from DOCX: {e}")

def extract_text_from_txt(txt_content: bytes) -> str:
    """
    Extract text content from a TXT file.
    
    Args:
        txt_content: TXT file content as bytes
    
    Returns:
        Extracted text as string
    """
    try:
        # Try different encodings
        encodings = ['utf-8', 'latin-1', 'cp1252']
        for encoding in encodings:
            try:
                return txt_content.decode(encoding).strip()
            except UnicodeDecodeError:
                continue
        raise ValueError("Could not decode text file with any supported encoding")
    except Exception as e:
        logger.error(f"Error reading TXT: {e}")
        raise ValueError(f"Failed to extract text from TXT: {e}")

def extract_resume_text(file_content: bytes, filename: str) -> str:
    """
    Extract text from resume file based on file extension.
    
    Args:
        file_content: File content as bytes
        filename: Original filename
    
    Returns:
        Extracted text as string
    """
    try:
        file_extension = filename.lower().split('.')[-1] if '.' in filename else 'txt'
        
        if file_extension == 'pdf':
            return extract_text_from_pdf(file_content)
        elif file_extension in ['docx', 'doc']:
            return extract_text_from_docx(file_content)
        elif file_extension == 'txt':
            return extract_text_from_txt(file_content)
        else:
            raise ValueError(f"Unsupported file type: {file_extension}")
    except Exception as e:
        logger.error(f"Error extracting text from {filename}: {e}")
        raise

def clean_resume_text(text: str) -> str:
    """
    Clean and normalize resume text.
    
    Args:
        text: Raw resume text
    
    Returns:
        Cleaned resume text
    """
    if not text:
        return ""
    
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove special characters that might interfere with parsing
    text = re.sub(r'[^\w\s\-\.\,\;\:\!\?\(\)\[\]\{\}\@\#\$\%\&\*\+\=\/\|\\]', '', text)
    
    # Normalize line breaks
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    
    # Remove empty lines
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    text = '\n'.join(lines)
    
    return text.strip()

def extract_contact_info(text: str) -> dict:
    """
    Extract contact information from resume text.
    
    Args:
        text: Resume text
    
    Returns:
        Dictionary with contact information
    """
    contact_info = {
        'email': None,
        'phone': None,
        'location': None
    }
    
    # Extract email
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    email_match = re.search(email_pattern, text)
    if email_match:
        contact_info['email'] = email_match.group()
    
    # Extract phone number
    phone_pattern = r'(\+?1?[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})'
    phone_match = re.search(phone_pattern, text)
    if phone_match:
        contact_info['phone'] = ''.join(phone_match.groups())
    
    return contact_info 