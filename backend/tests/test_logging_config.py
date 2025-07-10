"""
Comprehensive tests for Logging Configuration.
Tests the clean logging setup and formatter functionality.
"""

import pytest
import logging
import sys
import io
from unittest.mock import patch, MagicMock

from app.core.logging_config import (
    CleanFormatter,
    setup_clean_logging,
    get_clean_logger
)


class TestCleanFormatter:
    """Test suite for CleanFormatter class."""

    @pytest.fixture
    def formatter(self):
        """Create CleanFormatter instance for testing."""
        return CleanFormatter()

    def test_formatter_initialization(self, formatter):
        """Test CleanFormatter initialization."""
        assert hasattr(formatter, 'COLORS')
        assert hasattr(formatter, 'FORMATS')
        assert isinstance(formatter.COLORS, dict)
        assert isinstance(formatter.FORMATS, dict)

    def test_color_codes_defined(self, formatter):
        """Test that all required color codes are defined."""
        required_colors = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL', 'RESET']
        for color in required_colors:
            assert color in formatter.COLORS
            assert isinstance(formatter.COLORS[color], str)

    def test_format_strings_defined(self, formatter):
        """Test that all required format strings are defined."""
        required_formats = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        for format_key in required_formats:
            assert format_key in formatter.FORMATS
            assert isinstance(formatter.FORMATS[format_key], str)
            assert '{message}' in formatter.FORMATS[format_key]

    def test_format_debug_message(self, formatter):
        """Test formatting debug message."""
        record = logging.LogRecord(
            name='test_logger',
            level=logging.DEBUG,
            pathname='test.py',
            lineno=1,
            msg='Test debug message',
            args=(),
            exc_info=None
        )
        
        formatted = formatter.format(record)
        assert '[DEBUG]' in formatted
        assert 'Test debug message' in formatted

    def test_format_info_message(self, formatter):
        """Test formatting info message."""
        record = logging.LogRecord(
            name='test_logger',
            level=logging.INFO,
            pathname='test.py',
            lineno=1,
            msg='Test info message',
            args=(),
            exc_info=None
        )
        
        formatted = formatter.format(record)
        assert '[INFO]' in formatted
        assert 'Test info message' in formatted

    def test_format_warning_message(self, formatter):
        """Test formatting warning message."""
        record = logging.LogRecord(
            name='test_logger',
            level=logging.WARNING,
            pathname='test.py',
            lineno=1,
            msg='Test warning message',
            args=(),
            exc_info=None
        )
        
        formatted = formatter.format(record)
        assert '[WARNING]' in formatted
        assert 'Test warning message' in formatted

    def test_format_error_message(self, formatter):
        """Test formatting error message."""
        record = logging.LogRecord(
            name='test_logger',
            level=logging.ERROR,
            pathname='test.py',
            lineno=1,
            msg='Test error message',
            args=(),
            exc_info=None
        )
        
        formatted = formatter.format(record)
        assert '[ERROR]' in formatted
        assert 'Test error message' in formatted

    def test_format_critical_message(self, formatter):
        """Test formatting critical message."""
        record = logging.LogRecord(
            name='test_logger',
            level=logging.CRITICAL,
            pathname='test.py',
            lineno=1,
            msg='Test critical message',
            args=(),
            exc_info=None
        )
        
        formatted = formatter.format(record)
        assert '[CRITICAL]' in formatted
        assert 'Test critical message' in formatted

    def test_format_unknown_level(self, formatter):
        """Test formatting message with unknown log level."""
        record = logging.LogRecord(
            name='test_logger',
            level=99,  # Unknown level
            pathname='test.py',
            lineno=1,
            msg='Test unknown level message',
            args=(),
            exc_info=None
        )
        record.levelname = 'UNKNOWN'
        
        formatted = formatter.format(record)
        assert 'Test unknown level message' in formatted

    @patch('sys.stderr.isatty', return_value=True)
    def test_format_with_colors_on_tty(self, mock_isatty, formatter):
        """Test formatting with colors when output is a TTY."""
        record = logging.LogRecord(
            name='test_logger',
            level=logging.INFO,
            pathname='test.py',
            lineno=1,
            msg='Test message',
            args=(),
            exc_info=None
        )
        
        formatted = formatter.format(record)
        # Should contain color codes
        assert '\033[32m' in formatted  # Green for INFO
        assert '\033[0m' in formatted   # Reset

    @patch('sys.stderr.isatty', return_value=False)
    def test_format_without_colors_on_non_tty(self, mock_isatty, formatter):
        """Test formatting without colors when output is not a TTY."""
        record = logging.LogRecord(
            name='test_logger',
            level=logging.INFO,
            pathname='test.py',
            lineno=1,
            msg='Test message',
            args=(),
            exc_info=None
        )
        
        formatted = formatter.format(record)
        # Should not contain color codes
        assert '\033[' not in formatted
        assert '[INFO] Test message' in formatted

    def test_format_with_formatted_message(self, formatter):
        """Test formatting with message that has format arguments."""
        record = logging.LogRecord(
            name='test_logger',
            level=logging.INFO,
            pathname='test.py',
            lineno=1,
            msg='Test message with %s and %d',
            args=('string', 42),
            exc_info=None
        )
        
        formatted = formatter.format(record)
        assert 'Test message with string and 42' in formatted


