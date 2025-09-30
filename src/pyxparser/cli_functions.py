"""CLI helper functions."""

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict
from loguru import logger

from .__version__ import __version__


def base_cli() -> argparse.ArgumentParser:
    """Create parser object for CLI."""
    parser = argparse.ArgumentParser(
        description="Parse ANAREDE electrical power system files",
        add_help=True,
        prog="pyxparser",
    )

    parser.add_argument(
        "-i",
        "--input",
        required=True,
        type=str,
        help="Path to the PWF/ANAREDE input file to parse",
    )

    parser.add_argument(
        "-o",
        "--output",
        type=str,
        help="Output file path (optional, defaults to stdout)",
    )

    parser.add_argument(
        "-f",
        "--format",
        choices=["json", "csv", "yaml", "dat"],
        default="json",
        help="Output format (default: json). 'dat' format is for modeling.",
    )

    parser.add_argument(
        "--verbose",
        "-v",
        action="count",
        default=0,
        help="Run with additional verbosity (can be used multiple times: -v, -vv, -vvv)",
    )

    parser.add_argument("--log-file", type=str, help="Path to log file (optional)")

    parser.add_argument(
        "--version", "-V", action="version", version=f"pyxparser version: {__version__}"
    )

    return parser


def handle_output(result: Dict[str, Any], args: argparse.Namespace) -> None:
    """Handle output formatting and saving.

    Args:
        result: Parsed data dictionary
        args: CLI arguments namespace
    """
    from loguru import logger

    if args.output:
        output_path = Path(args.output)

        # Save to file based on format
        if args.format == "json":
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2)
            logger.success(f"Results saved as JSON: {output_path}")
        elif args.format == "csv":
            # TODO: Implement CSV export
            raise NotImplementedError("CSV format not yet implemented")
        elif args.format == "yaml":
            # TODO: Implement YAML export
            raise NotImplementedError("YAML format not yet implemented")
        elif args.format == "dat":
            _write_dat_file(result, output_path)
            logger.success(f"Results saved as DAT: {output_path}")

    else:
        # Print to stdout
        if args.format == "json":
            print(json.dumps(result, indent=2))
        elif args.format == "dat":
            _print_dat_format(result)
        else:
            # For other formats, default to JSON when printing to stdout
            print(json.dumps(result, indent=2))


def _print_dat_format(result: Dict[str, Any]) -> None:
    """Print data in .dat format to stdout.

    Args:
        result: Parsed data dictionary
    """
    print(_format_dat_file(result))


def _write_dat_file(result: Dict[str, Any], output_path: Path) -> None:
    """Write data in .dat format to file.

    Args:
        result: Parsed data dictionary
        output_path: Path to output file
    """
    try:
        # Create output directory if it doesn't exist
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(_format_dat_file(result))

        logger.success(f"Successfully wrote .dat file: {output_path}")

    except Exception as e:
        logger.error(f"Error writing .dat file {output_path}: {e}")
        raise


