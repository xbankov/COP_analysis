from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from utils.helpers import setup_driver
from utils.logger import setup_logger
from abc import ABC, abstractmethod
from pathlib import Path
import pandas as pd
import time

import config

logger = setup_logger()


class Scraper(ABC):
    def __init__(self, url, data_csv, current_html):
        self.current_html = Path(current_html)
        self.data_csv = Path(data_csv)
        self.url = url

        self._initialize_driver()

        self.base_url = self.driver.current_url
        self.html_content = None

    @abstractmethod
    def parse_html(self):
        pass

    @abstractmethod
    def resolve_duplicates(self):
        pass

    def parse(self):
        self.parse_html()
        self.resolve_duplicates()
        self.save_data()
        self.report()

    def save_data(self):
        self.data.to_csv(self.data_csv, index=False)

    def report(self):
        df = pd.read_csv(self.data_csv)

        logger.info(df.value_counts(subset=["Language"]))
        missing = (df["DownloadUrl"].isna()).sum()

        logger.info(f"Total entries: {len(df)}")
        logger.info(f"Total missing documents: {missing}")

    def _load_documents(self):
        total_documents = self._get_total_documents()
        shown_documents = self._get_shown_documents()

        while shown_documents < total_documents:
            logger.info(f"{shown_documents}/{total_documents} documents loaded")
            self._scroll_and_wait()
            self._click_load_more_items()
            self._wait_for_loading()
            shown_documents = self._get_shown_documents()

        logger.info("All documents loaded")
        self.html_content = self.driver.page_source
        self._write_html_to_file()

    def _initialize_driver(self):
        self.driver = setup_driver(config.DEFAULT_DRIVER_PATH, config.HEADLESS)
        self.driver.get(self.url)
        self.driver.maximize_window()

    def _initialize_page(self):
        self._select_item_per_page()
        self._wait_for_loading()

    def load_and_download_html(self):
        try:
            if self.current_html.exists() and not config.FORCE["HTML"]:
                logger.info(f"Saved HTML found: {self.current_html}")
                self._read_html_from_file()
            else:
                logger.info(
                    f"HTML not found: {self.current_html}. Loading and Downloading HTML"
                )
                self._initialize_page()
                total_documents = self._get_total_documents()
                shown_documents = self._get_shown_documents()

                while shown_documents < total_documents:
                    logger.info(f"{shown_documents}/{total_documents} documents loaded")

                    self._scroll_and_wait()
                    self._click_load_more_items()
                    self._wait_for_loading()

                    shown_documents = self._get_shown_documents()
                logger.info("HTML loaded. Saving HTML")
                self._write_html_to_file()
                self._read_html_from_file()

        except Exception as e:
            # logger.error(self.driver.page_source)
            logger.error(e)
        finally:
            self.driver.quit()

    def _select_item_per_page(self):
        logger.info("Select maximum item per page")
        items_per_page_button = self.driver.find_element(By.ID, self.button_id)
        select = Select(items_per_page_button)
        last_index = len(select.options) - 1
        select.select_by_index(last_index)

    def _scroll_and_wait(self):
        logger.info("Scroll and wait (multiple times) for button")
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        self._wait_for_scrolling()
        time.sleep(1)
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        self._wait_for_scrolling()

    def _click_load_more_items(self):
        load_more_button = self.driver.find_element(
            By.CSS_SELECTOR,
            f"{self.total_span_class} a.button[title='Load more items']",
        )
        logger.info("Click load more items")
        load_more_button.click()

    def _wait_for_scrolling(self):
        # Wait for the scrolling to complete
        try:
            # Set a timeout based on how long you expect the scrolling to take
            timeout = 5
            # Use WebDriverWait to wait until the page has scrolled to the bottom
            WebDriverWait(self.driver, timeout).until(
                lambda driver: driver.execute_script(
                    "return window.scrollY + window.innerHeight >= document.body.scrollHeight;"
                )
            )
        except TimeoutException:
            logger.warning("Timeout waiting for scrolling to complete")

    def _wait_for_loading(self):
        # Wait until the loading div element appears
        loading_div = WebDriverWait(self.driver, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.ajax-progress"))
        )
        # Wait until the loading div element disappears
        WebDriverWait(self.driver, 60).until(EC.staleness_of(loading_div))
        logger.info("'Load more items' button available.")

    def _write_html_to_file(self):
        with open(self.current_html, "w") as f:
            f.write(self.driver.page_source)

    def _read_html_from_file(self):
        with open(self.current_html, "r") as f:
            html_content = f.read()
        self.html_content = html_content

    def _get_total_documents(self):
        return int(
            self.driver.find_element(
                By.CSS_SELECTOR, f"{self.total_span_class} span.totalresults"
            ).text
        )

    def _get_shown_documents(self):
        return int(
            self.driver.find_element(
                By.CSS_SELECTOR, f"{self.total_span_class} span.endresults"
            ).text
        )