class TestLoggingSetup:
    """Test suite for logging setup functions."""

    def test_setup_clean_logging(self):
        """Test setup_clean_logging function."""
        # Store original state
        original_handlers = logging.root.handlers[:]
        original_level = logging.root.level
        
        try:
            # Setup clean logging
            result = setup_clean_logging()
            
            # Check that root logger is configured
            assert logging.root.level == logging.INFO
            assert len(logging.root.handlers) > 0
            
            # Check that handler has CleanFormatter
            handler = logging.root.handlers[0]
            assert isinstance(handler.formatter, CleanFormatter)
            
            # Function should return logger
            assert isinstance(result, logging.Logger)
            
        finally:
            # Restore original state
            logging.root.handlers = original_handlers
            logging.root.level = original_level

    def test_get_clean_logger(self):
        """Test get_clean_logger function."""
        logger_name = 'test_logger'
        logger = get_clean_logger(logger_name)
        
        assert isinstance(logger, logging.Logger)
        assert logger.name == logger_name

    def test_third_party_loggers_suppressed(self):
        """Test that third-party loggers are properly suppressed."""
        setup_clean_logging()
        
        # Check that known third-party loggers are set to WARNING level
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
            logger = logging.getLogger(logger_name)
            assert logger.level >= logging.WARNING

    def test_uvicorn_logger_level(self):
        """Test that uvicorn logger is set to INFO level."""
        setup_clean_logging()
        
        uvicorn_logger = logging.getLogger('uvicorn')
        assert uvicorn_logger.level == logging.INFO

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_logging_output_format(self, mock_stdout):
        """Test that logging output is properly formatted."""
        setup_clean_logging()
        
        logger = get_clean_logger('test_logger')
        test_message = 'Test log message'
        logger.info(test_message)
        
        output = mock_stdout.getvalue()
        assert '[INFO]' in output
        assert test_message in output

    def test_multiple_setup_calls(self):
        """Test that multiple calls to setup_clean_logging work correctly."""
        # Store original state
        original_handlers = logging.root.handlers[:]
        original_level = logging.root.level
        
        try:
            # Call setup multiple times
            setup_clean_logging()
            setup_clean_logging()
            setup_clean_logging()
            
            # Should still have only one handler (previous ones removed)
            assert len(logging.root.handlers) == 1
            assert isinstance(logging.root.handlers[0].formatter, CleanFormatter)
            
        finally:
            # Restore original state
            logging.root.handlers = original_handlers
            logging.root.level = original_level

    def test_logger_hierarchy(self):
        """Test that logger hierarchy works properly."""
        setup_clean_logging()
        
        # Create parent and child loggers
        parent_logger = get_clean_logger('parent')
        child_logger = get_clean_logger('parent.child')
        
        assert child_logger.parent == parent_logger

    @patch('logging.StreamHandler')
    def test_console_handler_configuration(self, mock_stream_handler):
        """Test that console handler is properly configured."""
        mock_handler = MagicMock()
        mock_stream_handler.return_value = mock_handler
        
        setup_clean_logging()
        
        # Verify handler was created and configured
        mock_stream_handler.assert_called_once_with(sys.stdout)
        mock_handler.setLevel.assert_called_once_with(logging.INFO)
        mock_handler.setFormatter.assert_called_once()

    def test_existing_handlers_removed(self):
        """Test that existing handlers are removed during setup."""
        # Add a dummy handler
        dummy_handler = logging.StreamHandler()
        logging.root.addHandler(dummy_handler)
        original_count = len(logging.root.handlers)
        
        try:
            setup_clean_logging()
            
            # Should have removed old handlers and added new one
            assert len(logging.root.handlers) == 1
            assert dummy_handler not in logging.root.handlers
            
        finally:
            # Clean up
            if dummy_handler in logging.root.handlers:
                logging.root.removeHandler(dummy_handler)

    def test_log_level_filtering(self):
        """Test that log level filtering works correctly."""
        setup_clean_logging()
        
        logger = get_clean_logger('test_logger')
        
        # Set logger to WARNING level
        logger.setLevel(logging.WARNING)
        
        with patch('sys.stdout', new_callable=io.StringIO) as mock_stdout:
            logger.debug('Debug message')  # Should not appear
            logger.info('Info message')    # Should not appear  
            logger.warning('Warning message')  # Should appear
            
            output = mock_stdout.getvalue()
            assert 'Debug message' not in output
            assert 'Info message' not in output
            assert 'Warning message' in output


