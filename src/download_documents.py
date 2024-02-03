#!/usr/bin/env python
from scrapers.document_scraper import DocumentScraper

from utils.logger import setup_logger
from utils.helpers import (
    download_files,
    extract_pdfs,
    init_dirs,
    scrape_url,
    translate_pdfs,
)
import config
import time

logger = setup_logger()


def main():
    for name, url in config.DOCUMENT_URLS.items():
        logger.info("##########################################")
        logger.info(f"###### DOWNLOAD DOCUMENTS: {name} #######")
        logger.info(f"###### DOWNLOAD URL: {url} ##############")
        logger.info("##########################################")
        data_dir, pdfs_dir, txts_dir = init_dirs(name)
        csv_path = data_dir / f"{data_dir.name}_{config.DEFAULT_CSV_FILENAME}"
        html_path = data_dir / f"{data_dir.name}_{config.DEFAULT_HTML_FILENAME}"

        logger.info("##########################################")
        logger.info("############ SCRAPE ######################")
        logger.info("##########################################")
        start_time = time.time()
        scrape_url(url, csv_path, html_path, DocumentScraper)
        end_time = time.time()
        logger.info(f"Scraping URL finished in: {end_time - start_time} seconds")

        logger.info("##########################################")
        logger.info("############ DOWNLOAD ####################")
        logger.info("##########################################")
        start_time = time.time()
        download_files(csv_path, pdfs_dir, filename_column="DocumentName")
        end_time = time.time()
        logger.info(f"Downloading files finished in: {end_time - start_time} seconds")

        logger.info("##########################################")
        logger.info("############ EXTRACT PDF #################")
        logger.info("##########################################")
        start_time = time.time()
        extract_pdfs(csv_path, pdfs_dir, txts_dir, "DocumentName")
        end_time = time.time()
        logger.info(
            f"Text extraction from PDF finished in: {end_time - start_time} seconds"
        )

        logger.info("##########################################")
        logger.info("############ Translate #################")
        logger.info("##########################################")
        start_time = time.time()
        # translate_pdfs(csv_path, txts_dir)
        end_time = time.time()
        logger.info(
            f"Text extraction from PDF finished in: {end_time - start_time} seconds"
        )


if __name__ == "__main__":
    main()
