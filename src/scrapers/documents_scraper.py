# src/scrapers/scraper1.py
from genericpath import exists
import bs4
import pandas as pd
from scrapers.scraper import Scraper
from utils.logger import setup_logger
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
import time


logger = setup_logger()


class DocumentScraper(Scraper):
    def __init__(self, driver, progress_csv):
        super().__init__(driver, progress_csv)

    def load_all_documents_dynamically(self):
        try:
            driver = self.driver
            items_per_page_button = driver.find_element(By.ID, "edit-items-per-page--4")
            select = Select(items_per_page_button)
            last_index = len(select.options) - 1
            select.select_by_index(last_index)

            self.wait_for_loading()

            total_documents = int(
                driver.find_element(
                    By.CSS_SELECTOR,
                    "div.block-views-blockdocuments-block-1 span.totalresults",
                ).text
            )
            shown_documents = int(
                driver.find_element(
                    By.CSS_SELECTOR,
                    "div.block-views-blockdocuments-block-1 span.endresults",
                ).text
            )

            while shown_documents < total_documents:
                logger.info(f"{shown_documents}/{total_documents}")

                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(3)

                load_more_button = driver.find_element(
                    By.CSS_SELECTOR,
                    'div.block-views-blockdocuments-block-1  a.button[title="Load more items"]',
                )
                load_more_button.click()

                self.wait_for_loading()

                shown_documents = int(
                    driver.find_element(
                        By.CSS_SELECTOR,
                        "div.block-views-blockdocuments-block-1 span.endresults",
                    ).text
                )
            logger.info("All documents loaded")
            self.html_content = driver.page_source
        finally:
            driver.quit()

    def parse_loaded_page(self):
        soup = bs4.BeautifulSoup(self.html_content, "lxml")
        documents = soup.find_all("tr")[1:]
        logger.info(f"Number of TR elements {len(documents)}")
        documents[0].find_all("td")[4].getText().strip().replace("/", "_")
        # Using a list comprehension to create download_progress directly
        self.download_progress = pd.DataFrame(
            [
                {
                    "Symbol": cols[0].getText().strip().replace("/", "_"),
                    "DocumentName": cols[1]
                    .getText()
                    .strip()
                    .replace(" ", "_")
                    .replace("/", "_"),
                    "DocumentType": cols[2].getText().strip().replace(" ", "_"),
                    "Date": cols[3].getText().strip().replace(" ", "."),
                    "DownloadUrl": self.get_eng_url_from_td(cols[4]),
                    "DownloadStatus": "Not Downloaded",
                    "UploadStatus": "Not Uploaded",
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
                    "DocumentType",
                    "Date",
                    "DownloadStatus",
                    "UploadStatus",
                    "DownloadUrl",
                ]
            )
            df.to_csv(self.progress_csv)

        df1 = pd.read_csv(self.progress_csv)
        df2 = self.download_progress

        # Identify the columns to keep
        common_columns = ["Symbol", "DocumentName", "DocumentType", "Date"]

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
                "DocumentType": merged_df["DocumentType"],
                "DownloadStatus": merged_df["DownloadStatus_df1"].fillna(
                    merged_df["DownloadStatus_df2"]
                ),
                "UploadStatus": merged_df["UploadStatus_df1"].fillna(
                    merged_df["UploadStatus_df2"]
                ),
                "DownloadUrl": merged_df["DownloadUrl_df1"].fillna(
                    merged_df["DownloadUrl_df2"]
                ),
            }
        )

        result_df.to_csv(self.progress_csv, index=None)
