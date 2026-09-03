import logging
import sys

def setup_logging():
    """Configure structured logging for LegalMetriX."""
    log_format = "%(asctime)s [%(levelname)s] [%(name)s] %(message)s"
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    # Quiet noisy third-party loggers
    logging.getLogger("passlib").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)

logger = logging.getLogger("legalmetrix")
