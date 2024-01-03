# src/utils/logger.py
import logging
import datetime


def setup_logger(log_file=None):
    if log_file is None:
        current_datetime = datetime.datetime.now()
        formatted_datetime = current_datetime.strftime("%Y-%m-%d_%H-%M")
        log_file = f"/home/xbankov/COP_analysis/logs/logfile_{formatted_datetime}.log"

    logging.basicConfig(
        filename=log_file,
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    formatter = logging.Formatter("%(levelname)s: %(message)s")
    console_handler.setFormatter(formatter)

    logging.getLogger("").addHandler(console_handler)

    return logging.getLogger(__name__)
