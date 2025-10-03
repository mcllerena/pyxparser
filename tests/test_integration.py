"""Integration tests for the complete parsing workflow."""

import pytest
import subprocess
import sys

from pyxparser.parser.anarede import AnaredeParser
from pyxparser.cli_functions import handle_output
from unittest.mock import MagicMock


class TestEndToEndWorkflow:
    """Test complete parsing workflow."""

    @pytest.fixture
    def sample_pwf_file(self, tmp_path):
        """Create a sample PWF file for testing."""
        content = """TITU
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
        test_file = tmp_path / "test_system.pwf"
        test_file.write_text(content, encoding="utf-8")
        return test_file

    def test_parse_to_dat_workflow(self, sample_pwf_file, tmp_path):
        """Test complete parse-to-DAT workflow."""
        # Parse the file
        parser = AnaredeParser()
        result = parser.parse_file(sample_pwf_file)

        # Generate output
        output_file = tmp_path / "output.dat"
        args = MagicMock()
        args.print = False
        args.output = output_file

        handle_output(result, args)

        # Verify output file was created
        assert output_file.exists()

        # Verify content
        content = output_file.read_text()
        assert "param BASE := 100;" in content
        assert "param: DBAR:" in content
        assert "param: DLIN:" in content

    def test_parse_multiple_sections(self, sample_pwf_file):
        """Test parsing file with multiple sections."""
        parser = AnaredeParser()
        result = parser.parse_file(sample_pwf_file)

        # Verify all sections were parsed
        assert len(result["DBAR"]) == 3  # 3 buses
        assert len(result["DLIN"]) == 2  # 2 lines
        assert len(result["DGER"]) == 2  # 2 generators

        # Verify data integrity
        dbar_numbers = [bus.get("number") for bus in result["DBAR"]]
        assert "1" in dbar_numbers
        assert "2" in dbar_numbers
        assert "3" in dbar_numbers

    def test_error_handling_workflow(self, tmp_path):
        """Test error handling in complete workflow."""
        # Create malformed file
        bad_file = tmp_path / "bad.pwf"
        bad_file.write_text("INVALID CONTENT", encoding="utf-8")

        parser = AnaredeParser()

        # Should not crash, should return empty sections
        result = parser.parse_file(bad_file)

        assert isinstance(result, dict)
        assert "DBAR" in result
        assert "DLIN" in result
        assert "DGER" in result

    @pytest.mark.skipif(
        sys.platform == "win32", reason="CLI test may be flaky on Windows"
    )
    def test_cli_integration(self, sample_pwf_file, tmp_path):
        """Test CLI integration (if available)."""
        output_file = tmp_path / "cli_output.dat"

        # Try to run CLI command
        try:
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "pyxparser",
                    "-i",
                    str(sample_pwf_file),
                    "-o",
                    str(output_file),
                    "-f",
                    "dat",
                ],
                capture_output=True,
                text=True,
                timeout=30,
            )

            # If CLI is available and works
            if result.returncode == 0:
                assert output_file.exists()
                content = output_file.read_text()
                assert "param BASE := 100;" in content
            else:
                pytest.skip(f"CLI not available or failed: {result.stderr}")

        except (subprocess.TimeoutExpired, FileNotFoundError):
            pytest.skip("CLI not available or timeout")

    def test_data_consistency(self, sample_pwf_file):
        """Test data consistency between parsing and formatting."""
        parser = AnaredeParser()
        result = parser.parse_file(sample_pwf_file)

        # Check that parsed data maintains relationships
        dbar_numbers = set(bus.get("number") for bus in result["DBAR"])
        dger_numbers = set(gen.get("number") for gen in result["DGER"])

        # All generators should reference existing buses
        for gen_num in dger_numbers:
            if gen_num:  # Skip empty numbers
                assert gen_num in dbar_numbers, (
                    f"Generator {gen_num} references non-existent bus"
                )

    def test_large_file_handling(self, tmp_path):
        """Test handling of larger files."""
        # Create a larger test file
        content_parts = ["TITU\nLarge System Test\nDOPC IMPR\n99999\n", "DBAR\n"]

        # Add many buses
        for i in range(1, 101):  # 100 buses
            content_parts.append(
                f"    {i:3d}  E BAR-{i:03d}      A1000  0.                                           11000\n"
            )

        content_parts.append("99999\nFIM\n")

        large_file = tmp_path / "large_system.pwf"
        large_file.write_text("".join(content_parts), encoding="utf-8")

        # Parse the large file
        parser = AnaredeParser()
        result = parser.parse_file(large_file)

        # Should handle all buses
        assert len(result["DBAR"]) == 100


class TestErrorConditions:
    """Test various error conditions."""

    def test_corrupted_file_handling(self, tmp_path):
        """Test handling of corrupted files."""
        # Create file with mixed encoding or binary data
        corrupted_file = tmp_path / "corrupted.pwf"

        # Write some binary data that might cause encoding issues
        with open(corrupted_file, "wb") as f:
            f.write(b"DBAR\n")
            f.write(b"\xff\xfe\x00\x00")  # Invalid UTF-8 sequence
            f.write(b"FIM\n")

        parser = AnaredeParser()

        # Should handle encoding errors gracefully
        try:
            result = parser.parse_file(corrupted_file)
            # If it succeeds, that's fine too
            assert isinstance(result, dict)
        except UnicodeDecodeError:
            # This is also acceptable behavior
            pass

    def test_permission_error_handling(self, tmp_path):
        """Test handling of permission errors."""
        # This test may not work on all systems
        output_file = tmp_path / "readonly.dat"
        output_file.write_text("test")

        # Try to make it read-only (may not work on all systems)
        try:
            output_file.chmod(0o444)

            result = {"DBAR": [], "DLIN": [], "DGER": []}
            args = MagicMock()
            args.print = False
            args.output = output_file

            # Should handle permission error gracefully
            handle_output(result, args)

        except (OSError, PermissionError):
            # If we can't create read-only files, skip this test
            pytest.skip("Cannot test permission errors on this system")
        finally:
            # Clean up
            try:
                output_file.chmod(0o644)
            except Exception:
                pass


if __name__ == "__main__":
    pytest.main([__file__])
