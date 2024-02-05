from pathlib import Path
import shutil
import subprocess
import time
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
            time.sleep(10)


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


# def extract_text(pdf_filepath):
#     with fitz.open(pdf_filepath) as doc:
#         text = ""
#         for page in doc:
#             text += " " + page.get_text()
#     return text


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
    if text is not None:
        with open(filename, "w", encoding="utf-8") as f:
            f.write(text)


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


def translate_pdfs(csv_path, txts_dir, eng_txts_dir, filename_column):
    data = pd.read_csv(csv_path)
    models = {}

    for _, group in data.groupby("Language"):
        language = group["Language"].iloc[0]  # Language of the current group

        if language == "english":
            # Handle English files by copying them directly to eng_txts_dir
            for _, row in group.iterrows():
                src = get_txt_filename(txts_dir, row[filename_column])
                dst = get_txt_filename(eng_txts_dir, row[filename_column])
                if not dst.exists():
                    shutil.copy(src, dst)
        else:
            # Existing logic for non-English languages
            language_code = config.LANGUAGE_TO_CODE[language]
            model_name = f"Helsinki-NLP/opus-mt-{language_code}-en"
            if language_code not in models:
                stanza.download(language_code)
                models[language_code] = {
                    "nlp": stanza.Pipeline(language_code),
                    "model": MarianMTModel.from_pretrained(model_name),
                    "tokenizer": MarianTokenizer.from_pretrained(model_name),
                }

            for _, row in group.iterrows():
                src = get_txt_filename(txts_dir, row[filename_column])
                dst = get_txt_filename(eng_txts_dir, row[filename_column])
                if not dst.exists():
                    with open(src, mode="r", encoding="utf-8") as fin:
                        text = fin.read()
                    translated_text = translate(text, models[language_code])
                    with open(dst, mode="w", encoding="utf-8") as fout:
                        fout.write(translated_text)

    data.to_csv(csv_path, index=False)


def translate(text, models):
    # Break the text into sentences
    sentences = text.split("\n")

    # Translate each sentence individually
    translated_sentences = []
    
        
        if len(sentence.text) > 300:
            # Split the sentence into chunks of  300 characters or fewer
            

            # Translate each chunk individually and append to the translated_sentences list
            for chunk in chunks:
                encoded = models["tokenizer"](
                    [chunk], return_tensors="pt", truncation=True, max_length=512
                )
                translated = models["model"].generate(**encoded)
                decoded = [
                    models["tokenizer"].decode(t, skip_special_tokens=True)
                    for t in translated
                ]
                translated_sentences.append(" ".join(decoded))
        else:
            # If the sentence is not too long, translate it normally
            encoded = models["tokenizer"](
                [sentence.text], return_tensors="pt", truncation=True, max_length=512
            )
            translated = models["model"].generate(**encoded)
            decoded = [
                models["tokenizer"].decode(t, skip_special_tokens=True)
                for t in translated
            ]
            translated_sentences.append(" ".join(decoded))

    translated_text = " ".join(translated_sentences)
    return translated_text
