#!/usr/bin/env python
from scrapers.decision_scraper import DecisionScraper
from utils.logger import setup_logger
from utils.helpers import (
    create_data_folder,
    download_files,
    extract_pdfs,
)
import pandas as pd
import config
import time

logger = setup_logger()


def scrape_url(url, current_data_csv, current_html):
    if not current_data_csv.exists() or config.FORCE["PARSE"]:
        scraper = DecisionScraper(url, current_data_csv, current_html)
        scraper.load_and_download_html()
        scraper.parse()


def main():
    logger.info("##########################################")
    logger.info("############ DOWNLOAD DECISIONS  #########")
    logger.info("##########################################")

    base_data_folder = create_data_folder(config.DEFAULT_DATA_FOLDER)

    for name, url in config.DECISION_URLS.items():
        data_folder = base_data_folder / name
        data_folder.mkdir(parents=True, exist_ok=True)

        data_path = data_folder / f"{data_folder.name}_{config.DEFAULT_CSV_FILENAME}"
        html_path = data_folder / f"{data_folder.name}_{config.DEFAULT_HTML_FILENAME}"

        # SCRAPE
        start_time = time.time()
        scrape_url(url, data_path, html_path)
        end_time = time.time()
        logger.info(f"Scraping URL finished in: {end_time - start_time} seconds")
        data = pd.read_csv(data_path)

        # DOWNLOAD
        start_time = time.time()
        download_files(data, data_path, data_folder, "Symbol")
        end_time = time.time()
        logger.info(f"Downloading files finished in: {end_time - start_time} seconds")

        # EXTRACT TEXT
        start_time = time.time()
        extract_pdfs(data, data_path, data_folder, "Symbol")
        end_time = time.time()
        logger.info(
            f"Text extraction from PDF finished in: {end_time - start_time} seconds"
        )


if __name__ == "__main__":
    main()
