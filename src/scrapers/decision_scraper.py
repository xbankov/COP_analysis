# src/scrapers/scraper1.py
from urllib.parse import urljoin

import bs4
import pandas as pd

from scrapers.parsing import get_pdf_info_from_td, parse_date, parse_text
from scrapers.scraper import Scraper
from utils.logger import setup_logger

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

            pdf_url, language = get_pdf_info_from_td(cols[4])

            data_list += [
                {
                    "symbol": parse_text(cols[0].getText()),
                    "document_name": parse_text(cols[1].getText()),
                    "body": parse_text(cols[2].getText()),
                    "date": parse_date(cols[3].getText()),
                    "pdf_url": pdf_url,
                    "language": language,
                    "detail_url": urljoin(self.base_url, cols[4].find("a")["href"]),
                    "download_status": "Not Downloaded",
                    "id": urljoin(self.base_url, cols[4].find("a")["href"]).split("/")[
                        -1
                    ],
                }
            ]

        self.data = pd.DataFrame(data_list)

    def resolve_duplicates(self):
        agg_funcs = {
            "date": "first",
            "body": "first",
            "download_status": "first",
            "pdf_url": "first",
            "language": "first",
            "detail_url": "first",
            "document_name": lambda x: "|".join(x),
            "symbol": lambda x: "|".join(x),
        }

        df_grouped = self.data.groupby(["id"]).agg(agg_funcs).reset_index()

        self.data = df_grouped
