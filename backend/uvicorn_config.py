"""
Clean Uvicorn Configuration for ResumeWise
Suppresses verbose request logging while keeping essential information.
"""

import logging
import sys

# Suppress uvicorn access logs (HTTP requests)
uvicorn_logger = logging.getLogger("uvicorn.access")
uvicorn_logger.disabled = True

# Keep uvicorn startup info but make it cleaner
uvicorn_error_logger = logging.getLogger("uvicorn.error")
uvicorn_error_logger.setLevel(logging.WARNING)

# Clean format for essential logs only
class CleanFilter(logging.Filter):
    """Filter to show only essential logs."""
    
    def filter(self, record):
        # Suppress HTTP request logs completely
        if "GET" in record.getMessage() or "POST" in record.getMessage():
            return False
        if "HTTP" in record.getMessage():
            return False
        if "Uvicorn running on" in record.getMessage():
            # Clean up the startup message
            record.msg = "🚀 ResumeWise API running on %s"
        return True

# Apply clean filter
for handler in logging.root.handlers:
    handler.addFilter(CleanFilter())

# Setup clean console output
if not logging.root.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.INFO)
    handler.addFilter(CleanFilter())
    logging.root.addHandler(handler)
    logging.root.setLevel(logging.INFO) 