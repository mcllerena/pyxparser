"""Pytest configuration and shared fixtures."""

import pytest
from pathlib import Path
import tempfile


@pytest.fixture
def sample_data_dir():
    """Return path to sample data directory."""
    return Path(__file__).parent / "data"


@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for test outputs."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)


@pytest.fixture
def minimal_pwf_content():
    """Minimal valid PWF content for testing."""
    return """DBAR
    1  E BUS1          A1000  0.                                           11000
99999
FIM
"""


@pytest.fixture
def complete_pwf_content():
    """Complete PWF content with all sections for testing."""
    return """TITU
Test System
DOPC IMPR
99999
DBAR
    1  2 A BAR-1 GER1  A1000  0.230.2 35.4-99999999.                       11000
    2  1 A BAR-2 GER2  A1000-8.4 100.24.48-99999999.                       11000
99999
DLIN
    1         2 1           5.34         1.                      300 300
99999
DGER
    1       0.   650.    0.  100.
99999
DCSC
    1  A     2 1 L F D      -9999.      9999.       0. X       0.     1   1
99999
DCER
    1 A 1  1     1      5.      0.   -100.    100. I L
99999
FIM
"""
