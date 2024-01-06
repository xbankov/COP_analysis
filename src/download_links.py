# src/download_pdf.py
from src.scrapers.decisions_scraper import (
    download_all_pdfs,
)
from pathlib import Path
import config
import pandas as pd
import time

from utils.helpers import Document


def main():
    # SETUP
    start_time = time.time()
    metadata_df = pd.read_csv(config.METADATA_CSV)

    # ACTION
    documents_metadata = [
        Document(title, url)
        for title, url in zip(metadata_df["Title"], metadata_df["Download_URL"])
    ]
    status_l = download_all_pdfs(documents_metadata, Path(config.PDF_DOWNLOAD_PATH))

    # REPORT
    metadata_df["Status"] = status_l

    # Add a new column 'Is_200' with True for status 200 and False for other statuses
    metadata_df["Downloaded"] = metadata_df["Status"] == 200

    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"Finished in: {elapsed_time} seconds")


if __name__ == "__main__":
    main()
