"""Pytest configuration and shared fixtures."""

import pytest
from pathlib import Path
import tempfile
import os
from unittest.mock import MagicMock

# Make sure the src directory is in the path for imports
import sys

src_path = Path(__file__).parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))


@pytest.fixture(scope="session")
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
(No )OETGb(   nome   )Gl( V)( A)( Pg)( Qg)( Qn)( Qm)(Bc  )( Pl)( Ql)( Sh)Are(Vf)
    1  2 A BAR-1 GER1  A1000  0.230.2 35.4-99999999.                       11000
    2  1 A BAR-2 GER2  A1000-8.4 100.24.48-99999999.                       11000
    3    E BAR-3       A 989-7.1                                           11000
99999
DLIN
(De )d O d(Pa )NcEP ( R% )( X% )(Mvar)(Tap)(Tmn)(Tmx)(Phs)(Bc  )(Cn)(Ce)Ns
    1         2 1           5.34         1.                      300 300
    2         3 1           7.68         1.                      230 230
99999
DGER
(No ) O (Pmn ) (Pmx ) ( Fp) (FpR) (FPn) (Fa) (Fr) (Ag) ( Xq) (Sno)
    1       0.   650.    0.  100.
    2       0.  1350.    0.  100.
99999
DCSC
    1  A     2 1 L F D      -9999.      9999.       0. X       0.     1   1
99999
DCER
    1 A 1  1     1      5.      0.   -100.    100. I L
