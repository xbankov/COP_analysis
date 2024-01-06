# src/scrapers/scraper1.py
import bs4
import pandas as pd
from scrapers.scraper import Scraper
from utils.logger import setup_logger
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
import time


logger = setup_logger()


class DecisionScraper(Scraper):
    def __init__(self, driver, progress_csv):
        super().__init__(driver, progress_csv)

    def load_all_documents_dynamically(self):
        try:
            driver = self.driver
            items_per_page_button = driver.find_element(By.ID, "edit-items-per-page--3")
            select = Select(items_per_page_button)
            last_index = len(select.options) - 1
            select.select_by_index(last_index)

            self.wait_for_loading()

            total_documents = int(
                driver.find_elements(By.CSS_SELECTOR, "span.totalresults")[-1].text
            )
            shown_documents = int(
                driver.find_elements(By.CSS_SELECTOR, "span.endresults")[-1].text
            )

            while shown_documents < total_documents:
                logger.info(f"{shown_documents}/{total_documents}")

                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(3)

                load_more_button = driver.find_element(
                    By.CSS_SELECTOR,
                    'div.block-views-blockdecisions-block-1 a.button[title="Load more items"]',
                )
                load_more_button.click()

                self.wait_for_loading()

                shown_documents = int(
                    driver.find_element(
                        By.CSS_SELECTOR,
                        "div.block-views-blockdecisions-block-1 span.endresults",
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

        # Using a list comprehension to create download_progress directly
        self.download_progress = pd.DataFrame(
            [
                {
                    "Symbol": cols[0].getText().strip().replace("/", "_"),
                    "DocumentName": cols[1].getText().strip().replace(" ", "_"),
                    "Body": cols[2].getText().strip().replace(" ", "_"),
                    "Date": cols[3].getText().strip().replace(" ", "."),
                    "DownloadUrl": self.get_eng_url_from_td(cols[4]),
                    "Status": "Not Downloaded",
                }
                for document in documents
                for cols in [document.find_all("td")]
            ]
        )

    def update_progress(self):
        if not self.progress_csv.exists():
            df = pd.DataFrame(
                columns=[
                    "Symbol",
                    "DocumentName",
                    "Body",
                    "Date",
                    "Status",
                    "DownloadUrl",
                ]
            )
            df.to_csv(self.progress_csv, index=None)
        df = pd.read_csv(self.progress_csv)

        # Merge df2 into df1 based on the 'Symbol' column
        merged_df = pd.merge(
            df,
            self.download_progress,
            on=["Symbol", "DocumentName", "Date"],
            how="outer",
            indicator=True,
        )

        # Filter only the rows from df2 that don't exist in df1
        new_rows_df2 = merged_df[merged_df["_merge"] == "right_only"].drop(
            "_merge", axis=1
        )

        # Concatenate the filtered rows to df1
        result_df = pd.concat([df, new_rows_df2], ignore_index=True)

        result_df.to_csv(self.progress_csv, index=None)
