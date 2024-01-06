# src/extract_links.py
from scrapers.decisions_scraper import DecisionScraper
from utils.logger import setup_logger
from utils.helpers import setup_driver
import config
import time
import argparse


def main(args):
    # SETUP
    start_time = time.time()
    logger = setup_logger()
    driver = setup_driver(args.driver_path, args.headless)

    # ACTION
    # TODO Robot detection
    # TODO Scraper Selection
    # TODO WebPage changes
    driver.get(url=args.url)
    
    scraper = DecisionScraper(driver, args.progress_csv)
    scraper.load_all_documents_dynamically()
    scraper.parse_loaded_page()
    scraper.update_progress()

    end_time = time.time()
    logger.info(f"Finished in: {end_time - start_time} seconds")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", type=str, default=config.DEFAULT_URL)
    parser.add_argument(
        "--headless",
        action="store_true",
        default=config.DEFAULT_HEADLESS,
    )
    parser.add_argument("--driver_path", type=str, default=config.DEFAULT_DRIVER_PATH)
    parser.add_argument(
        "--progress_csv", type=str, default=config.DEFAULT_PROGRESS_CSV_PATH
    )

    main(parser.parse_args())