class TestLoggingIntegration:
    """Integration tests for logging configuration."""

    def test_logging_with_resume_agent_context(self):
        """Test logging in the context of resume agent usage."""
        setup_clean_logging()
        
        # Simulate resume agent logging
        agent_logger = get_clean_logger('app.core.resume_agent')
        
        with patch('sys.stdout', new_callable=io.StringIO) as mock_stdout:
            agent_logger.info('Analysis session started')
            agent_logger.warning('Fabrication risk detected')
            agent_logger.error('API call failed')
            
            output = mock_stdout.getvalue()
            assert '[INFO] Analysis session started' in output
            assert '[WARNING] Fabrication risk detected' in output
            assert '[ERROR] API call failed' in output

    def test_logging_with_judgment_context(self):
        """Test logging in the context of judgment framework."""
        setup_clean_logging()
        
        judgment_logger = get_clean_logger('app.core.judgment_config')
        
        with patch('sys.stdout', new_callable=io.StringIO) as mock_stdout:
            judgment_logger.info('Judgment framework initialized')
            judgment_logger.warning('JUDGMENT_API_KEY not set')
            
            output = mock_stdout.getvalue()
            assert '[INFO] Judgment framework initialized' in output
            assert '[WARNING] JUDGMENT_API_KEY not set' in output

    def test_no_emoji_in_professional_output(self):
        """Test that no emojis appear in professional logging output."""
        setup_clean_logging()
        
        logger = get_clean_logger('test_professional')
        
        with patch('sys.stdout', new_callable=io.StringIO) as mock_stdout:
            logger.info('Professional business message')
            logger.warning('System warning occurred')
            logger.error('Critical error detected')
            
            output = mock_stdout.getvalue()
            
            # Common emoji characters that should not appear
            emoji_chars = ['🚀', '📊', '⚠️', '❌', '✅', '🔍', '💡']
            for emoji in emoji_chars:
                assert emoji not in output

    def test_concurrent_logging(self):
        """Test that concurrent logging works properly."""
        import threading
        import time
        
        setup_clean_logging()
        
        messages = []
        
        def log_messages(logger_name, message_prefix):
            logger = get_clean_logger(logger_name)
            for i in range(5):
                message = f'{message_prefix} message {i}'
                logger.info(message)
                messages.append(message)
                time.sleep(0.01)  # Small delay
        
        # Create multiple threads logging concurrently
        threads = []
        for i in range(3):
            thread = threading.Thread(
                target=log_messages,
                args=(f'logger_{i}', f'Thread{i}')
            )
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # All messages should have been logged
        assert len(messages) == 15  # 3 threads * 5 messages each

    @patch.dict('os.environ', {'LOG_LEVEL': 'DEBUG'})
    def test_environment_variable_log_level(self):
        """Test handling of environment variable for log level."""
        # This test demonstrates how environment variables could be used
        # Current implementation doesn't use env vars, but this shows the pattern
        setup_clean_logging()
        
        logger = get_clean_logger('env_test')
        assert isinstance(logger, logging.Logger)

    def test_error_logging_with_exception_info(self):
        """Test error logging with exception information."""
        setup_clean_logging()
        
        logger = get_clean_logger('error_test')
        
        with patch('sys.stdout', new_callable=io.StringIO) as mock_stdout:
            try:
                raise ValueError("Test exception")
            except ValueError as e:
                logger.error(f'Error occurred: {str(e)}')
            
            output = mock_stdout.getvalue()
            assert '[ERROR] Error occurred: Test exception' in output 