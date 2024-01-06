import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

from utils.logger import setup_logger
import config

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


def download_pdf(url, filename):
    headers = config.DEFAULT_HEADERS

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        # Save the PDF content to a local file
        with open(filename, "wb") as pdf_file:
            pdf_file.write(response.content)
        logger.info(f"Downloaded: {url}")
    else:
        logger.info(
            f"Failed to download file: {filename} with url: {url}. Status Code: {response.status_code}"
        )
    return response.status_code


def get_filename(symbol, document_name):
    return f"{symbol}_{document_name}.pdf"
