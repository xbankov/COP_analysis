# src/download_pdf.py
from tqdm import tqdm
from pathlib import Path
import config
import pandas as pd
import time

from utils.helpers import download_pdf, setup_logger

logger = setup_logger()


def main():
    # SETUP
    start_time = time.time()

    if not Path(config.DEFAULT_PROGRESS_CSV_PATH).exists():
        logger.error("There is no progress csv with links to download")
        exit(1)

    progress_csv = pd.read_csv(config.DEFAULT_PROGRESS_CSV_PATH)
    not_downloaded = progress_csv[progress_csv["Status"] != "Downloaded"]

    for index, row in tqdm(not_downloaded.iterrows(), total=len(not_downloaded)):
        symbol = row["Symbol"]
        document_name = row["DocumentName"]
        url = row["DownloadUrl"]

        filename = Path(config.DEFAULT_PDF_PATH) / f"{symbol}_{document_name}.pdf"

        try:
            status = download_pdf(url, filename)
            if status != 200:
                logger.warn(f"Request failed with status code: {status}")
            if status == 200:
                status = "Downloaded"
            
        except Exception as e:
            logger.warn(e)
        progress_csv.iloc[index]["Status"] = status
        progress_csv.to_csv(config.DEFAULT_PROGRESS_CSV_PATH, index=None)

        time.sleep(10)

    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"Finished in: {elapsed_time} seconds")


if __name__ == "__main__":
    main()
