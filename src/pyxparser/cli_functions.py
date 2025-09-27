"""CLI helper functions."""

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict

from .__version__ import __version__


def base_cli() -> argparse.ArgumentParser:
    """Create parser object for CLI."""
    parser = argparse.ArgumentParser(
        description="Parse ANAREDE electrical power system files",
        add_help=True,
        prog="pyxparser",
    )

    parser.add_argument(
        "pwf_file", type=str, help="Path to the PWF/ANAREDE file to parse"
    )

    parser.add_argument("-o", "--output", type=str, help="Output file path (optional)")

    parser.add_argument(
        "-f",
        "--format",
        choices=["json", "csv", "yaml"],
        default="json",
        help="Output format (default: json)",
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
    if args.output:
        output_path = Path(args.output)

        # Save to file based on format
        if args.format == "json":
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2)
        elif args.format == "csv":
            # TODO: Implement CSV export
            raise NotImplementedError("CSV format not yet implemented")
        elif args.format == "yaml":
            # TODO: Implement YAML export
            raise NotImplementedError("YAML format not yet implemented")

        if args.verbose:
            print(f"Results saved to: {output_path}")
    else:
        # Print to stdout
        if args.format == "json":
            print(json.dumps(result, indent=2))
        else:
            # For other formats, default to JSON when printing to stdout
            print(json.dumps(result, indent=2))


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