def _format_dat_file(result: Dict[str, Any]) -> str:
    """Format data as .dat file content.

    Args:
        result: Parsed data dictionary

    Returns:
        String in .dat format
    """
    dat_content = []

    # System base power
    dat_content.append("# System base power")
    dat_content.append("param BASE := 100;\n")

    # Process DBAR data (buses)
    if "DBAR" in result and result["DBAR"]:
        buses = result["DBAR"]

        dat_content.append("# Bus data")
        dat_content.append(
            "param: DBAR:       Name Tb   Are    V0      A0      Pg0      Qg0       Pgm      Pgn        Qgm        Qgn       Pl       Ql      Bsh     Vmx     Vmn    :="
        )
        dat_content.append(
            "#                                 [pu]  [grau]     [MW]   [MVAr]      [MW]     [MW]     [MVAr]     [MVAr]     [MW]   [MVAr]     [pu]    [pu]    [pu]      "
        )

        for bus in buses:
            if bus.get("state", "L") == "L":  # Only connected buses
                # Extract values with defaults
                num = bus.get("number", 0)
                name = bus.get("name", "").strip()[:12]  # Truncate to 12 chars
                tb = bus.get("type", 0)
                area = bus.get("area", 1)
                v0 = bus.get("voltage", 1.0)
                a0 = bus.get("angle", 0.0)
                pg0 = bus.get("active_generation", 0.0)
                qg0 = bus.get("reactive_generation", 0.0)
                pgm = (
                    bus.get("reactive_generation_max", 0.0)
                    if bus.get("reactive_generation_max")
                    else 0.0
                )
                pgn = (
                    bus.get("reactive_generation_min", 0.0)
                    if bus.get("reactive_generation_min")
                    else 0.0
                )
                qgm = 300.0 if tb > 0 else 0.0  # Reactive limits for generators
                qgn = -300.0 if tb > 0 else 0.0  # Reactive limits for generators
                pl = bus.get("active_load", 0.0)
                ql = bus.get("reactive_load", 0.0)
                bsh = bus.get("capacitor_reactor", 0.0) / 100.0  # Convert to pu
                vmx = 1.100  # Default max voltage
                vmn = 0.950  # Default min voltage

                # Format the line according to the desired output format
                line = f'{num:8} "{name:12}" {tb:2} {area:3} {v0:7.3f} {a0:8.2f} {pg0:8.3f} {qg0:8.3f} {pgm:8.2f} {pgn:8.2f} {qgm:10.2f} {qgn:10.2f} {pl:8.3f} {ql:8.3f} {bsh:8.4f} {vmx:7.3f} {vmn:7.3f}'
                dat_content.append(line)

        dat_content.append(";\n")

    # Process DLIN data (lines)
    if "DLIN" in result and result["DLIN"]:
        lines = result["DLIN"]

        dat_content.append("# AC circuits data (LTs and Transfos)")
        dat_content.append(
            "param: DLIN:       Tr         R          X       Bshl     Tap     Tmx     Tmn      Psh        Cn     :="
        )
        dat_content.append(
            "#    k     i     j          [pu]       [pu]       [pu]                           [grau]    [MVA]                     "
        )

        for idx, line_data in enumerate(lines, 1):
            if line_data.get("state", "L") == "L":  # Only connected lines
                # Extract values with defaults
                from_bus = line_data.get("from_bus", 0)
                to_bus = line_data.get("to_bus", 0)
                tr = int(line_data.get("circuit", 1))
                r = line_data.get("resistance", 0.0) / 100.0  # Convert % to pu
                x = line_data.get("reactance", 0.0) / 100.0  # Convert % to pu
                bshl = line_data.get("susceptance", 0.0) / 100.0  # Convert to pu
                tap = line_data.get("tap", 1.0) if line_data.get("tap") else 1.0
                tmx = (
                    line_data.get("tap_maximum", 0.0)
                    if line_data.get("tap_maximum")
                    else 0.0
                )
                tmn = (
                    line_data.get("tap_minimum", 0.0)
                    if line_data.get("tap_minimum")
                    else 0.0
                )
                psh = line_data.get("phase_shift", 0.0)
                cn = (
                    line_data.get("normal_capacity", 99999.0)
                    if line_data.get("normal_capacity")
                    else 99999.0
                )

                # Format the line according to the desired output format
                line_str = f"{idx:6d} {from_bus:5d} {to_bus:5d} {tr:2d} {r:10.7f} {x:10.7f} {bshl:10.7f} {tap:7.4f} {tmx:7.4f} {tmn:7.4f} {psh:8.3f} {cn:8.2f}"
                dat_content.append(line_str)

        dat_content.append(";\n")

    return "\n".join(dat_content)


def validate_input_file(file_path: str) -> Path:
    """Validate that input file exists.

    Args:
        file_path: Path to the input file

    Returns:
        Path object for the validated file

    Raises:
        SystemExit: If file doesn't exist
    """
    pwf_path = Path(file_path)
    if not pwf_path.exists():
        print(f"Error: File '{pwf_path}' does not exist.", file=sys.stderr)
        sys.exit(1)
    return pwf_path
