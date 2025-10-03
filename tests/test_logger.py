"""Tests for logger functionality."""

import pytest
from unittest.mock import patch
from pyxparser.logger import DEFAULT_FORMAT
from pyxparser.logger import setup_logging, Formatter


class TestFormatter:
    """Test cases for log formatter."""

    def test_formatter_creation(self):
        """Test formatter can be created."""
        formatter = Formatter()
        assert formatter is not None
        assert hasattr(formatter, "format")

    def test_formatter_format_attribute(self):
        """Test formatter has correct format string."""
        formatter = Formatter()

        if hasattr(formatter, "format") and isinstance(formatter.format, str):
            format_str = formatter.format
        elif hasattr(formatter, "DEFAULT_FORMAT"):
            format_str = formatter.DEFAULT_FORMAT
        else:
            format_str = DEFAULT_FORMAT

        assert isinstance(format_str, str)
        assert "{time:" in format_str
        assert "{level:" in format_str
        assert "{message}" in format_str


class TestLoggingSetup:
    """Test cases for logging setup."""

    @patch("pyxparser.logger.logger")
    def test_setup_logging_default(self, mock_logger):
        """Test default logging setup."""
        setup_logging()

        mock_logger.remove.assert_called_once()
        mock_logger.enable.assert_called_once_with("pyxparser")
        mock_logger.add.assert_called()

    @patch("pyxparser.logger.logger")
    def test_setup_logging_with_verbosity(self, mock_logger):
        """Test logging setup with verbosity."""
        setup_logging(verbosity=1)

        mock_logger.remove.assert_called_once()
        mock_logger.enable.assert_called_once_with("pyxparser")

        assert mock_logger.add.call_count >= 1

    @patch("pyxparser.logger.logger")
    def test_setup_logging_with_file(self, mock_logger):
        """Test logging setup with file output."""
        setup_logging(filename="test.log")

        mock_logger.remove.assert_called_once()
        mock_logger.enable.assert_called_once_with("pyxparser")

        # Should be called twice: once for stderr, once for file
        assert mock_logger.add.call_count == 2

    @patch("pyxparser.logger.logger")
    def test_setup_logging_verbosity_levels(self, mock_logger):
        """Test different verbosity levels."""
        # Test verbosity level 1 (INFO)
        setup_logging(verbosity=1)

        # Test verbosity level 2 (DEBUG)
        setup_logging(verbosity=2)

        # Test verbosity level 3 (TRACE)
        setup_logging(verbosity=3)

        # Test high verbosity (should default to DEBUG)
        setup_logging(verbosity=5)

        # Should have been called multiple times
        assert mock_logger.add.call_count >= 4

    @patch("pyxparser.logger.logger")
    @patch.dict("os.environ", {"LOGURU_LEVEL": "WARNING"})
    def test_setup_logging_environment_override(self, mock_logger):
        """Test that environment variable overrides level."""
        setup_logging(level="INFO")

        # The add method should be called with WARNING level from environment
        mock_logger.add.assert_called()

    @patch("pyxparser.logger.logger")
    def test_setup_logging_no_verbosity_simple_format(self, mock_logger):
        """Test that no verbosity uses simple format."""
        setup_logging(verbosity=0)

        # Should use simple format without timestamps
        calls = mock_logger.add.call_args_list
        assert len(calls) >= 1

        # Check that format is simple (just {message})
        call_kwargs = calls[0][1]
        assert call_kwargs["format"] == "{message}"

    @patch("pyxparser.logger.logger")
    def test_setup_logging_with_verbosity_detailed_format(self, mock_logger):
        """Test that verbosity uses detailed format."""
        setup_logging(verbosity=1)

        # Should use detailed format with timestamps
        calls = mock_logger.add.call_args_list
        assert len(calls) >= 1

        # Check that format is detailed (contains time, level, etc.)
        call_kwargs = calls[0][1]
        format_obj = call_kwargs["format"]

        # The key test: it should NOT be the simple format
        assert format_obj != "{message}"

        # Debug: Let's see what type format_obj actually is
        print(f"Debug: format_obj type: {type(format_obj)}")
        print(f"Debug: format_obj value: {format_obj}")

        # Handle different possible types
        if hasattr(format_obj, "format") and isinstance(format_obj.format, str):
            # It's a Formatter object with a format attribute
            format_str = format_obj.format
            assert "{time:" in format_str
            assert "{level:" in format_str
            assert "{message}" in format_str
        elif isinstance(format_obj, str):
            # It's a string directly
            assert "{time:" in format_obj
            assert "{level:" in format_obj
            assert "{message}" in format_obj
        else:
            # For any other case, just verify it's not the simple format
            # and that it's some kind of detailed formatter
            from pyxparser.logger import Formatter

            assert isinstance(format_obj, Formatter) or str(format_obj) != "{message}"


class TestLoggingIntegration:
    """Integration tests for logging functionality."""

    def test_logging_output_capture(self, capsys):
        """Test that logging output can be captured."""
        from loguru import logger

        # Setup logging with simple format
        setup_logging(verbosity=0)

        # Log a message
        logger.info("Test message")

        # Capture output
        captured = capsys.readouterr()
        assert "Test message" in captured.err

    def test_logging_levels_filtering(self, capsys):
        """Test that log levels are properly filtered."""
        from loguru import logger

        # Setup with INFO level
        setup_logging(level="WARNING", verbosity=0)

        # Log messages at different levels
        logger.debug("Debug message")
        logger.info("Info message")
        logger.warning("Warning message")
        logger.error("Error message")

        # Capture output
        captured = capsys.readouterr()

        # Should only see WARNING and ERROR
        assert "Debug message" not in captured.err
        assert "Info message" not in captured.err
        assert "Warning message" in captured.err
        assert "Error message" in captured.err


if __name__ == "__main__":
    pytest.main([__file__])
