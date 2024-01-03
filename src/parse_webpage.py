# src/parse_table.py
from utils.logger import setup_logger
from utils.helpers import setup_driver
from scrapers.cop_scraper import (
    load_all_documents_dynamically,
    parse_loaded_page,
)
import pandas as pd
import config
import time


def main():
    # SETUP
    start_time = time.time()
    logger = setup_logger()
    url_to_scrape = config.PRODUCTION_URL
    driver = setup_driver(config.DRIVER_PATH, config.HEADLESS)

    # ACTION
    html_content = load_all_documents_dynamically(driver, url_to_scrape)
    documents_metadata = parse_loaded_page(html_content)

    # REPORT
    logger.info(len(documents_metadata))
    df = pd.DataFrame(
        [(doc.title, doc.download_url) for doc in documents_metadata],
        columns=["Title", "Download_URL"],
    )

    df.to_csv(config.METADATA_CSV, index=False)

    end_time = time.time()
    elapsed_time = end_time - start_time
    logger.info(f"Finished in: {elapsed_time} seconds")


if __name__ == "__main__":
    main()
