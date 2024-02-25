from pathlib import Path
import subprocess
import time
import pandas as pd
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from tqdm import tqdm

from utils.logger import setup_logger
import config

logger = setup_logger()


def init_dirs(name):
    base_data_dir = Path(config.DEFAULT_DATA_DIR)
    data_dir = base_data_dir / name
    data_dir.mkdir(parents=True, exist_ok=True)
    logger.debug(f"mkdir: {data_dir}")

    pdfs_dir = data_dir / "pdfs"
    pdfs_dir.mkdir(parents=True, exist_ok=True)
    logger.debug(f"mkdir: {pdfs_dir}")

    txts_dir = data_dir / "txts"
    txts_dir.mkdir(parents=True, exist_ok=True)
    logger.debug(f"mkdir: {txts_dir}")

    eng_txts_dir = data_dir / "eng_txts"
    eng_txts_dir.mkdir(parents=True, exist_ok=True)
    logger.debug(f"mkdir: {eng_txts_dir}")

    return data_dir, pdfs_dir, txts_dir, eng_txts_dir


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


def get_pdf_filename(data_dir: Path, document_name: str) -> Path:
    return data_dir / f"{document_name}.pdf"


def get_txt_filename(data_dir: Path, document_name: str) -> Path:
    return data_dir / f"{document_name}.txt"


def scrape_url(url, csv_path, html_path, scraper_class):
    if not csv_path.exists() or config.FORCE["PARSE"]:
        logger.info(f"Scraper class: {scraper_class}")
        scraper = scraper_class(url, csv_path, html_path)
        scraper.load_and_download_html()
        scraper.parse()


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


def download_pdfs(csv_path, pdfs_dir, filename_column):
    data = pd.read_csv(csv_path)
    for index, row in tqdm(data.iterrows(), total=len(data)):
        was_requested = False
        url = row["DownloadUrl"]

        filename = get_pdf_filename(pdfs_dir, row[filename_column])

        if filename.exists() and not config.FORCE["DOWNLOAD"]:
            status = "Downloaded"

        else:
            if pd.isna(url):
                logger.debug(f"{filename} has no pdf file associated on row: {index}")
                status = None
            else:
                was_requested = True
                status = download_pdf(url, filename)
                if status != 200:
                    logger.error(f"Request failed with status code: {status}")
                else:
                    status = "Downloaded"

        data.at[index, "DownloadStatus"] = status

        # Only wait 10 seconds if request was made (To prevent blocking from the unfccc).
        if was_requested:
            data.to_csv(csv_path, index=None)
            time.sleep(config.UNIVERSAL_REQUEST_SLEEP)
    data.to_csv(csv_path, index=None)


def extract_text(pdf_filepath):
    try:
        # Use pdftotext to extract text from PDF
        result = subprocess.run(
            ["pdftotext", "-layout", pdf_filepath, "-"],
            stdout=subprocess.PIPE,
            check=True,
        )
        text = result.stdout.decode("utf-8")
    except subprocess.CalledProcessError as e:
        print(f"Error occurred while extracting text: {e}")
        text = ""

    return text


def save_text(text, filename):
    with open(filename, "w", encoding="utf-8") as f:
        f.write(text)


def load_text(filename):
    with open(filename, "r", encoding="utf-8") as f:
        return f.read()


def extract_pdfs(csv_path, pdfs_dir, txts_dir, filename_column):
    data = pd.read_csv(csv_path)

    # Define a function to extract text from a PDF file
    def extract_text_from_file(row):
        src = get_pdf_filename(pdfs_dir, row[filename_column])
        dst = get_txt_filename(txts_dir, row[filename_column])

        if not src.exists():
            logger.error(f"There is no pdf found to extract: {src}")

        elif not dst.exists():
            text = extract_text(src)
            save_text(text, dst)

    # Apply the function to each row in the DataFrame
    data.apply(extract_text_from_file, axis=1)
