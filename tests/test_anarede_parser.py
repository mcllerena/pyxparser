"""Tests for PWF (ANAREDE) parser functionality."""

import pytest
from pathlib import Path
from unittest.mock import patch

from pyxparser.parser.anarede import AnaredeParser
from pyxparser.cli_functions import _format_dat_file


class TestAnaredeParser:
    """Test cases for ANAREDE parser."""

    @pytest.fixture
    def parser(self):
        """Create an ANAREDE parser instance."""
        return AnaredeParser()

    @pytest.fixture
    def sample_pwf_content(self):
        """Sample PWF file content for testing."""
        return """TITU
Sistema-Teste de 9 Barras - Caso Inicial
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
    1         3 1           5.34         1.                      300 300
    2         4 1           7.68         1.                      230 230
99999
DGER
(No ) O (Pmn ) (Pmx ) ( Fp) (FpR) (FPn) (Fa) (Fr) (Ag) ( Xq) (Sno)
    1       0.   650.    0.  100.
    2       0.  1350.    0.  100.
99999
FIM
"""

    def test_parser_initialization(self, parser):
        """Test parser initialization."""
        assert parser is not None
        assert hasattr(parser, "field_mappings")

    def test_parse_file_success(self, parser, tmp_path, sample_pwf_content):
        """Test successful file parsing."""
        # Create temporary PWF file
        test_file = tmp_path / "test.pwf"
        test_file.write_text(sample_pwf_content, encoding="utf-8")

        # Parse the file
        result = parser.parse_file(test_file)

        # Verify structure
        assert isinstance(result, dict)
        assert "DBAR" in result
        assert "DLIN" in result
        assert "DGER" in result
        assert "metadata" in result

        # Verify metadata
        assert result["metadata"]["file_path"] == str(test_file)
        assert result["metadata"]["status"] == "parsed"

        # Verify data was parsed
        assert len(result["DBAR"]) > 0
        assert len(result["DLIN"]) > 0
        assert len(result["DGER"]) > 0

    def test_parse_nonexistent_file(self, parser):
        """Test parsing non-existent file raises error."""
        with pytest.raises(FileNotFoundError):
            parser.parse_file(Path("nonexistent.pwf"))

    def test_parse_dbar_record(self, parser):
        """Test DBAR record parsing."""
        line = "    1  2 A BAR-1 GER1  A1000  0.230.2 35.4-99999999.                       11000"

        # Mock field mappings for DBAR
        with patch.object(parser, "field_mappings") as mock_mappings:
            mock_mappings.get.return_value = {
                "fields": {
                    "number": {"column": {"start": 1, "end": 5}, "default": ""},
                    "type": {"column": {"start": 6, "end": 7}, "default": ""},
                    "operation": {"column": {"start": 8, "end": 8}, "default": "A"},
                    "name": {"column": {"start": 9, "end": 21}, "default": ""},
                }
            }

            result = parser.parse_dbar_record(line)

            assert isinstance(result, dict)
            assert "number" in result
            assert "name" in result

    def test_parse_dlin_record(self, parser):
        """Test DLIN record parsing."""
        line = (
            "    1         3 1           5.34         1.                      300 300"
        )

        with patch.object(parser, "field_mappings") as mock_mappings:
            mock_mappings.get.return_value = {
                "fields": {
                    "from_bus": {"column": {"start": 1, "end": 5}, "default": ""},
                    "to_bus": {"column": {"start": 10, "end": 14}, "default": ""},
                    "circuit": {"column": {"start": 15, "end": 16}, "default": ""},
                }
            }

            result = parser.parse_dlin_record(line)

            assert isinstance(result, dict)
            assert "from_bus" in result
            assert "to_bus" in result

    def test_parse_dger_record(self, parser):
        """Test DGER record parsing."""
        line = "    1       0.   650.    0.  100.                                 "

        with patch.object(parser, "field_mappings") as mock_mappings:
            mock_mappings.get.return_value = {
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
                }
            }

            result = parser.parse_dger_record(line)

            assert isinstance(result, dict)
            assert "number" in result

    def test_skip_unsupported_sections(self, parser, tmp_path):
        """Test that unsupported sections are skipped."""
        content = """TITU
Test Title
DOPC IMPR
99999
DBAR
    1  2 A BAR-1       A1000  0.                                            11000
99999
FIM
"""
        test_file = tmp_path / "test.pwf"
        test_file.write_text(content, encoding="utf-8")

        result = parser.parse_file(test_file)

        # Should parse DBAR but skip TITU and DOPC
        assert len(result["DBAR"]) > 0

    def test_empty_file(self, parser, tmp_path):
        """Test parsing empty file."""
        test_file = tmp_path / "empty.pwf"
        test_file.write_text("", encoding="utf-8")

        result = parser.parse_file(test_file)

        assert len(result["DBAR"]) == 0
        assert len(result["DLIN"]) == 0
        assert len(result["DGER"]) == 0

    def test_file_with_only_fim(self, parser, tmp_path):
        """Test file that only contains FIM marker."""
        test_file = tmp_path / "fim_only.pwf"
        test_file.write_text("FIM\n", encoding="utf-8")

        result = parser.parse_file(test_file)

        assert len(result["DBAR"]) == 0
        assert len(result["DLIN"]) == 0
        assert len(result["DGER"]) == 0


