#!/usr/bin/env python
from scrapers.decisions_scraper import DecisionScraper
from scrapers.documents_scraper import DocumentScraper
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
    driver.get(url=args.url)

    time.sleep(1)
    if args.tab == "decisions":
        scraper = DecisionScraper(driver, args.progress_csv)
    elif args.tab == "documents":
        scraper = DocumentScraper(driver, args.progress_csv)
    else:
        logger.error(
            f"Unknown type of webpage {args.tab}. Choose either decisions or documents. Exitiing... "
        )
        exit(1)

    scraper.load_all_documents_dynamically()
    scraper.parse_loaded_page()
    scraper.update_progress()
    scraper.report()

    end_time = time.time()
    logger.info(f"Finished in: {end_time - start_time} seconds")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", type=str)
    parser.add_argument("--tab", type=str)
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--progress_csv", type=str)
    parser.add_argument("--driver_path", type=str, default=config.DEFAULT_DRIVER_PATH)

    main(parser.parse_args())
