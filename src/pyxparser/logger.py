"""pyxparser logger configuration."""

# System packages
import argparse
import os
import sys

# Third-party packages
from loguru import logger

# Logger printing formats
DEFAULT_FORMAT = "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level>| <cyan>{name}:{line}{extra[padding]}</cyan> | {message}\n{exception}"


class Formatter:  # noqa: D101
    def __init__(self):
        self.padding = 0
        self.fmt = "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level>| <cyan>{name}:{line}{extra[padding]}</cyan> | {message}\n{exception}"  # noqa: E501

    def format(self, record):  # noqa: D102
        length = len("{name}:{line}".format(**record))
        self.padding = max(self.padding, length)
        record["extra"]["padding"] = " " * (self.padding - length)
        return self.fmt


def setup_logging(
    filename=None,
    level="INFO",
    verbosity: int = 0,
):
    """Configure logging of file.

    Parameters
    ----------
    filename : str | None
        log filename
    level : str, optional
        change default level of logging.
    verbosity : int
        returns additional logging information.
    """
    match verbosity:
        case 0:
            level = "SUCCESS"
        case 1:
            level = "INFO"
        case 2:
            level = "DEBUG"
        case 3:
            level = "TRACE"
        case _:
            msg = "Verbosity level not supported"
            raise NotImplementedError(msg)

    from loguru import logger

    logger.remove()
    logger.enable("pyxparser")

    level = os.environ.get("LOGURU_LEVEL", level)

    # Always use the detailed format with timestamps and module info
    formatter = Formatter()
    logger.add(
        sys.stderr,
        level=level,
        enqueue=False,
        format=formatter.format,
    )
    if filename:
        logger.add(filename, level=level, enqueue=True, format=formatter.format)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args()

    setup_logging(level="TRACE")

    # Testing different types of loggers.
    logger.trace("A trace message.")
    logger.debug("A debug message.")
    logger.info("An info message.")
    logger.success("A success message.")
    logger.warning("A warning message.")
    logger.error("An error message.")
    logger.critical("A critical message.")
