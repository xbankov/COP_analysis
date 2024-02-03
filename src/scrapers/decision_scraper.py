# src/scrapers/scraper1.py
import bs4
import pandas as pd
from scrapers.scraper import Scraper
from scrapers.parsing import get_pdf_info_from_td, parse_date, parse_text
from utils.logger import setup_logger
from urllib.parse import urljoin

logger = setup_logger()


class DecisionScraper(Scraper):
    def __init__(self, url, data_csv, current_html):
        super().__init__(url, data_csv, current_html)
        self.button_id = "edit-items-per-page--3"
        self.total_span_class = "div.block-views-blockdecisions-block-1"

    def parse_html(self):
        soup = bs4.BeautifulSoup(self.html_content, "lxml")
        documents = soup.find_all("tr")[1:]
        logger.info(f"Number of TR elements {len(documents)}")

        data_list = []

        for document in documents:
            cols = document.find_all("td")

            download_url, language = get_pdf_info_from_td(cols[4])

            data_list += [
                {
                    "Symbol": parse_text(cols[0].getText()),
                    "DocumentName": parse_text(cols[1].getText()),
                    "Body": parse_text(cols[2].getText()),
                    "Date": parse_date(cols[3].getText()),
                    "DownloadUrl": download_url,
                    "Language": language,
                    "DocumentUrl": urljoin(self.base_url, cols[4].find("a")["href"]),
                    "DownloadStatus": "Not Downloaded",
                }
            ]

        self.data = pd.DataFrame(data_list)

    def resolve_duplicates(self):
        # Define aggregation functions for each column
        agg_funcs = {
            "Date": "first",
            "Body": "first",
            "DownloadStatus": "first",
            "DownloadUrl": "first",
            "Language": "first",
            "DocumentName": lambda x: "|".join(x),
            "Symbol": lambda x: "|".join(x),
        }

        # Group by unique combination of 'DownloadUrl' and aggregate columns
        df_grouped = self.data.groupby(["DocumentUrl"]).agg(agg_funcs).reset_index()

        self.data = df_grouped
