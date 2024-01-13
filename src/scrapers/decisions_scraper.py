# src/scrapers/scraper1.py
from urllib.parse import urljoin
import bs4
import pandas as pd
from scrapers.scraper import Scraper
from scrapers.parsing import get_eng_url_from_td, parse_date, parse_text
from utils.logger import setup_logger
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select


logger = setup_logger()


class DecisionScraper(Scraper):
    def __init__(self, driver, progress_csv):
        super().__init__(driver, progress_csv)
        self.button_id = "edit-items-per-page--3"
        self.total_span_class = "div.block-views-blockdecisions-block-1"

    def parse_loaded_page(self):
        soup = bs4.BeautifulSoup(self.html_content, "lxml")
        documents = soup.find_all("tr")[1:]
        logger.info(f"Number of TR elements {len(documents)}")

        # Using a list comprehension to create download_progress directly
        self.download_progress = pd.DataFrame(
            [
                {
                    "Symbol": parse_text(cols[0].getText()),
                    "DocumentName": parse_text(cols[1].getText()),
                    "Body": parse_text(cols[2].getText()),
                    "Date": parse_date(cols[3].getText()),
                    "DownloadUrl": get_eng_url_from_td(cols[4]),
                    "DocumentUrl": urljoin(self.base_url, cols[4].find("a")["href"]),
                    "DownloadStatus": "Not Downloaded",
                }
                for document in documents
                for cols in [document.find_all("td")]
            ]
        )

    def update_progress(self):
        if not self.progress_csv.parent.exists():
            self.progress_csv.parent.mkdir(exist_ok=True, parents=True)
        if not self.progress_csv.exists():
            df = pd.DataFrame(
                columns=[
                    "Symbol",
                    "DocumentName",
                    "Body",
                    "Date",
                    "DownloadStatus",
                    "DownloadUrl",
                    "DocumentUrl",
                ]
            )
            df.to_csv(self.progress_csv, index=None)

        df1 = pd.read_csv(self.progress_csv)
        df2 = self.download_progress

        # Identify the columns to keep
        common_columns = ["Symbol", "DocumentName", "Body", "Date", "DocumentUrl"]

        # Merge df2 into df1 based on the unique identifier columns
        merged_df = pd.merge(
            df1,
            df2,
            on=common_columns,
            how="outer",
            suffixes=("_df1", "_df2"),
            indicator=True,
        )

        result_df = pd.DataFrame(
            {
                "Symbol": merged_df["Symbol"],
                "DocumentName": merged_df["DocumentName"],
                "Date": merged_df["Date"],
                "Body": merged_df["Body"],
                "DocumentUrl": merged_df["DocumentUrl"],
                "DownloadStatus": merged_df["DownloadStatus_df1"].fillna(
                    merged_df["DownloadStatus_df2"]
                ),
                "DownloadUrl": merged_df["DownloadUrl_df1"].fillna(
                    merged_df["DownloadUrl_df2"]
                ),
            }
        )
        result_df.to_csv(self.progress_csv, index=None)
