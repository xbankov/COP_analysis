# src/utils/logger.py
import logging
import datetime
from pathlib import Path


def setup_logger(log_file=None):
    log_path = Path("./logs")
    log_path.mkdir(exist_ok=True)

    if log_file is None:
        current_datetime = datetime.datetime.now()
        formatted_datetime = current_datetime.strftime("%Y-%m-%d_%H-%M")
        log_file = log_path / f"logfile_{formatted_datetime}.log"

    # Check if handlers already exist to avoid duplication
    root_logger = logging.getLogger("")
    if not root_logger.handlers:
        # Configure the root logger only if no handlers are already configured
        logging.basicConfig(
            filename=log_file,
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(filename)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)

        formatter = logging.Formatter("%(levelname)s - %(filename)s: %(message)s")
        console_handler.setFormatter(formatter)

        root_logger.addHandler(console_handler)

    return logging.getLogger(__name__)