99999
FIM
"""


@pytest.fixture
def sample_dbar_data():
    """Sample DBAR data for testing."""
    return [
        {
            "number": "1",
            "name": "BAR-1",
            "type": "2",
            "area": "1",
            "voltage": "1000",
            "angle": "0.0",
            "active_generation": "230.2",
            "reactive_generation": "35.4",
            "active_load": "0.0",
            "reactive_load": "0.0",
            "state": "L",
        },
        {
            "number": "2",
            "name": "BAR-2",
            "type": "1",
            "area": "1",
            "voltage": "1000",
            "angle": "-8.4",
            "active_generation": "100.0",
            "reactive_generation": "24.48",
            "active_load": "0.0",
            "reactive_load": "0.0",
            "state": "L",
        },
    ]


@pytest.fixture
def sample_dlin_data():
    """Sample DLIN data for testing."""
    return [
        {
            "from_bus": "1",
            "to_bus": "2",
            "circuit": "1",
            "resistance": "0.0",
            "reactance": "5.34",
            "susceptance": "0.0",
            "tap": "1.0",
            "normal_capacity": "300",
            "state": "L",
        },
        {
            "from_bus": "2",
            "to_bus": "3",
            "circuit": "1",
            "resistance": "0.0",
            "reactance": "7.68",
            "susceptance": "0.0",
            "tap": "1.0",
            "normal_capacity": "230",
            "state": "L",
        },
    ]


@pytest.fixture
def sample_dger_data():
    """Sample DGER data for testing."""
    return [
        {
            "number": "1",
            "min_active_generation": "0.0",
            "max_active_generation": "650.0",
            "participation_factor": "0.0",
            "remote_control_participation_factor": "100.0",
        },
        {
            "number": "2",
            "min_active_generation": "0.0",
            "max_active_generation": "1350.0",
            "participation_factor": "0.0",
            "remote_control_participation_factor": "100.0",
        },
    ]


@pytest.fixture
def sample_dcsc_data():
    """Sample DCSC data for testing."""
    return [
        {
            "from_bus": "1",
            "to_bus": "2",
            "circuit": "1",
            "state": "L",
            "owner": "F",
            "bypass": "D",
            "min_reactance": "-9999.0",
            "max_reactance": "9999.0",
            "initial_reactance": "0.0",
            "control_mode": "X",
            "specified_value": "0.0",
            "measurement_terminal": "1",
            "number_of_stages": "1",
        }
    ]


@pytest.fixture
def sample_dcer_data():
    """Sample DCER data for testing."""
    return [
        {
            "bus": "1",
            "group": "1",
            "units": "1",
            "controlled_bus": "1",
            "slope": "5.0",
            "reactive_generation": "0.0",
            "min_reactive_generation": "-100.0",
            "max_reactive_generation": "100.0",
            "control_mode": "I",
            "state": "L",
        }
    ]


@pytest.fixture
def sample_parsed_result(
    sample_dbar_data,
    sample_dlin_data,
    sample_dger_data,
    sample_dcsc_data,
    sample_dcer_data,
):
    """Complete sample parsed result for testing."""
    return {
        "DBAR": sample_dbar_data,
        "DLIN": sample_dlin_data,
        "DGER": sample_dger_data,
        "DCSC": sample_dcsc_data,
        "DCER": sample_dcer_data,
        "metadata": {"file_path": "test.pwf", "status": "parsed"},
    }


@pytest.fixture
def mock_field_mappings():
    """Mock field mappings for testing."""
    return {
        "DBAR": {
            "fields": {
                "number": {"column": {"start": 1, "end": 5}, "default": ""},
                "type": {"column": {"start": 6, "end": 7}, "default": ""},
                "operation": {"column": {"start": 8, "end": 8}, "default": "A"},
                "name": {"column": {"start": 9, "end": 21}, "default": ""},
                "voltage": {"column": {"start": 25, "end": 28}, "default": 1.0},
                "angle": {"column": {"start": 29, "end": 32}, "default": 0.0},
                "active_generation": {
                    "column": {"start": 33, "end": 37},
                    "default": 0.0,
                },
                "reactive_generation": {
                    "column": {"start": 38, "end": 42},
                    "default": 0.0,
                },
                "state": {"column": {"start": 24, "end": 24}, "default": "L"},
            }
        },
        "DLIN": {
            "fields": {
                "from_bus": {"column": {"start": 1, "end": 5}, "default": ""},
                "to_bus": {"column": {"start": 10, "end": 14}, "default": ""},
                "circuit": {"column": {"start": 15, "end": 16}, "default": "1"},
                "resistance": {"column": {"start": 23, "end": 27}, "default": 0.0},
                "reactance": {"column": {"start": 28, "end": 32}, "default": 0.0},
                "susceptance": {"column": {"start": 33, "end": 37}, "default": 0.0},
                "tap": {"column": {"start": 38, "end": 42}, "default": 1.0},
                "state": {"column": {"start": 17, "end": 17}, "default": "L"},
            }
        },
        "DGER": {
            "fields": {
                "number": {"column": {"start": 1, "end": 5}, "default": ""},
                "min_active_generation": {
                    "column": {"start": 8, "end": 13},
                    "default": 0.0,
                },
                "max_active_generation": {
                    "column": {"start": 14, "end": 19},
                    "default": 0.0,
                },
                "participation_factor": {
                    "column": {"start": 20, "end": 24},
                    "default": 0.0,
                },
            }
        },
        "DCSC": {
            "fields": {
                "from_bus": {"column": {"start": 1, "end": 5}, "default": ""},
                "to_bus": {"column": {"start": 10, "end": 14}, "default": ""},
                "circuit": {"column": {"start": 15, "end": 16}, "default": "1"},
                "state": {"column": {"start": 17, "end": 17}, "default": "L"},
                "min_reactance": {
                    "column": {"start": 26, "end": 31},
                    "default": -9999.0,
                },
                "max_reactance": {
                    "column": {"start": 32, "end": 37},
                    "default": 9999.0,
                },
            }
        },
        "DCER": {
            "fields": {
                "bus": {"column": {"start": 1, "end": 5}, "default": ""},
                "group": {"column": {"start": 9, "end": 10}, "default": "1"},
                "controlled_bus": {"column": {"start": 15, "end": 19}, "default": ""},
                "slope": {"column": {"start": 21, "end": 26}, "default": 0.0},
                "state": {"column": {"start": 46, "end": 46}, "default": "L"},
            }
        },
    }


@pytest.fixture
def mock_anarede_parser(mock_field_mappings):
    """Mock ANAREDE parser with field mappings."""
    from pyxparser.parser.anarede import AnaredeParser

    parser = AnaredeParser()
    parser.field_mappings = mock_field_mappings
    return parser


@pytest.fixture
def mock_args():
    """Mock command line arguments for testing."""
    args = MagicMock()
    args.input = "test.pwf"
    args.output = "output.dat"
    args.format = "dat"
    args.verbose = False
    args.print = False
    return args


@pytest.fixture(autouse=True)
def reset_loguru():
    """Reset loguru logger between tests."""
    from loguru import logger

    logger.remove()
    yield
    logger.remove()


@pytest.fixture
def capture_logs():
    """Capture log messages during tests."""
    from loguru import logger
    import io

    # Create a string buffer to capture logs
    log_buffer = io.StringIO()

    # Add handler to capture logs
    handler_id = logger.add(log_buffer, level="DEBUG", format="{message}")

    yield log_buffer

    # Clean up
    logger.remove(handler_id)


@pytest.fixture
def mock_file_system(tmp_path):
    """Mock file system operations for testing."""
    # Create test directories
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "output"
    input_dir.mkdir()
    output_dir.mkdir()

    # Create sample files
    (input_dir / "test1.pwf").write_text("DBAR\n1\n99999\nFIM\n")
    (input_dir / "test2.pwf").write_text("DBAR\n2\n99999\nFIM\n")
    (input_dir / "readme.txt").write_text("Not a PWF file")

    return {
        "input_dir": input_dir,
        "output_dir": output_dir,
        "test_files": ["test1.pwf", "test2.pwf"],
        "non_pwf_file": "readme.txt",
    }


@pytest.fixture
def suppress_logging():
    """Suppress logging output during tests."""
    from loguru import logger

    logger.remove()
    yield
    logger.remove()


# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line(
        "markers", "cli: marks tests that require CLI functionality"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers automatically."""
    for item in items:
        # Mark slow tests
        if "large_file" in item.name or "test_cli_integration" in item.name:
            item.add_marker(pytest.mark.slow)

        # Mark integration tests
        if "integration" in item.fspath.basename or "test_end_to_end" in item.name:
            item.add_marker(pytest.mark.integration)

        # Mark CLI tests
        if "cli" in item.name.lower():
            item.add_marker(pytest.mark.cli)


