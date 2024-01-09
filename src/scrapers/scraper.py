import time
from utils.logger import setup_logger
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from utils.logger import setup_logger
from pathlib import Path

logger = setup_logger()


class Scraper:
    def __init__(self, driver, progress_csv):
        self.driver = driver
        self.html_content = None
        self.progress_csv = Path(progress_csv)
        self.base_url = driver.current_url

    def scroll_and_wait(self):
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        self.wait_for_scrolling()
        time.sleep(3)
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        self.wait_for_scrolling()

    def wait_for_scrolling(self):
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
            print("Timeout waiting for scrolling to complete")

    def wait_for_loading(self):
        # Wait until the loading div element appears
        loading_div = WebDriverWait(self.driver, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.ajax-progress"))
        )
        # Wait until the loading div element disappears
        WebDriverWait(self.driver, 60).until(EC.staleness_of(loading_div))
        logger.info("'Load more items' button available.")
