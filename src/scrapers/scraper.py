import re
import pandas as pd
from utils.logger import setup_logger
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from utils.logger import setup_logger
from pathlib import Path

logger = setup_logger()


class Scraper:
    def __init__(self, driver, progress_csv):
        self.driver = driver
        self.html_content = None
        self.progress_csv = Path(progress_csv)
        self.base_url = driver.current_url

    def wait_for_loading(self):
        # Wait until the loading div element appears
        loading_div = WebDriverWait(self.driver, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.ajax-progress"))
        )
        # Wait until the loading div element disappears
        WebDriverWait(self.driver, 60).until(EC.staleness_of(loading_div))
        logger.info("'Load more items' button available.")
