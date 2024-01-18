#!/usr/bin/env python
from scrapers.decision_scraper import DecisionScraper
from utils.logger import setup_logger
from utils.helpers import (
    create_data_folder,
    extract_pdfs,
    download_pdf,
    get_pdf_filename,
)
from tqdm import tqdm
import pandas as pd
import config
import time

logger = setup_logger()


def extract_data(url, current_data_csv, current_html):
    if not current_data_csv.exists():
        scraper = DecisionScraper(url, current_data_csv, current_html)
        scraper.load_and_parse()


def download_files(data, data_path, data_folder):
    for index, row in tqdm(data.iterrows(), total=len(data)):
        was_requested = False
        symbol = row["Symbol"]
        url = row["DownloadUrl"]

        filename = data_folder / get_pdf_filename(symbol)

        if not filename.exists():
            if url == "NOT_ENG" or url == "NO_DOC":
                logger.warning(
                    f"{filename} has no ENG pdf files associated on row: {index}"
                )
            else:
                was_requested = True
                status = download_pdf(url, filename)
                if status != 200:
                    logger.error(f"Request failed with status code: {status}")
                else:
                    status = "Downloaded"

            data.at[index, "DownloadStatus"] = status
            data.to_csv(data_path, index=None)

            # Only wait 10 seconds if request was made (To prevent blocking from the unfccc).
            if was_requested:
                time.sleep(10)


def main():
    # SETUP
    start_time = time.time()
    logger = setup_logger()
    base_data_folder = create_data_folder(config.DEFAULT_DATA_FOLDER)

    # LOAD AND PARSE
    for name, url in config.DECISION_URLS.items():
        data_folder = base_data_folder / name
        data_folder.mkdir(parents=True, exist_ok=True)

        data_path = data_folder / f"{data_folder.name}_{config.DEFAULT_CSV_FILENAME}"
        html_path = data_folder / f"{data_folder.name}_{config.DEFAULT_HTML_FILENAME}"

        extract_data(url, data_path, html_path)

        data = pd.read_csv(data_path)

        end_time = time.time()
        logger.info(
            f"HTML download and URL extraction finished in: {end_time - start_time} seconds"
        )

        # DOWNLOAD
        start_time = time.time()
        download_files(data, data_path, data_folder)
        end_time = time.time()
        elapsed_time = end_time - start_time

        # EXTRACT TEXT
        start_time = time.time()
        extract_pdfs(data, data_path, data_folder)
        end_time = time.time()
        elapsed_time = end_time - start_time

        print(f"Finished in: {elapsed_time} seconds")


if __name__ == "__main__":
    main()
