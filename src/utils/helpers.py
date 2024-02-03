from pathlib import Path
import time
import fitz
import pandas as pd
from transformers import MarianTokenizer, MarianMTModel
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from tqdm import tqdm
from utils.logger import setup_logger
import config
import stanza

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

    return data_dir, pdfs_dir, txts_dir


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


def get_pdf_filename(data_dir, document_name):
    return data_dir / f"{document_name}.pdf"


def get_txt_filename(data_dir, document_name):
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


def download_files(csv_path, pdfs_dir, filename_column):
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
        data.to_csv(csv_path, index=None)

        # Only wait 10 seconds if request was made (To prevent blocking from the unfccc).
        if was_requested:
            time.sleep(10)


def extract_text(pdf_filepath):
    with fitz.open(pdf_filepath) as doc:
        text = ""
        for page in doc:
            text += " " + page.get_text()
    return text


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


def save_text(text, filename):
    with open(filename, "w", encoding="utf8") as f:
        f.write(text)


def extract_pdfs(csv_path, pdfs_dir, txts_dir, filename_column):
    data = pd.read_csv(csv_path)

    # Define a function to extract text from a PDF file
    def extract_text_from_file(row):
        filename = get_pdf_filename(pdfs_dir, row[filename_column])
        if not filename.exists():
            logger.error(f"There is no pdf found to extract: {filename}")
            return None
        elif (
            "Text" in row.index
            and not pd.isna(row["Text"])
            and not config.FORCE["PDF_EXTRACT"]
        ):
            return row["Text"]
        else:
            return extract_text(filename)

    def save_text_to_file(row):
        filename = get_txt_filename(txts_dir, row[filename_column])
        save_text(row["Text"], filename)

    # Apply the function to each row in the DataFrame
    data["Text"] = data.apply(extract_text_from_file, axis=1)

    # Clean the extracted text
    data["Text"] = clean_text(data)

    data.apply(save_text_to_file, axis=1)

    # Save the updated DataFrame back to the CSV file
    data.to_csv(csv_path, index=False)


def translate_pdfs(csv_path, txts_dir):

    data = pd.read_csv(csv_path)

    # Define a dictionary to store models for each language
    models = {}

    for language in data["Language"].unique():
        if language != "english":
            # Get the language code
            language_code = config.LANGUAGE_TO_CODE[language]

            # Create the model name
            model_name = f"Helsinki-NLP/opus-mt-{language_code}-en"

            # Load the model and tokenizer only once per language
            if language_code not in models:
                stanza.download(language_code)
                models[language_code] = {
                    "nlp": stanza.Pipeline(language_code),
                    "model": MarianMTModel.from_pretrained(model_name),
                    "tokenizer": MarianTokenizer.from_pretrained(model_name),
                }

            # Apply the translation function to each row in the current group
            data.loc[data["Language"] == language, "TranslatedText"] = data.loc[
                data["Language"] == language, "Text"
            ].apply(lambda x: translate(x, models[language_code]))

    data.to_csv(csv_path, index=False)


def translate(text, models):
    # Break the text into sentences
    sentences = models["nlp"](text).sentences

    # Translate each sentence individually
    translated_sentences = []
    for sentence in sentences:
        encoded = models["tokenizer"]([sentence.text], return_tensors="pt")
        translated = models["model"].generate(**encoded)
        decoded = [
            models["tokenizer"].decode(t, skip_special_tokens=True) for t in translated
        ]
        translated_sentences.append(decoded)

    translated_text = " ".join(translated_sentences)

    return translated_text
