import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
import structlog

class CustomLogger:
    """
    A logger class that implements structured JSON logging using `structlog`.
    It automatically creates a logs/ directory in the project root and generates timestamp-based 
    log files. It logs to both console and file simultaneously.
    """
    _is_configured = False

    @classmethod
    def configure(cls, level: int = logging.INFO):
        """
        Configures the structlog and standard logging settings.
        """
        if cls._is_configured:
            return

        # Determine project root (this file is in src/logger/)
        project_root = Path(__file__).resolve().parent.parent.parent
        logs_dir = project_root / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now(timezone.utc).strftime("%Y_%m_%d_%H_%M_%S")
        log_file = logs_dir / f"app_{timestamp}.log"

        shared_processors = [
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso", utc=True, key="timestamp"),
            structlog.processors.CallsiteParameterAdder(
                {
                    structlog.processors.CallsiteParameter.FILENAME,
                    structlog.processors.CallsiteParameter.FUNC_NAME,
                    structlog.processors.CallsiteParameter.LINENO,
                }
            ),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
        ]

        structlog.configure(
            processors=shared_processors + [
                structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
            ],
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )

        formatter = structlog.stdlib.ProcessorFormatter(
            processor=structlog.processors.JSONRenderer(),
        )

        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        file_handler.setLevel(level)

        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        console_handler.setLevel(level)

        root_logger = logging.getLogger()
        root_logger.setLevel(level)
        root_logger.handlers.clear()
        root_logger.addHandler(file_handler)
        root_logger.addHandler(console_handler)

        cls._is_configured = True

    @classmethod
    def get_logger(cls, name: str, level: int = logging.INFO) -> structlog.BoundLogger:
        """
        Returns a reusable structlog logger instance.
        """
        if not cls._is_configured:
            cls.configure(level=level)
        
        return structlog.get_logger(name)


def get_logger(name: str, level: int = logging.INFO) -> structlog.BoundLogger:
    """
    Helper function to maintain backwards compatibility and get a logger instance easily.
    """
    return CustomLogger.get_logger(name, level=level)

if __name__ == "__main__":
    logger = get_logger(__name__)
    logger.info("Application started safely.")
    logger.debug("This is a debug message.")
    logger.warning("This is a warning message.")

    logger.info("User logged in", user_id=123, ip_address="192.168.1.1")

    try:
        1 / 0
    except ZeroDivisionError as e:
        logger.error("A division by zero error occurred", exc_info=True, current_action="Math calculation")