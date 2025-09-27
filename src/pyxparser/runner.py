"""Parser runner functions."""

import argparse
import sys

from loguru import logger

from .parser.anarede import AnaredeParser
from .cli_functions import handle_output, validate_input_file


def run_parser(args: argparse.Namespace) -> None:
    """Run the ANAREDE parser with given arguments.

    Args:
        args: CLI arguments namespace
    """
    # Validate input file exists
    pwf_path = validate_input_file(args.pwf_file)

    try:
        logger.info(f"Starting to parse file: {pwf_path}")

        anarede_parser = AnaredeParser()
        result = anarede_parser.parse_file(pwf_path)

        # Handle output
        handle_output(result, args)

        logger.success(f"Successfully completed parsing: {pwf_path}")

    except Exception as e:
        logger.error(f"Error parsing file: {e}")
        sys.exit(1)
