"""
Clean, Professional Logging Configuration for ResumeWise
"""

import logging
import sys


class CleanFormatter(logging.Formatter):
    """Custom formatter for clean, professional log output."""
    
    def __init__(self):
        super().__init__()
        
        # Define color codes
        self.COLORS = {
            'DEBUG': '\033[36m',     # Cyan
            'INFO': '\033[32m',      # Green  
            'WARNING': '\033[33m',   # Yellow
            'ERROR': '\033[31m',     # Red
            'CRITICAL': '\033[35m',  # Magenta
            'RESET': '\033[0m'       # Reset
        }
        
        # Define clean formats
        self.FORMATS = {
            'DEBUG': '[DEBUG] {message}',
            'INFO': '[INFO] {message}',
            'WARNING': '[WARNING] {message}',
            'ERROR': '[ERROR] {message}',
            'CRITICAL': '[CRITICAL] {message}'
        }
    
    def format(self, record):
        """Format log record with clean, professional styling."""
        
        # Get the appropriate format and color
        log_format = self.FORMATS.get(record.levelname, '{message}')
        color = self.COLORS.get(record.levelname, '')
        reset = self.COLORS['RESET']
        
        # Format the message
        formatted_message = log_format.format(message=record.getMessage())
        
        # Add color if terminal supports it
        if sys.stderr.isatty():
            return f"{color}{formatted_message}{reset}"
        else:
            return formatted_message


def setup_clean_logging():
    """Set up clean, professional logging for ResumeWise."""
    
    # Create root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create console handler with clean formatter
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(CleanFormatter())
    
    # Add handler to root logger
    root_logger.addHandler(console_handler)
    
    # Suppress verbose third-party logging
    third_party_loggers = [
        'uvicorn.access',
        'uvicorn.error', 
        'fastapi',
        'openai',
        'httpx',
        'httpcore',
        'urllib3',
        'requests'
    ]
    
    for logger_name in third_party_loggers:
        logging.getLogger(logger_name).setLevel(logging.WARNING)
    
    # Set specific uvicorn loggers to show only essential info
    logging.getLogger('uvicorn').setLevel(logging.INFO)
    
    return logging.getLogger(__name__)


def get_clean_logger(name: str):
    """Get a logger instance with clean formatting."""
    return logging.getLogger(name) 