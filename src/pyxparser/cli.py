"""CLI entry point for pyxparser."""

from .cli_functions import base_cli
from .logger import setup_logging
from .runner import run_parser


def main() -> None:
    """Main CLI entry point."""
    parser = base_cli()
    args = parser.parse_args()

    # Setup logging based on verbosity
    setup_logging(filename=args.log_file, verbosity=args.verbose)

    # Run the parser
    run_parser(args)


if __name__ == "__main__":
    main()
