from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

from utils.logger import setup_logger

logger = setup_logger()


def setup_driver(driver_path, headless):
    # Set up Chrome options (optional: you can add more options as needed)
    chrome_options = Options()
    if headless:
        chrome_options.add_argument(
            "--headless"
        )  # Run Chrome in headless mode (no GUI)
    chrome_service = Service(driver_path)

    # Initialize the Chrome brexecutable_pathowser
    driver = webdriver.Chrome(service=chrome_service, options=chrome_options)
    driver.implicitly_wait(20)
    return driver
