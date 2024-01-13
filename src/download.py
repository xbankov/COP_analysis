#!/usr/bin/env python

import argparse
from tqdm import tqdm
from pathlib import Path
import pandas as pd
import time

from utils.helpers import download_pdf, get_filename, setup_logger

logger = setup_logger()


def main(args):
    # SETUP
    start_time = time.time()

    if not Path(args.progress_csv).exists():
        logger.error("There is no progress csv with links to download. Run extract.py")
        exit(1)

    progress_csv = pd.read_csv(args.progress_csv)

    for index, row in tqdm(progress_csv.iterrows(), total=len(progress_csv)):
        was_requested = False
        symbol = row["Symbol"]
        document_name = row["DocumentName"]
        url = row["DownloadUrl"]

        filename = Path(args.data_folder) / get_filename(symbol, document_name)

        if url == "NOT_ENG" or url == "NO_DOC":
            logger.warning(
                f"{filename} has no ENG pdf files associated on row: {index}"
            )

        else:
            if Path(filename).exists() or row["DownloadStatus"] == "Downloaded":
                status = "Downloaded"
            else:
                try:
                    was_requested = True
                    status = download_pdf(url, filename)
                    if status != 200:
                        logger.error(f"Request failed with status code: {status}")

                except Exception as e:
                    logger.error(e)

            progress_csv.iloc[index]["DownloadStatus"] = status
            progress_csv.to_csv(args.progress_csv, index=None)

        # Only wait 10 seconds if request was made (To prevent blocking from the unfccc).
        if was_requested:
            time.sleep(10)

    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"Finished in: {elapsed_time} seconds")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--tab", type=str)
    parser.add_argument("--progress_csv", type=str)
    parser.add_argument("--data_folder", type=str)

    main(parser.parse_args())
