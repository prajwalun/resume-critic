"""
Professional Logging Configuration for ResumeWise
Structured, clean, and meaningful logging for production use.
"""

import logging
import sys
import json
from datetime import datetime
from typing import Dict, Any


class ProfessionalFormatter(logging.Formatter):
    """Professional formatter for structured, clean log output."""
    
    def __init__(self):
        super().__init__()
        
        # Define color codes for terminal output
        self.COLORS = {
            'DEBUG': '\033[90m',     # Dark Gray
            'INFO': '\033[32m',      # Green  
            'WARNING': '\033[33m',   # Yellow
            'ERROR': '\033[31m',     # Red
            'CRITICAL': '\033[35m',  # Magenta
            'RESET': '\033[0m'       # Reset
        }
        
        # Define professional formats - clean and structured
        self.FORMATS = {
            'DEBUG': '[DEBUG] {message}',
            'INFO': '[INFO] {message}',
            'WARNING': '[WARN] {message}',
            'ERROR': '[ERROR] {message}',
            'CRITICAL': '[CRITICAL] {message}'
        }
    
    def format(self, record):
        """Format log record with professional styling."""
        
        # Get timestamp
        timestamp = datetime.now().strftime('%H:%M:%S')
        
        # Get the appropriate format and color
        log_format = self.FORMATS.get(record.levelname, '{message}')
        color = self.COLORS.get(record.levelname, '')
        reset = self.COLORS['RESET']
        
        # Format the message
        message = record.getMessage()
        
        # Truncate very long messages for readability
        if len(message) > 120:
            message = message[:117] + "..."
        
        formatted_message = f"[{timestamp}] {log_format.format(message=message)}"
        
        # Add color if terminal supports it
        if sys.stderr.isatty():
            return f"{color}{formatted_message}{reset}"
        else:
            return formatted_message


class ResumeWiseLogger:
    """Centralized logger for ResumeWise with structured logging methods."""
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
    
    def session_started(self, session_id: str, sections_count: int):
        """Log session start with key metrics."""
        self.logger.info(f"Session {session_id[:8]} started | {sections_count} sections detected")
    
    def analysis_progress(self, session_id: str, section: str, status: str):
        """Log analysis progress updates."""
        self.logger.info(f"Session {session_id[:8]} | {section.title()}: {status}")
    
    def clarification_requested(self, session_id: str, section: str, count: int = 1):
        """Log clarification requests without showing the full question."""
        self.logger.warning(f"Session {session_id[:8]} | {section.title()}: Clarification needed ({count} questions)")
    
    def user_decision(self, session_id: str, section: str, accepted: bool):
        """Log user accept/reject decisions."""
        status = "Accepted" if accepted else "Rejected"
        self.logger.info(f"Session {session_id[:8]} | {section.title()}: {status}")
    
    def session_completed(self, session_id: str, sections_processed: int, clarifications: int):
        """Log session completion summary."""
        self.logger.info(f"Session {session_id[:8]} completed | {sections_processed} sections, {clarifications} clarifications")
    
    def error_occurred(self, session_id: str, operation: str, error_msg: str):
        """Log errors with context."""
        short_error = error_msg[:80] + "..." if len(error_msg) > 80 else error_msg
        self.logger.error(f"Session {session_id[:8]} | {operation}: {short_error}")
    
    def debug(self, message: str):
        """Debug logging - only shown in debug mode."""
        self.logger.debug(message)
    
    def info(self, message: str):
        """Standard info logging."""
        self.logger.info(message)
    
    def warning(self, message: str):
        """Warning logging."""
        self.logger.warning(message)
    
    def error(self, message: str):
        """Error logging."""
        self.logger.error(message)


def setup_professional_logging(log_level: str = "INFO"):
    """Set up professional, structured logging for ResumeWise."""
    
    # Convert string level to logging constant
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Create root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create console handler with professional formatter
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(ProfessionalFormatter())
    
    # Add handler to root logger
    root_logger.addHandler(console_handler)
    
    # Suppress verbose third-party logging
    third_party_suppressions = {
        'uvicorn.access': logging.WARNING,
        'uvicorn.error': logging.ERROR,
        'fastapi': logging.WARNING,
        'openai': logging.WARNING,
        'httpx': logging.WARNING,
        'httpcore': logging.WARNING,
        'urllib3': logging.WARNING,
        'requests': logging.WARNING,
        'openai._client': logging.WARNING,
        'httpx._client': logging.WARNING,
        'judgeval': logging.ERROR,  # Suppress judgment framework verbose logs
        'judgeval.common.tracer': logging.ERROR,
        'judgeval.scorers': logging.ERROR,
        'watchfiles': logging.WARNING,  # Suppress file watching logs
        'app.utils.pdf_parser': logging.WARNING,  # Suppress PDF parsing details
    }
    
    for logger_name, level in third_party_suppressions.items():
        logging.getLogger(logger_name).setLevel(level)
    
    # Configure uvicorn to show only essential startup info
    uvicorn_logger = logging.getLogger('uvicorn')
    uvicorn_logger.setLevel(logging.INFO)
    
    # Suppress specific verbose patterns
    logging.getLogger('app.core.resume_agent').addFilter(
        lambda record: not any(phrase in record.getMessage() for phrase in [
            "Agent action logged:",
            "Starting iterative improvement",
            "Running fabrication detection", 
            "Fabrication analysis for",
            "Generated intelligent clarification",
            "Clarification required for",
            "Content needs formatting improvements"
        ])
    )
    
    return logging.getLogger(__name__)


def get_resume_logger(name: str) -> ResumeWiseLogger:
    """Get a ResumeWise logger instance with structured logging methods."""
    return ResumeWiseLogger(name)


# Backward compatibility
def get_clean_logger(name: str):
    """Get a logger instance - for backward compatibility."""
    return get_resume_logger(name) 