# Custom pytest options
def pytest_addoption(parser):
    """Add custom command line options."""
    parser.addoption(
        "--run-slow", action="store_true", default=False, help="run slow tests"
    )
    parser.addoption(
        "--run-integration",
        action="store_true",
        default=False,
        help="run integration tests",
    )


def pytest_runtest_setup(item):
    """Setup for individual test runs."""
    # Skip slow tests unless --run-slow is given
    if "slow" in item.keywords and not item.config.getoption("--run-slow"):
        pytest.skip("need --run-slow option to run")

    # Skip integration tests unless --run-integration is given
    if "integration" in item.keywords and not item.config.getoption(
        "--run-integration"
    ):
        pytest.skip("need --run-integration option to run")


# Environment setup
@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Setup test environment."""
    # Ensure test data directory exists
    test_data_dir = Path(__file__).parent / "data"
    test_data_dir.mkdir(exist_ok=True)

    # Create sample data if it doesn't exist
    if not (test_data_dir / "9bus").exists():
        (test_data_dir / "9bus").mkdir()

    # Set environment variables for testing
    os.environ["PYXPARSER_TEST_MODE"] = "1"

    yield

    # Cleanup
    if "PYXPARSER_TEST_MODE" in os.environ:
        del os.environ["PYXPARSER_TEST_MODE"]