class TestDatFileFormatting:
    """Test cases for DAT file formatting."""

    @pytest.fixture
    def sample_parsed_data(self):
        """Sample parsed data for testing DAT formatting."""
        return {
            "DBAR": [
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
                }
            ],
            "DLIN": [
                {
                    "from_bus": "1",
                    "to_bus": "3",
                    "circuit": "1",
                    "resistance": "0.0",
                    "reactance": "5.34",
                    "susceptance": "0.0",
                    "tap": "1.0",
                    "normal_capacity": "300",
                    "state": "L",
                }
            ],
            "DGER": [
                {
                    "number": "1",
                    "min_active_generation": "0.0",
                    "max_active_generation": "650.0",
                }
            ],
        }

    def test_format_dat_file_basic(self, sample_parsed_data):
        """Test basic DAT file formatting."""
        result = _format_dat_file(sample_parsed_data)

        assert isinstance(result, str)
        assert "param BASE := 100;" in result
        assert "param: DBAR:" in result
        assert "param: DLIN:" in result

    def test_format_dat_file_empty_data(self):
        """Test DAT formatting with empty data."""
        empty_data = {"DBAR": [], "DLIN": [], "DGER": []}

        result = _format_dat_file(empty_data)

        assert isinstance(result, str)
        assert "param BASE := 100;" in result

    def test_format_dat_file_missing_sections(self):
        """Test DAT formatting with missing sections."""
        partial_data = {"DBAR": []}

        result = _format_dat_file(partial_data)

        assert isinstance(result, str)
        assert "param BASE := 100;" in result

    def test_voltage_conversion(self, sample_parsed_data):
        """Test voltage conversion from kV to pu."""
        result = _format_dat_file(sample_parsed_data)

        # Voltage should be converted from 1000 to 1.000 (1000/1000)
        assert "1.000" in result

    def test_reactance_conversion(self, sample_parsed_data):
        """Test reactance conversion from % to pu."""
        result = _format_dat_file(sample_parsed_data)

        # Reactance should be converted from 5.34% to 0.0534 pu
        lines = result.split("\n")
        dlin_lines = [
            line
            for line in lines
            if line.strip()
            and not line.startswith("#")
            and not line.startswith("param")
        ]

        # Should find the converted reactance value
        found_reactance = False
        for line in dlin_lines:
            if "0.0534" in line:
                found_reactance = True
                break
        assert found_reactance or "0.0534000" in result


class TestFieldExtraction:
    """Test cases for field extraction logic."""

    def test_extract_field_value_string(self):
        """Test string field extraction."""
        parser = AnaredeParser()
        line = "  1  A  BAR-1    "

        result = parser._extract_field_value(line, 6, 7, str)
        assert result == "A"

    def test_extract_field_value_integer(self):
        """Test integer field extraction."""
        parser = AnaredeParser()
        line = "  123  "

        result = parser._extract_field_value(line, 3, 5, int)
        assert result == 123

    def test_extract_field_value_float(self):
        """Test float field extraction."""
        parser = AnaredeParser()
        line = "  12.34  "

        result = parser._extract_field_value(line, 3, 7, float)
        assert result == 12.34

    def test_extract_field_value_out_of_bounds(self):
        """Test field extraction beyond line length."""
        parser = AnaredeParser()
        line = "short"

        result = parser._extract_field_value(line, 10, 15, str)
        assert result == ""

    def test_extract_field_value_empty_field(self):
        """Test extraction of empty field."""
        parser = AnaredeParser()
        line = "     "

        result = parser._extract_field_value(line, 1, 5, str)
        assert result == ""


if __name__ == "__main__":
    pytest.main([__file__])
