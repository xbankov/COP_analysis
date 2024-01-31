# src/utils/logger.py
from cgitb import handler
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
    root_logger.setLevel(logging.DEBUG)

    if not root_logger.handlers:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            "%(asctime)s - %(levelname)s - %(filename)s: %(message)s"
        )
        file_handler.setFormatter(file_formatter)

        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(
            "%(levelname)s - %(filename)s: %(message)s"
        )
        console_handler.setFormatter(console_formatter)

        root_logger.addHandler(console_handler)
        root_logger.addHandler(file_handler)

    return root_logger
