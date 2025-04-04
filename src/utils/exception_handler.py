import structlog
from structlog.typing import FilteringBoundLogger

from src.utils.qt_error import excepthook

logger: FilteringBoundLogger = structlog.get_logger()


def exception_handler(exception_type, exception, traceback):
    logger.error(
        f"An unhandled exception occurred {exception_type}, {exception}, {traceback}"
    )
    excepthook(exception_type, exception, traceback)
