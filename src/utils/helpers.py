from pathlib import Path
import time
import fitz
import pandas as pd  # install using: pip install PyMuPDF
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from tqdm import tqdm

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
        chrome_options.add_argument("--window-size=1920x1080")

    chrome_service = Service(driver_path)

    # Initialize the Chrome brexecutable_pathowser
    driver = webdriver.Chrome(service=chrome_service, options=chrome_options)
    driver.implicitly_wait(20)

    logger.info("Chrome driver initialized with parameters:")
    logger.info(f"Driver path: {driver_path}")
    logger.info(f"Headless: {headless}")
    logger.info(f"Default window-size: 1920x1080")

    return driver


def download_pdf(url, filename):
    headers = config.DEFAULT_HEADERS
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        with open(filename, "wb") as pdf_file:
            pdf_file.write(response.content)
        logger.info(f"Downloaded: {url}")
    else:
        logger.error(
            f"Failed to download file: {filename} with url: {url}. Status Code: {response.status_code}"
        )
    return response.status_code


def get_pdf_filename(document_name):
    return f"{document_name}.pdf"


def clean_text(data):
    return (
        data["Text"]
        .str[19:]
        .str.lower()
        .str.replace("\W", " ", regex=True)
        .str.replace("\s", " ", regex=True)
        .str.replace("\s+", " ", regex=True)
        .str.strip()
    )


def extract_pdfs(data, data_path, data_folder, filename_column):
    texts = []
    for _, row in tqdm(data.iterrows(), total=len(data)):
        filename = data_folder / get_pdf_filename(row[filename_column])
        if not filename.exists() and row["DownloadStatus"] == "Downloaded":
            logger.error(
                "Inconsistency in db, Status:Downloaded but filename not existing."
            )
        if not filename.exists():
            texts.append("-")
        else:
            text = extract_text(filename)
            texts.append(text)
    data["Text"] = texts
    data["Text"] = clean_text(data)
    data.to_csv(data_path, index=False)


def download_files(data, data_path, data_folder, filename_column):
    for index, row in tqdm(data.iterrows(), total=len(data)):
        was_requested = False
        url = row["DownloadUrl"]

        filename = data_folder / get_pdf_filename(row[filename_column])

        if not filename.exists():
            if pd.isna(url):
                logger.warning(f"{filename} has no pdf file associated on row: {index}")
                status = None
            else:
                was_requested = True
                status = download_pdf(url, filename)
                if status != 200:
                    logger.error(f"Request failed with status code: {status}")
                else:
                    status = "Downloaded"

            data.at[index, "DownloadStatus"] = status
            data.to_csv(data_path, index=None)

            # Only wait 10 seconds if request was made (To prevent blocking from the unfccc).
            if was_requested:
                time.sleep(10)


def extract_text(pdf_filepath):
    with fitz.open(pdf_filepath) as doc:
        text = ""
        for page in doc:
            text += " " + page.get_text()
    return text


def create_data_folder(data_folder_path):
    folder_path = Path(data_folder_path)
    folder_path.mkdir(parents=True, exist_ok=True)
    return folder_path
