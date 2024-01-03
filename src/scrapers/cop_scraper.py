# src/scrapers/scraper1.py
import re
import bs4
import requests
from tqdm import tqdm
from utils.helpers import Document
from utils.logger import setup_logger
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
import time


logger = setup_logger()


def get_eng_url_from_td(td):
    select_element = td.select_one(".select-wrapper select")
    english_option = select_element.find(
        "option", string=re.compile("english", re.IGNORECASE)
    )
    return english_option["value"]


def parse_loaded_page(html_content):
    soup = bs4.BeautifulSoup(html_content, "lxml")
    documents = soup.find_all("tr")[1:]
    logger.info(f"Number of TR elements {len(documents)}")
    documents_metadata = []

    for doc in documents:
        cols = doc.find_all("td")
        title = cols[1].getText().strip().replace(" ", "_")
        download_url = get_eng_url_from_td(cols[4])
        cols[0]
        documents_metadata.append(Document(title=title, download_url=download_url))

    return documents


def download_pdf(document_metadata, folder):
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.3",
    }
    download_url = document_metadata.download_url
    filename = folder / f'{document_metadata.title.replace("/", "_")}.pdf'
    response = requests.get(download_url, headers=headers)

    if response.status_code == 200:
        # Save the PDF content to a local file
        with open(filename, "wb") as pdf_file:
            pdf_file.write(response.content)
        logger.info(f"Downloaded: {download_url}")
    else:
        logger.info(
            f"Failed to download file: {document_metadata.title} with url: {download_url}. Status Code: {response.status_code}"
        )
    return response.status_code


def download_all_pdfs(documents_metadata, folder):
    status_l = []
    for doc in tqdm(documents_metadata):
        try:
            status = download_pdf(doc, folder)
        except:
            status = 404
        status_l.append(status)
        time.sleep(10)
    return status_l


def wait_for_loading(driver):
    loading_div = WebDriverWait(driver, 30).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "div.ajax-progress"))
    )
    logger.info("Loading started")
    # Wait until the div element disappears
    WebDriverWait(driver, 60).until(EC.staleness_of(loading_div))
    logger.info("Loading done")


def load_all_documents_dynamically(driver, url_to_open):
    try:
        driver.get(url_to_open)

        items_per_page_button = driver.find_element(By.ID, "edit-items-per-page--3")
        select = Select(items_per_page_button)
        last_index = len(select.options) - 1
        select.select_by_index(last_index)

        wait_for_loading(driver, logger)

        total_documents = int(
            driver.find_elements(By.CSS_SELECTOR, "span.totalresults")[-1].text
        )
        shown_documents = int(
            driver.find_elements(By.CSS_SELECTOR, "span.endresults")[-1].text
        )

        while shown_documents < total_documents:
            logger.info(f"{shown_documents}/{total_documents}")

            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(3)

            load_more_button = driver.find_element(
                By.CSS_SELECTOR,
                'div.block-views-blockdecisions-block-1 a.button[title="Load more items"]',
            )
            load_more_button.click()

            wait_for_loading(driver, logger)

            shown_documents = int(
                driver.find_element(
                    By.CSS_SELECTOR,
                    "div.block-views-blockdecisions-block-1 span.endresults",
                ).text
            )
        logger.info("All documents loaded")
        return driver.page_source
    finally:
        driver.quit()
