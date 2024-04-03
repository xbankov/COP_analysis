#!/usr/bin/env python
import config
from scrapers.decision_scraper import DecisionScraper
from utils.helpers import (csv2json, detailview, download_pdfs, extract_pdfs,
                           init_dirs, scrape_url)
from utils.logger import setup_logger
from utils.translation import translate_pdfs

logger = setup_logger()


def main():
    for name, url in config.DECISION_URLS.items():

        logger.info(f"###### DOWNLOAD DECISIONS: {name} #######")
        logger.info(f"###### DOWNLOAD URL: {url} ##############")

        data_dir, pdfs_dir, json_dir = init_dirs(name)
        csv_path = data_dir / f"{data_dir.name}_{config.DEFAULT_CSV_FILENAME}"
        html_path = data_dir / f"{data_dir.name}_{config.DEFAULT_HTML_FILENAME}"

        logger.info("############## SCRAPE HTML ###############")
        scrape_url(url, csv_path, html_path, DecisionScraper)

        logger.info("############## CSV2JSON ###############")
        csv2json(csv_path, json_dir)

        logger.info("############## ADD_DETAIL_VIEW_TO_JSON ###############")
        detailview(json_dir)

        logger.info("############ DOWNLOAD PDF ################")
        download_pdfs(csv_path, pdfs_dir)

        logger.info("############ EXTRACT PDF #################")
        extract_pdfs(csv_path, json_dir, pdfs_dir)

        logger.info("############ TRANSLATE #################")
        translate_pdfs(csv_path, json_dir)


if __name__ == "__main__":
    main()
