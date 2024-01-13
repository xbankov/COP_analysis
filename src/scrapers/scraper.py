import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from utils.logger import setup_logger
from pathlib import Path
from abc import ABC, abstractmethod
import pandas as pd

logger = setup_logger()


class Scraper(ABC):
    def __init__(self, driver, progress_csv):
        self.driver = driver
        self.html_content = None
        self.progress_csv = Path(progress_csv)
        self.base_url = driver.current_url

    @abstractmethod
    def parse_loaded_page(self):
        pass

    @abstractmethod
    def update_progress(self):
        pass

    def report(self):
        df = pd.read_csv(self.progress_csv)

        NOT_ENG = (df["DownloadUrl"] == "NOT_ENG").sum()
        NOT_DOC = (df["DownloadUrl"] == "NOT_DOC").sum()

        logger.info(f"Total entries: {len(df)}")
        logger.info(f"Total NO ENGLISH documents: {NOT_ENG}")
        logger.info(f"Total NO DOCUMENT documents: {NOT_DOC}")
        logger.info(f"Total of downloadable documents: {len(df) - NOT_ENG - NOT_DOC}")

    def load_all_documents_dynamically(self):
        try:
            driver = self.driver
            driver.maximize_window()
            self.select_item_per_page()
            self.wait_for_loading()

            total_documents = int(
                driver.find_element(
                    By.CSS_SELECTOR, f"{self.total_span_class} span.totalresults"
                ).text
            )
            shown_documents = int(
                driver.find_element(
                    By.CSS_SELECTOR, f"{self.total_span_class} span.endresults"
                ).text
            )

            while shown_documents < total_documents:
                logger.info(f"{shown_documents}/{total_documents} documents loaded")

                self.scroll_and_wait()

                load_more_button = driver.find_element(
                    By.CSS_SELECTOR,
                    f"{self.total_span_class} a.button[title='Load more items']",
                )
                logger.info("Click load more items")
                load_more_button.click()

                self.wait_for_loading()

                shown_documents = int(
                    driver.find_element(
                        By.CSS_SELECTOR,
                        f"{self.total_span_class} span.endresults",
                    ).text
                )
            logger.info("All documents loaded")
            self.html_content = driver.page_source
        finally:
            driver.quit()

    def select_item_per_page(self):
        logger.info("Select maximum item per page")
        items_per_page_button = self.driver.find_element(By.ID, self.button_id)
        select = Select(items_per_page_button)
        last_index = len(select.options) - 1
        select.select_by_index(last_index)

    def scroll_and_wait(self):
        logger.info("Scroll and wait (multiple times) for button")
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        self.wait_for_scrolling()
        time.sleep(1)
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        self.wait_for_scrolling()

    def wait_for_scrolling(self):
        # Wait for the scrolling to complete
        try:
            # Set a timeout based on how long you expect the scrolling to take
            timeout = 3
            # Use WebDriverWait to wait until the page has scrolled to the bottom
            WebDriverWait(self.driver, timeout).until(
                lambda driver: driver.execute_script(
                    "return window.scrollY + window.innerHeight >= document.body.scrollHeight;"
                )
            )
        except TimeoutException:
            print("Timeout waiting for scrolling to complete")

    def wait_for_loading(self):
        # Wait until the loading div element appears
        loading_div = WebDriverWait(self.driver, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.ajax-progress"))
        )
        # Wait until the loading div element disappears
        WebDriverWait(self.driver, 60).until(EC.staleness_of(loading_div))
        logger.info("'Load more items' button available.")
