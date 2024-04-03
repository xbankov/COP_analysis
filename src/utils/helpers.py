import json
import random
import subprocess
import time
from pathlib import Path

import pandas as pd
import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from tqdm import tqdm

import config
from utils.logger import setup_logger

logger = setup_logger()


def init_dirs(name):
    base_data_dir = Path(config.DEFAULT_DATA_DIR)
    data_dir = base_data_dir / name
    data_dir.mkdir(parents=True, exist_ok=True)
    logger.debug(f"mkdir: {data_dir}")

    pdfs_dir = data_dir / "pdfs"
    pdfs_dir.mkdir(parents=True, exist_ok=True)
    logger.debug(f"mkdir: {pdfs_dir}")

    json_dir = data_dir / "json"
    json_dir.mkdir(parents=True, exist_ok=True)
    logger.debug(f"mkdir: {json_dir}")

    return data_dir, pdfs_dir, json_dir


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


def get_json_filename(data_dir: Path, document_name: str) -> Path:
    return data_dir / f"{document_name}.json"


def scrape_url(url, csv_path, html_path, scraper_class):
    logger.info(f"Scraper class: {scraper_class}")
    scraper = scraper_class(url, csv_path, html_path)
    scraper.load_and_download_html()
    scraper.parse()


def csv2json(csv_path, json_dir):
    csv_data = pd.read_csv(csv_path)
    for _, row in csv_data.iterrows():
        json_filename = get_json_filename(json_dir, row["id"])
        json_dict = read_json(json_filename)
        json_dict.update(row.to_dict())
        write_json(json_dict, json_filename)


def extract_metadata(html):
    metadata = {}
    soup = BeautifulSoup(html, "lxml")
    div = soup.find(class_="document-metadata")
    if len(div) == 0:
        logger.warning("empty")
    fields = div.find_all(class_="field--item")
    for field in fields:
        label = field.find_previous(class_="field__label").text.strip()
        value = field.text.strip()
        metadata[label] = value

    return metadata


def make_request_selenium(url):
    try:
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("user-agent=" + UserAgent().random)
        driver = webdriver.Chrome(options=options)
        driver.get(url)
        html = driver.page_source
        return html
    except WebDriverException as e:
        logger.error(f"Error fetching detail view for URL: {url}, {e}")
        return None
    finally:
        if driver:
            driver.quit()


def detailview(json_dir):
    for json_path in tqdm(list(json_dir.iterdir())):
        with open(json_path, "r") as json_file:
            data = json.load(json_file)

        if (
            "extra_metadata" in data
            and data["extra_metadata"]
            and not config.FORCE["EXTRA_METADATA"]
        ):
            continue

        detail_url = data.get("detail_url")
        if not detail_url:
            logger.error(f"No detail URL found in JSON: {json_path}")
            continue

        html = make_request_selenium(detail_url)
        if not html:
            logger.error(f"Failed to fetch HTML for URL: {detail_url}")
            continue

        metadata = extract_metadata(html)
        metadata["extra_metadata"] = True
        data.update(metadata)

        with open(json_path, "w") as json_file:
            json.dump(data, json_file, indent=4)

        time.sleep(config.UNIVERSAL_REQUEST_SLEEP)


def read_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def write_json(data, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f)


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


def download_pdfs(csv_path, pdfs_dir):
    data = pd.read_csv(csv_path)
    for index, row in tqdm(data.iterrows(), total=len(data)):
        was_requested = False
        url = row["pdf_url"]

        filename = get_pdf_filename(pdfs_dir, row["id"])

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


def save_tag(filename, tag, value):
    json_dict = read_json(filename)
    json_dict[tag] = value
    write_json(json_dict, filename)


def load_tag(filename, tag):
    json_dict = read_json(filename)
    return json_dict.get(tag, "")


def extract_pdfs(csv_path, json_dir, pdfs_dir):
    data = pd.read_csv(csv_path)

    def extract_text_from_pdf(row):
        src = get_pdf_filename(pdfs_dir, row["id"])
        dst = get_json_filename(json_dir, row["id"])

        if not src.exists():
            logger.error(f"There is no pdf found to extract: {src}")

        elif not dst.exists():
            text = extract_text(src)
            json_dict = read_json(dst)
            json_dict["original_text"] = text

    data.apply(extract_text_from_pdf, axis=1)
