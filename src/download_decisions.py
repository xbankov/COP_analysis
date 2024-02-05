#!/usr/bin/env python
from scrapers.decision_scraper import DecisionScraper
from utils.logger import setup_logger
from utils.helpers import (
    download_pdfs,
    extract_pdfs,
    init_dirs,
    scrape_url,
    translate_pdfs,
)
import config
import time

logger = setup_logger()


def main():
    for name, url in config.DECISION_URLS.items():
        logger.info("##########################################")
        logger.info(f"###### DOWNLOAD DECISIONS: {name} #######")
        logger.info(f"###### DOWNLOAD URL: {url} ##############")
        logger.info("##########################################")
        data_dir, pdfs_dir, txts_dir, eng_txts_dir = init_dirs(name)
        csv_path = data_dir / f"{data_dir.name}_{config.DEFAULT_CSV_FILENAME}"
        html_path = data_dir / f"{data_dir.name}_{config.DEFAULT_HTML_FILENAME}"

        logger.info("##########################################")
        logger.info("############ SCRAPE ######################")
        logger.info("##########################################")
        start_time = time.time()
        scrape_url(url, csv_path, html_path, DecisionScraper)
        end_time = time.time()
        logger.info(f"Scraping URL finished in: {end_time - start_time} seconds")

        logger.info("##########################################")
        logger.info("############ DOWNLOAD ####################")
        logger.info("##########################################")
        start_time = time.time()
        download_pdfs(csv_path, pdfs_dir, filename_column="Symbol")
        end_time = time.time()
        logger.info(f"Downloading files finished in: {end_time - start_time} seconds")

        logger.info("##########################################")
        logger.info("############ EXTRACT PDF #################")
        logger.info("##########################################")
        start_time = time.time()
        extract_pdfs(csv_path, pdfs_dir, txts_dir, "Symbol")
        end_time = time.time()
        logger.info(
            f"Text extraction from PDF finished in: {end_time - start_time} seconds"
        )

        logger.info("##########################################")
        logger.info("############ Translate #################")
        logger.info("##########################################")
        start_time = time.time()
        translate_pdfs(csv_path, txts_dir, eng_txts_dir, "Symbol")
        end_time = time.time()
        logger.info(
            f"Text extraction from PDF finished in: {end_time - start_time} seconds"
        )


if __name__ == "__main__":
    main()
